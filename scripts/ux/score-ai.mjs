#!/usr/bin/env node
/**
 * AI Visual Harmony Scoring Script
 * Uses OpenAI Vision API to analyze screenshots for visual harmony
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';
import OpenAI from 'openai';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const config = await import('./config.js').then(m => m.default);

const APP_NAME = process.env.APP_NAME || 'frontend-dashboard';
const OUTPUT_DIR = path.join(__dirname, '../../ux-qa-results');
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const PROMPT_VERSION = process.env.PROMPT_VERSION || 'v0.1';

if (!OPENAI_API_KEY) {
  console.log('⏭️  Skipping AI Perceptual QA: OPENAI_API_KEY not set');
  process.exit(0);
}

const openai = new OpenAI({ apiKey: OPENAI_API_KEY });

// Load prompt configuration
const promptPath = path.join(__dirname, `../../prompts/ux_vision_${PROMPT_VERSION}.json`);
let promptConfig;
try {
  promptConfig = JSON.parse(fs.readFileSync(promptPath, 'utf-8'));
  console.log(`📝 Using prompt version: ${promptConfig.version}`);
} catch (error) {
  console.error(`❌ Error loading prompt: ${promptPath}`);
  console.error(`   ${error.message}`);
  process.exit(1);
}

// Extract schema from prompt config
const HARMONY_SCHEMA = promptConfig.schema;

// Get git metadata for calibration tracking
function getGitMetadata() {
  try {
    const commitSha = process.env.GITHUB_SHA || execSync('git rev-parse HEAD', { encoding: 'utf-8' }).trim();
    
    let prNumber = null;
    if (process.env.GITHUB_EVENT_NAME === 'pull_request' && process.env.GITHUB_EVENT_PATH) {
      try {
        const eventData = JSON.parse(fs.readFileSync(process.env.GITHUB_EVENT_PATH, 'utf-8'));
        prNumber = eventData.pull_request?.number || null;
      } catch (e) {
        // Event file not readable, skip PR number
      }
    }
    
    return { commitSha, prNumber };
  } catch (error) {
    return { commitSha: 'unknown', prNumber: null };
  }
}

const gitMetadata = getGitMetadata();

function buildPrompt(pageInfo, tokens) {
  // Render prompt template with actual values
  return promptConfig.user_template
    .replace('{tokens}', JSON.stringify(tokens, null, 2))
    .replace('{page_name}', pageInfo.name)
    .replace('{page_description}', pageInfo.description)
    .replace('{schema}', JSON.stringify(HARMONY_SCHEMA, null, 2));
}

async function scoreScreenshot(pageInfo, screenshotPath, tokens, attempt = 1) {
  console.log(`  Analyzing: ${pageInfo.name}...`);

  try {
    // Read and encode image
    const imageBuffer = fs.readFileSync(screenshotPath);
    const base64Image = imageBuffer.toString('base64');
    const imageUrl = `data:image/jpeg;base64,${base64Image}`;

    // Call OpenAI Vision API
    const response = await openai.chat.completions.create({
      model: config.AI_CONFIG.model,
      temperature: config.AI_CONFIG.temperature,
      max_tokens: config.AI_CONFIG.maxTokens,
      messages: [
        {
          role: 'system',
          content: promptConfig.system_message,
        },
        {
          role: 'user',
          content: [
            {
              type: 'text',
              text: buildPrompt(pageInfo, tokens),
            },
            {
              type: 'image_url',
              image_url: {
                url: imageUrl,
                detail: config.AI_CONFIG.imageDetail,
              },
            },
          ],
        },
      ],
      response_format: { type: 'json_object' },
    });

    const content = response.choices[0].message.content;
    const harmony = JSON.parse(content);

    console.log(`    Overall: ${harmony.overall}/100`);
    console.log(`    Color: ${harmony.color}, Spacing: ${harmony.spacing}, Typography: ${harmony.typography}`);
    console.log(`    Alignment: ${harmony.alignment}, Contrast: ${harmony.contrast}`);

    return {
      success: true,
      harmony,
      usage: response.usage,
    };
  } catch (error) {
    console.error(`    ❌ Error: ${error.message}`);

    // Retry once on parse error (max 2 attempts total)
    if (error.message.includes('JSON') && attempt < 2) {
      console.log(`    🔄 Retrying (attempt ${attempt + 1}/2)...`);
      await new Promise(resolve => setTimeout(resolve, 1000));
      return scoreScreenshot(pageInfo, screenshotPath, tokens, attempt + 1);
    }

    return {
      success: false,
      error: error.message,
    };
  }
}

async function scoreAllPages() {
  console.log(`🤖 AI Visual Harmony Scoring for ${APP_NAME}...\n`);

  // Load screenshot manifest
  const manifestPath = path.join(OUTPUT_DIR, `${APP_NAME}-screenshots.json`);
  if (!fs.existsSync(manifestPath)) {
    console.error(`❌ Error: Screenshot manifest not found: ${manifestPath}`);
    console.error('Run capture.mjs first');
    process.exit(1);
  }

  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
  const pageResults = [];
  let totalUsage = { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 };

  for (const page of manifest.pages) {
    if (page.error) {
      console.log(`  ⏭️  Skipping ${page.name}: ${page.error}`);
      pageResults.push({
        name: page.name,
        path: page.path,
        error: page.error,
      });
      continue;
    }

    const result = await scoreScreenshot(page, page.screenshotPath, config.relevantTokens);

    if (result.success) {
      pageResults.push({
        name: page.name,
        path: page.path,
        url: page.url,
        harmony: result.harmony,
      });

      totalUsage.prompt_tokens += result.usage.prompt_tokens;
      totalUsage.completion_tokens += result.usage.completion_tokens;
      totalUsage.total_tokens += result.usage.total_tokens;
    } else {
      pageResults.push({
        name: page.name,
        path: page.path,
        error: result.error,
      });
    }

    // Rate limiting: wait 1s between requests
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  // Calculate app-level harmony score
  const validPages = pageResults.filter(p => p.harmony);
  const harmonyOverall = validPages.length > 0
    ? Math.round(validPages.reduce((sum, p) => sum + p.harmony.overall, 0) / validPages.length)
    : 0;

  const report = {
    app: APP_NAME,
    timestamp: new Date().toISOString(),
    model: config.AI_CONFIG.model,
    prompt_version: promptConfig.version,
    commit_sha: gitMetadata.commitSha,
    pr_number: gitMetadata.prNumber,
    pages: pageResults,
    harmony_overall: harmonyOverall,
    thresholds: config.THRESHOLDS.harmony,
    usage: totalUsage,
  };

  // Save report
  const reportPath = path.join(OUTPUT_DIR, `${APP_NAME}-harmony.json`);
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  console.log(`\n📊 Harmony Report saved: ${reportPath}`);
  console.log(`\n🎨 Overall Harmony Score: ${harmonyOverall}/100`);
  console.log(`   Threshold: ${config.THRESHOLDS.harmony.min}/100`);
  console.log(`   Status: ${harmonyOverall >= config.THRESHOLDS.harmony.min ? '✅ PASS' : '⚠️  BELOW THRESHOLD'}`);
  console.log(`\n💰 API Usage: ${totalUsage.total_tokens} tokens`);

  return report;
}

// Main execution
(async () => {
  await scoreAllPages();
})();

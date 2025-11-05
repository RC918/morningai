#!/usr/bin/env node
/**
 * AI Visual Harmony Scoring Script
 * Uses OpenAI Vision API to analyze screenshots for visual harmony
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import OpenAI from 'openai';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const config = await import('./config.js').then(m => m.default);

const APP_NAME = process.env.APP_NAME || 'frontend-dashboard';
const OUTPUT_DIR = path.join(__dirname, '../../ux-qa-results');
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;

if (!OPENAI_API_KEY) {
  console.log('⏭️  Skipping AI Perceptual QA: OPENAI_API_KEY not set');
  process.exit(0);
}

const openai = new OpenAI({ apiKey: OPENAI_API_KEY });

// JSON schema for AI response
const HARMONY_SCHEMA = {
  type: 'object',
  properties: {
    overall: { type: 'number', minimum: 0, maximum: 100 },
    color: { type: 'number', minimum: 0, maximum: 100 },
    spacing: { type: 'number', minimum: 0, maximum: 100 },
    typography: { type: 'number', minimum: 0, maximum: 100 },
    alignment: { type: 'number', minimum: 0, maximum: 100 },
    contrast: { type: 'number', minimum: 0, maximum: 100 },
    findings: {
      type: 'array',
      items: { type: 'string' },
      maxItems: 5,
    },
  },
  required: ['overall', 'color', 'spacing', 'typography', 'alignment', 'contrast', 'findings'],
};

function buildPrompt(pageInfo, tokens) {
  return `You are a UI design QA assistant. Analyze this screenshot for visual harmony based on the design system tokens provided.

**Design System Tokens:**
${JSON.stringify(tokens, null, 2)}

**Page Context:**
- Name: ${pageInfo.name}
- Description: ${pageInfo.description}

**Evaluation Rubric (0-100 scale):**

1. **Color Harmony (0-100):**
   - Are colors from the token palette?
   - Is contrast sufficient (WCAG AA minimum)?
   - Is brand color usage consistent?
   - Penalize: non-token colors, poor contrast, inconsistent brand usage

2. **Spacing Consistency (0-100):**
   - Do margins/padding follow the spacing scale?
   - Is vertical rhythm consistent?
   - Are elements properly spaced?
   - Penalize: arbitrary spacing, inconsistent rhythm, cramped/loose layouts

3. **Typography Consistency (0-100):**
   - Do font sizes match the typography scale?
   - Are font weights appropriate?
   - Is line-height comfortable?
   - Penalize: off-scale sizes, inconsistent weights, poor readability

4. **Alignment & Grid (0-100):**
   - Are elements properly aligned?
   - Is the grid system consistent?
   - Are cards/components aligned?
   - Penalize: misaligned elements, ragged grids, inconsistent columns

5. **Contrast Quality (0-100):**
   - Is text readable against backgrounds?
   - Are interactive elements distinguishable?
   - Is visual hierarchy clear?
   - Penalize: low contrast, unclear hierarchy, hard-to-read text

**Output Requirements:**
- Provide scores for each dimension (0-100)
- Calculate overall score as weighted average: (color*0.25 + spacing*0.20 + typography*0.20 + alignment*0.20 + contrast*0.15)
- List 3-5 actionable findings (specific issues or improvements)
- Be objective and consistent
- Output ONLY valid JSON matching the schema

**JSON Schema:**
${JSON.stringify(HARMONY_SCHEMA, null, 2)}`;
}

async function scoreScreenshot(pageInfo, screenshotPath, tokens) {
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
          content: 'You are a UI design QA assistant. Output strict JSON only.',
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

    // Retry once on parse error
    if (error.message.includes('JSON')) {
      console.log(`    🔄 Retrying...`);
      await new Promise(resolve => setTimeout(resolve, 1000));
      return scoreScreenshot(pageInfo, screenshotPath, tokens);
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

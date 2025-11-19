#!/usr/bin/env node
/**
 * UX Quality Assurance Runner
 * Orchestrates the complete UX QA pipeline: capture, score, aggregate
 */

import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const APP_NAME = process.env.APP_NAME || 'frontend-dashboard';
const SKIP_AI = process.env.SKIP_AI === 'true';

function runScript(scriptPath, env = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn('node', [scriptPath], {
      stdio: 'inherit',
      env: { ...process.env, ...env },
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Script ${scriptPath} exited with code ${code}`));
      }
    });

    child.on('error', reject);
  });
}

async function runUXQA() {
  console.log(`🚀 Starting UX Quality Assurance for ${APP_NAME}...\n`);

  try {
    // Step 1: Capture screenshots
    console.log('📸 Step 1/3: Capturing screenshots...\n');
    await runScript(path.join(__dirname, 'capture.mjs'), { APP_NAME });

    // Step 2: AI scoring (optional)
    if (!SKIP_AI && process.env.OPENAI_API_KEY) {
      console.log('\n🤖 Step 2/3: AI Visual Harmony Scoring...\n');
      await runScript(path.join(__dirname, 'score-ai.mjs'), { APP_NAME });
    } else {
      console.log('\n⏭️  Step 2/3: Skipping AI scoring (OPENAI_API_KEY not set or SKIP_AI=true)\n');
    }

    // Step 3: Aggregate metrics
    console.log('\n📊 Step 3/3: Aggregating metrics...\n');
    await runScript(path.join(__dirname, 'aggregate.mjs'), { APP_NAME });

    console.log('\n✅ UX Quality Assurance completed successfully!\n');
  } catch (error) {
    console.error(`\n❌ UX QA failed: ${error.message}\n`);
    process.exit(1);
  }
}

// Main execution
runUXQA();

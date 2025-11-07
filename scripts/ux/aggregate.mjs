#!/usr/bin/env node
/**
 * UX Metrics Aggregator
 * Combines Motion Performance and Visual Harmony scores into Delight Index
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const config = await import('./config.js').then(m => m.default);

const APP_NAME = process.env.APP_NAME || 'frontend-dashboard';
const OUTPUT_DIR = path.join(__dirname, '../../ux-qa-results');
const MOTION_RESULTS_DIR = path.join(__dirname, `../../handoff/20250928/40_App/${APP_NAME}/motion-test-results`);

/**
 * Normalize motion metrics to 0-100 score
 */
function normalizeMotionScore(motionReport) {
  if (!motionReport || !motionReport.results) {
    return { overall: 0, details: null, error: 'No motion data' };
  }

  const validResults = motionReport.results.filter(r => r.action && !r.error);
  
  if (validResults.length === 0) {
    return { overall: 0, details: null, error: 'No valid motion results' };
  }

  // Calculate normalized scores for each test
  const testScores = validResults.map(result => {
    const action = result.action;
    
    // FPS Score: normalize to 0-100 (60 FPS = 100)
    const fpsScore = Math.min(100, Math.round((action.fps / 60) * 100));
    
    // P95 Frame Time Score: normalize to 0-100 (16.67ms or less = 100)
    const p95Score = Math.min(100, Math.round((16.67 / Math.max(action.p95FrameTime, 0.01)) * 100));
    
    // Dropped Frames Score: normalize to 0-100 (0% dropped = 100)
    const droppedScore = Math.min(100, Math.round((1 - (action.droppedRate / 100)) * 100));
    
    // Weighted average: FPS (40%), P95 (40%), Dropped (20%)
    const testScore = Math.round(
      fpsScore * 0.4 +
      p95Score * 0.4 +
      droppedScore * 0.2
    );
    
    return {
      name: result.name,
      score: testScore,
      fps: action.fps,
      p95FrameTime: action.p95FrameTime,
      droppedRate: action.droppedRate,
      fpsScore,
      p95Score,
      droppedScore,
    };
  });

  // Overall motion score: average of all test scores
  const overallScore = Math.round(
    testScores.reduce((sum, t) => sum + t.score, 0) / testScores.length
  );

  return {
    overall: overallScore,
    details: testScores,
    timestamp: motionReport.timestamp,
  };
}

/**
 * Calculate Delight Index from Harmony and Motion scores
 */
function calculateDelightIndex(harmonyScore, motionScore) {
  const weights = config.DELIGHT_WEIGHTS;
  
  const delightIndex = Math.round(
    harmonyScore * weights.harmony +
    motionScore * weights.motion
  );
  
  return {
    index: delightIndex,
    harmony: harmonyScore,
    motion: motionScore,
    weights,
  };
}

async function aggregateMetrics() {
  console.log(`📊 Aggregating UX metrics for ${APP_NAME}...\n`);

  // Load harmony report
  const harmonyPath = path.join(OUTPUT_DIR, `${APP_NAME}-harmony.json`);
  let harmonyReport = null;
  let harmonyScore = 0;

  if (fs.existsSync(harmonyPath)) {
    harmonyReport = JSON.parse(fs.readFileSync(harmonyPath, 'utf-8'));
    harmonyScore = harmonyReport.harmony_overall || 0;
    console.log(`✅ Harmony Score: ${harmonyScore}/100`);
  } else {
    console.log(`⚠️  No harmony report found (AI scoring skipped)`);
  }

  // Load motion report
  const motionPath = path.join(MOTION_RESULTS_DIR, 'motion-test-report.json');
  let motionReport = null;
  let motionScore = 0;

  if (fs.existsSync(motionPath)) {
    motionReport = JSON.parse(fs.readFileSync(motionPath, 'utf-8'));
    const normalized = normalizeMotionScore(motionReport);
    motionScore = normalized.overall;
    console.log(`✅ Motion Score: ${motionScore}/100`);
    
    if (normalized.details) {
      console.log(`   Tests:`);
      normalized.details.forEach(test => {
        console.log(`     - ${test.name}: ${test.score}/100 (FPS: ${test.fps}, P95: ${test.p95FrameTime}ms)`);
      });
    }
  } else {
    console.log(`⚠️  No motion report found`);
  }

  // Calculate Delight Index
  const delight = calculateDelightIndex(harmonyScore, motionScore);
  console.log(`\n🎯 Delight Index: ${delight.index}/100`);
  console.log(`   Weights: Harmony ${delight.weights.harmony * 100}%, Motion ${delight.weights.motion * 100}%`);
  console.log(`   Threshold: ${config.THRESHOLDS.delight.min}/100`);
  console.log(`   Status: ${delight.index >= config.THRESHOLDS.delight.min ? '✅ PASS' : '⚠️  BELOW THRESHOLD'}`);

  // Create comprehensive report
  const report = {
    app: APP_NAME,
    timestamp: new Date().toISOString(),
    prompt_version: harmonyReport?.prompt_version || 'unknown',
    commit_sha: harmonyReport?.commit_sha || 'unknown',
    pr_number: harmonyReport?.pr_number || null,
    harmony: {
      overall: harmonyScore,
      pages: harmonyReport?.pages || [],
      threshold: config.THRESHOLDS.harmony,
      model: harmonyReport?.model,
      usage: harmonyReport?.usage,
    },
    motion: {
      overall: motionScore,
      tests: normalizeMotionScore(motionReport).details || [],
      timestamp: motionReport?.timestamp,
    },
    delight: {
      index: delight.index,
      harmony_score: delight.harmony,
      motion_score: delight.motion,
      weights: delight.weights,
      threshold: config.THRESHOLDS.delight,
    },
    passed: {
      harmony: harmonyScore >= config.THRESHOLDS.harmony.min,
      motion: motionScore >= 60, // Basic threshold
      delight: delight.index >= config.THRESHOLDS.delight.min,
    },
  };

  // Save aggregated report
  const reportPath = path.join(OUTPUT_DIR, `${APP_NAME}-ux-report.json`);
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`\n📄 UX Report saved: ${reportPath}`);

  // Generate HTML report
  generateHTMLReport(report);

  return report;
}

function generateHTMLReport(report) {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UX Quality Report - ${report.app}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; background: #f5f5f7; }
    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    h1 { color: #1d1d1f; margin-bottom: 8px; }
    .subtitle { color: #6e6e73; margin-bottom: 32px; }
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 32px 0; }
    .metric-card { background: #f5f5f7; padding: 24px; border-radius: 8px; }
    .metric-card h3 { margin: 0 0 8px 0; color: #1d1d1f; font-size: 14px; font-weight: 600; text-transform: uppercase; }
    .metric-value { font-size: 48px; font-weight: 700; margin: 8px 0; }
    .metric-value.pass { color: #34c759; }
    .metric-value.warn { color: #ff9500; }
    .metric-value.fail { color: #ff3b30; }
    .metric-label { color: #6e6e73; font-size: 14px; }
    .section { margin: 40px 0; }
    .section h2 { color: #1d1d1f; margin-bottom: 16px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: 12px; border-bottom: 1px solid #d2d2d7; }
    th { background: #f5f5f7; font-weight: 600; }
    .findings { background: #f5f5f7; padding: 16px; border-radius: 8px; margin: 8px 0; }
    .findings li { margin: 8px 0; }
  </style>
</head>
<body>
  <div class="container">
    <h1>UX Quality Report</h1>
    <div class="subtitle">${report.app} • ${new Date(report.timestamp).toLocaleString()}</div>
    
    <div class="metric-grid">
      <div class="metric-card">
        <h3>Delight Index</h3>
        <div class="metric-value ${report.passed.delight ? 'pass' : 'warn'}">${report.delight.index}</div>
        <div class="metric-label">Target: ${report.delight.threshold.target} • Min: ${report.delight.threshold.min}</div>
      </div>
      
      <div class="metric-card">
        <h3>Visual Harmony</h3>
        <div class="metric-value ${report.passed.harmony ? 'pass' : 'warn'}">${report.harmony.overall}</div>
        <div class="metric-label">AI-powered design analysis</div>
      </div>
      
      <div class="metric-card">
        <h3>Motion Performance</h3>
        <div class="metric-value ${report.passed.motion ? 'pass' : 'warn'}">${report.motion.overall}</div>
        <div class="metric-label">Animation smoothness</div>
      </div>
    </div>
    
    ${report.harmony.pages && report.harmony.pages.length > 0 ? `
    <div class="section">
      <h2>Visual Harmony by Page</h2>
      <table>
        <thead>
          <tr>
            <th>Page</th>
            <th>Overall</th>
            <th>Color</th>
            <th>Spacing</th>
            <th>Typography</th>
            <th>Alignment</th>
            <th>Contrast</th>
          </tr>
        </thead>
        <tbody>
          ${report.harmony.pages.filter(p => p.harmony).map(page => `
            <tr>
              <td><strong>${page.name}</strong></td>
              <td>${page.harmony.overall}</td>
              <td>${page.harmony.color}</td>
              <td>${page.harmony.spacing}</td>
              <td>${page.harmony.typography}</td>
              <td>${page.harmony.alignment}</td>
              <td>${page.harmony.contrast}</td>
            </tr>
            ${page.harmony.findings && page.harmony.findings.length > 0 ? `
            <tr>
              <td colspan="7">
                <div class="findings">
                  <strong>Findings:</strong>
                  <ul>
                    ${page.harmony.findings.map(f => `<li>${f}</li>`).join('')}
                  </ul>
                </div>
              </td>
            </tr>
            ` : ''}
          `).join('')}
        </tbody>
      </table>
    </div>
    ` : ''}
    
    ${report.motion.tests && report.motion.tests.length > 0 ? `
    <div class="section">
      <h2>Motion Performance Tests</h2>
      <table>
        <thead>
          <tr>
            <th>Test</th>
            <th>Score</th>
            <th>FPS</th>
            <th>P95 Frame Time</th>
            <th>Dropped Rate</th>
          </tr>
        </thead>
        <tbody>
          ${report.motion.tests.map(test => `
            <tr>
              <td><strong>${test.name}</strong></td>
              <td>${test.score}/100</td>
              <td>${test.fps}</td>
              <td>${test.p95FrameTime}ms</td>
              <td>${test.droppedRate}%</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    ` : ''}
    
    ${report.harmony.usage ? `
    <div class="section">
      <h2>AI Analysis Details</h2>
      <p><strong>Model:</strong> ${report.harmony.model}</p>
      <p><strong>Tokens Used:</strong> ${report.harmony.usage.total_tokens} (Prompt: ${report.harmony.usage.prompt_tokens}, Completion: ${report.harmony.usage.completion_tokens})</p>
    </div>
    ` : ''}
  </div>
</body>
</html>`;

  const htmlPath = path.join(OUTPUT_DIR, `${APP_NAME}-ux-report.html`);
  fs.writeFileSync(htmlPath, html);
  console.log(`📄 HTML Report saved: ${htmlPath}`);
}

// Main execution
(async () => {
  await aggregateMetrics();
})();

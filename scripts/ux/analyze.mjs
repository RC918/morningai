#!/usr/bin/env node
/**
 * Calibration Data Analyzer
 * Aggregates AI Perceptual QA results into calibration.csv for threshold tuning
 * 
 * Reads from ux-qa-results/*-ux-report.json (preferred) or *-harmony.json (fallback)
 * Outputs calibration.csv with per-page rows for statistical analysis
 * 
 * CSV Columns:
 * - row_id: Unique identifier (commit_sha:app:page_route:prompt_version:model)
 * - prompt_version: Version of the AI prompt used (e.g., v0.1, v0.2)
 * - model: AI model used (e.g., gpt-4o-mini)
 * - app: Application name (e.g., frontend-dashboard)
 * - page_route: Page path (e.g., /, /login, /dashboard)
 * - page_name: Human-readable page name
 * - harmony_score: Visual harmony score (0-100)
 * - delight_score: Delight index (0-100, app-level)
 * - pr_number: GitHub PR number (if available)
 * - commit_sha: Git commit SHA
 * - labels: Semicolon-separated PR labels (if available)
 * - decision: pass/fail based on harmony threshold
 * - timestamp: ISO timestamp of the analysis
 * - source_file: Path to source report file
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const INPUT_DIR = process.env.INPUT_DIR || path.join(__dirname, '../../ux-qa-results');
const OUTPUT_FILE = process.env.OUTPUT_FILE || path.join(__dirname, '../../calibration.csv');

/**
 * Get PR labels from GitHub API
 */
async function getPRLabels(prNumber) {
  if (!prNumber || !process.env.GITHUB_TOKEN) {
    return [];
  }

  try {
    const repo = process.env.GITHUB_REPOSITORY;
    if (!repo) return [];

    const [owner, repoName] = repo.split('/');
    const url = `https://api.github.com/repos/${owner}/${repoName}/issues/${prNumber}/labels`;
    
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${process.env.GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
      },
    });

    if (!response.ok) {
      console.warn(`⚠️  Failed to fetch labels for PR #${prNumber}: ${response.status}`);
      return [];
    }

    const labels = await response.json();
    return labels.map(l => l.name);
  } catch (error) {
    console.warn(`⚠️  Error fetching PR labels: ${error.message}`);
    return [];
  }
}

/**
 * Load UX report (preferred) or harmony report (fallback)
 */
function loadReport(inputDir) {
  const reports = [];

  // Find all ux-report.json files (preferred)
  const uxReportFiles = fs.readdirSync(inputDir)
    .filter(f => f.endsWith('-ux-report.json'))
    .map(f => path.join(inputDir, f));

  for (const reportPath of uxReportFiles) {
    try {
      const report = JSON.parse(fs.readFileSync(reportPath, 'utf-8'));
      reports.push({ report, source: reportPath, type: 'ux-report' });
    } catch (error) {
      console.warn(`⚠️  Failed to load ${reportPath}: ${error.message}`);
    }
  }

  // Fallback: Find harmony.json files if no ux-report found
  if (reports.length === 0) {
    const harmonyFiles = fs.readdirSync(inputDir)
      .filter(f => f.endsWith('-harmony.json'))
      .map(f => path.join(inputDir, f));

    for (const reportPath of harmonyFiles) {
      try {
        const report = JSON.parse(fs.readFileSync(reportPath, 'utf-8'));
        reports.push({ report, source: reportPath, type: 'harmony' });
      } catch (error) {
        console.warn(`⚠️  Failed to load ${reportPath}: ${error.message}`);
      }
    }
  }

  return reports;
}

/**
 * Extract calibration rows from a report
 */
async function extractRows(reportData) {
  const { report, source, type } = reportData;
  const rows = [];

  // Extract metadata
  const app = report.app || 'unknown';
  const timestamp = report.timestamp || new Date().toISOString();
  const promptVersion = report.prompt_version || 'unknown';
  const commitSha = report.commit_sha || 'unknown';
  const prNumber = report.pr_number || null;
  const model = type === 'ux-report' ? report.harmony?.model : report.model;

  // Get PR labels if available
  const labels = prNumber ? await getPRLabels(prNumber) : [];
  const labelsStr = labels.join(';');

  // Extract harmony threshold for decision logic
  const harmonyThreshold = type === 'ux-report' 
    ? report.harmony?.threshold?.min || 70
    : report.thresholds?.min || 70;

  // Get delight score (app-level)
  const delightScore = type === 'ux-report' ? report.delight?.index || null : null;

  // Extract pages
  const pages = type === 'ux-report' ? report.harmony?.pages || [] : report.pages || [];

  for (const page of pages) {
    // Skip pages without harmony data
    if (!page.harmony) {
      continue;
    }

    const pageRoute = page.path || 'unknown';
    const pageName = page.name || pageRoute;
    const harmonyScore = page.harmony.overall;

    // Decision: pass if harmony >= threshold
    const decision = harmonyScore >= harmonyThreshold ? 'pass' : 'fail';

    // Generate stable row ID
    const rowId = `${commitSha}:${app}:${pageRoute}:${promptVersion}:${model}`;

    rows.push({
      row_id: rowId,
      prompt_version: promptVersion,
      model: model || 'unknown',
      app,
      page_route: pageRoute,
      page_name: pageName,
      harmony_score: harmonyScore,
      delight_score: delightScore || '',
      pr_number: prNumber || '',
      commit_sha: commitSha,
      labels: labelsStr,
      decision,
      timestamp,
      source_file: source,
    });
  }

  return rows;
}

/**
 * Convert rows to CSV format
 */
function rowsToCSV(rows) {
  if (rows.length === 0) {
    return '';
  }

  // CSV header
  const headers = Object.keys(rows[0]);
  const csvLines = [headers.join(',')];

  // CSV rows
  for (const row of rows) {
    const values = headers.map(h => {
      const value = row[h];
      // Escape values containing commas or quotes
      if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
        return `"${value.replace(/"/g, '""')}"`;
      }
      return value;
    });
    csvLines.push(values.join(','));
  }

  return csvLines.join('\n');
}

/**
 * Main execution
 */
async function analyze() {
  console.log('📊 Analyzing UX QA results for calibration...\n');

  // Check if input directory exists
  if (!fs.existsSync(INPUT_DIR)) {
    console.error(`❌ Error: Input directory not found: ${INPUT_DIR}`);
    console.error('Run UX QA pipeline first to generate reports');
    process.exit(1);
  }

  // Load reports
  console.log(`📂 Reading reports from: ${INPUT_DIR}`);
  const reports = loadReport(INPUT_DIR);

  if (reports.length === 0) {
    console.error(`❌ Error: No UX reports found in ${INPUT_DIR}`);
    console.error('Expected files: *-ux-report.json or *-harmony.json');
    process.exit(1);
  }

  console.log(`✅ Found ${reports.length} report(s)`);

  // Extract calibration rows
  const allRows = [];
  for (const reportData of reports) {
    const rows = await extractRows(reportData);
    allRows.push(...rows);
    console.log(`   ${reportData.report.app}: ${rows.length} page(s)`);
  }

  if (allRows.length === 0) {
    console.warn('⚠️  No calibration data extracted (no pages with harmony scores)');
    process.exit(0);
  }

  // Convert to CSV
  const csv = rowsToCSV(allRows);

  // Save CSV
  fs.writeFileSync(OUTPUT_FILE, csv);
  console.log(`\n📄 Calibration data saved: ${OUTPUT_FILE}`);
  console.log(`   Total rows: ${allRows.length}`);
  console.log(`   Columns: ${Object.keys(allRows[0]).length}`);

  // Summary statistics
  const passCount = allRows.filter(r => r.decision === 'pass').length;
  const failCount = allRows.filter(r => r.decision === 'fail').length;
  const avgHarmony = Math.round(
    allRows.reduce((sum, r) => sum + r.harmony_score, 0) / allRows.length
  );

  console.log(`\n📈 Summary:`);
  console.log(`   Pass: ${passCount} (${Math.round(passCount / allRows.length * 100)}%)`);
  console.log(`   Fail: ${failCount} (${Math.round(failCount / allRows.length * 100)}%)`);
  console.log(`   Avg Harmony: ${avgHarmony}/100`);

  if (allRows[0].pr_number) {
    console.log(`   PR: #${allRows[0].pr_number}`);
  }
  if (allRows[0].labels) {
    console.log(`   Labels: ${allRows[0].labels || '(none)'}`);
  }
}

// Main execution
(async () => {
  try {
    await analyze();
  } catch (error) {
    console.error(`❌ Fatal error: ${error.message}`);
    console.error(error.stack);
    process.exit(1);
  }
})();

#!/usr/bin/env node

/**
 * Update LHCI baseline and trend data after main branch runs
 * 
 * This script:
 * 1. Reads the latest LHCI report from .lhci directory
 * 2. Updates .lhci-baseline.json with current metrics
 * 3. Appends to trend.csv for long-term tracking
 */

const fs = require('fs');
const path = require('path');

const LHCI_DIR = path.join(__dirname, '../frontend-dashboard-deploy/.lighthouseci');
const BASELINE_FILE = path.join(__dirname, '../.lhci-baseline.json');
const TREND_FILE = path.join(__dirname, '../trend.csv');

const METRICS = [
  'largest-contentful-paint',
  'total-blocking-time',
  'interactive',
  'cumulative-layout-shift',
  'first-contentful-paint'
];

function readLatestLHCIReport() {
  try {
    const files = fs.readdirSync(LHCI_DIR)
      .filter(f => f.startsWith('lhr-') && f.endsWith('.json'))
      .sort()
      .reverse();
    
    if (files.length === 0) {
      console.error('No LHCI reports found');
      return null;
    }

    const reportPath = path.join(LHCI_DIR, files[0]);
    return JSON.parse(fs.readFileSync(reportPath, 'utf8'));
  } catch (error) {
    console.error('Error reading LHCI report:', error.message);
    return null;
  }
}

function extractMetrics(report) {
  const audits = report.audits;
  const metrics = {};

  for (const key of METRICS) {
    if (audits[key] && audits[key].numericValue !== undefined) {
      metrics[key] = audits[key].numericValue;
    }
  }

  return metrics;
}

function updateBaseline(metrics) {
  try {
    fs.writeFileSync(BASELINE_FILE, JSON.stringify(metrics, null, 2), 'utf8');
    console.log(`✅ Baseline updated: ${BASELINE_FILE}`);
  } catch (error) {
    console.error('Error updating baseline:', error.message);
    throw error;
  }
}

function updateTrend(metrics) {
  try {
    const timestamp = new Date().toISOString();
    
    const fileExists = fs.existsSync(TREND_FILE);
    
    if (!fileExists) {
      const header = 'timestamp,lcp_ms,tbt_ms,tti_ms,cls,fcp_ms\n';
      fs.writeFileSync(TREND_FILE, header, 'utf8');
    }
    
    const row = [
      timestamp,
      metrics['largest-contentful-paint']?.toFixed(0) || '',
      metrics['total-blocking-time']?.toFixed(0) || '',
      metrics['interactive']?.toFixed(0) || '',
      metrics['cumulative-layout-shift']?.toFixed(4) || '',
      metrics['first-contentful-paint']?.toFixed(0) || ''
    ].join(',') + '\n';
    
    fs.appendFileSync(TREND_FILE, row, 'utf8');
    console.log(`✅ Trend updated: ${TREND_FILE}`);
    console.log(`   Row: ${row.trim()}`);
  } catch (error) {
    console.error('Error updating trend:', error.message);
    throw error;
  }
}

function calculateMedian(reports) {
  if (!Array.isArray(reports) || reports.length === 0) {
    return null;
  }

  const allMetrics = reports.map(report => extractMetrics(report));
  const medianMetrics = {};

  for (const key of METRICS) {
    const values = allMetrics
      .map(m => m[key])
      .filter(v => v !== undefined)
      .sort((a, b) => a - b);
    
    if (values.length > 0) {
      const mid = Math.floor(values.length / 2);
      medianMetrics[key] = values.length % 2 === 0
        ? (values[mid - 1] + values[mid]) / 2
        : values[mid];
    }
  }

  return medianMetrics;
}

function readAllReports() {
  try {
    const files = fs.readdirSync(LHCI_DIR)
      .filter(f => f.startsWith('lhr-') && f.endsWith('.json'))
      .sort();
    
    return files.map(file => {
      const reportPath = path.join(LHCI_DIR, file);
      return JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    });
  } catch (error) {
    console.error('Error reading all reports:', error.message);
    return [];
  }
}

function main() {
  console.log('Updating LHCI baseline and trend...');
  
  const reports = readAllReports();
  console.log(`Found ${reports.length} report(s)`);
  
  let metrics;
  
  if (reports.length > 1) {
    console.log('Calculating median from multiple runs...');
    metrics = calculateMedian(reports);
  } else if (reports.length === 1) {
    console.log('Using single report...');
    metrics = extractMetrics(reports[0]);
  } else {
    console.error('No reports found');
    process.exit(1);
  }
  
  console.log('Metrics:', metrics);
  
  updateBaseline(metrics);
  
  updateTrend(metrics);
  
  console.log('\n✅ Baseline and trend updated successfully!');
}

main();

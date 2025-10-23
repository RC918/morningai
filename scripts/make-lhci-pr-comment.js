#!/usr/bin/env node

/**
 * Generate Lighthouse CI PR comment with performance delta comparison
 * 
 * This script:
 * 1. Reads the latest LHCI report from .lhci directory
 * 2. Compares against baseline (if exists)
 * 3. Generates a markdown comment with delta indicators
 * 4. Highlights metrics that regressed >5%
 */

const fs = require('fs');
const path = require('path');

const LHCI_DIR = path.join(__dirname, '../frontend-dashboard-deploy/.lighthouseci');
const BASELINE_FILE = path.join(__dirname, '../.lhci-baseline.json');
const OUTPUT_FILE = path.join(__dirname, '../frontend-dashboard-deploy/.lhci-diff.md');

const METRICS = {
  'largest-contentful-paint': { label: 'Largest Contentful Paint (LCP)', unit: 's', divisor: 1000 },
  'total-blocking-time': { label: 'Total Blocking Time (TBT)', unit: 'ms', divisor: 1 },
  'interactive': { label: 'Time to Interactive (TTI)', unit: 's', divisor: 1000 },
  'cumulative-layout-shift': { label: 'Cumulative Layout Shift (CLS)', unit: '', divisor: 1 },
  'first-contentful-paint': { label: 'First Contentful Paint (FCP)', unit: 's', divisor: 1000 }
};

const TOLERANCE_PERCENT = 5; // 5% tolerance for warnings

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

function readBaseline() {
  try {
    if (!fs.existsSync(BASELINE_FILE)) {
      return null;
    }
    return JSON.parse(fs.readFileSync(BASELINE_FILE, 'utf8'));
  } catch (error) {
    console.error('Error reading baseline:', error.message);
    return null;
  }
}

function extractMetrics(report) {
  const audits = report.audits;
  const metrics = {};

  for (const [key, config] of Object.entries(METRICS)) {
    if (audits[key] && audits[key].numericValue !== undefined) {
      metrics[key] = audits[key].numericValue;
    }
  }

  return metrics;
}

function formatValue(value, config) {
  const formatted = (value / config.divisor).toFixed(2);
  return config.unit ? `${formatted}${config.unit}` : formatted;
}

function calculateDelta(current, baseline, config) {
  const delta = current - baseline;
  const percentChange = (delta / baseline) * 100;
  
  const formattedDelta = (delta / config.divisor).toFixed(2);
  const sign = delta > 0 ? '+' : '';
  const deltaStr = `${sign}${formattedDelta}${config.unit}`;
  
  let emoji = '🟢'; // Good (improved or within tolerance)
  if (Math.abs(percentChange) > TOLERANCE_PERCENT) {
    emoji = delta > 0 ? '🔻' : '🟢'; // Worse or Better
  }
  
  return {
    delta: formattedDelta,
    deltaStr,
    percentChange: percentChange.toFixed(1),
    emoji,
    isRegression: delta > 0 && Math.abs(percentChange) > TOLERANCE_PERCENT
  };
}

function generateComment(currentMetrics, baseline) {
  let comment = '### 📈 Lighthouse CI 效能報告\n\n';
  
  if (!baseline) {
    comment += '> ℹ️ 這是第一次執行，尚無基線數據可比較。\n\n';
    comment += '#### 當前效能指標\n\n';
    
    for (const [key, config] of Object.entries(METRICS)) {
      if (currentMetrics[key] !== undefined) {
        const value = formatValue(currentMetrics[key], config);
        comment += `- **${config.label}**: ${value}\n`;
      }
    }
    
    comment += '\n---\n';
    comment += '*下次 PR 將會顯示與此基線的對比。*\n';
    return comment;
  }

  comment += '#### 效能對比 (本次 vs 基線)\n\n';
  
  const regressions = [];
  
  for (const [key, config] of Object.entries(METRICS)) {
    if (currentMetrics[key] !== undefined && baseline[key] !== undefined) {
      const currentValue = formatValue(currentMetrics[key], config);
      const delta = calculateDelta(currentMetrics[key], baseline[key], config);
      
      comment += `- ${delta.emoji} **${config.label}**: ${currentValue} (Δ ${delta.deltaStr}, ${delta.percentChange}%)\n`;
      
      if (delta.isRegression) {
        regressions.push({
          metric: config.label,
          percentChange: delta.percentChange
        });
      }
    }
  }
  
  if (regressions.length > 0) {
    comment += '\n#### ⚠️ 效能警告\n\n';
    comment += `以下指標退步超過 ${TOLERANCE_PERCENT}%，請檢查是否需要優化：\n\n`;
    
    for (const reg of regressions) {
      comment += `- **${reg.metric}** 增加了 ${reg.percentChange}%\n`;
    }
    
    comment += '\n**建議行動**：\n';
    comment += '1. 檢查是否新增了大型資源（圖片、字型、第三方腳本）\n';
    comment += '2. 使用 Chrome DevTools Performance 面板分析瓶頸\n';
    comment += '3. 考慮使用 code splitting 或 lazy loading\n';
    comment += '4. 如果是預期的變更，請在 PR 描述中說明原因\n';
  } else {
    comment += '\n✅ **所有效能指標都在可接受範圍內！**\n';
  }
  
  comment += '\n---\n';
  comment += `*容差範圍: ±${TOLERANCE_PERCENT}% | 測試環境: Desktop (模擬)*\n`;
  
  return comment;
}

function main() {
  console.log('Generating LHCI PR comment...');
  
  const report = readLatestLHCIReport();
  if (!report) {
    console.error('Failed to read LHCI report');
    process.exit(1);
  }
  
  const currentMetrics = extractMetrics(report);
  console.log('Current metrics:', currentMetrics);
  
  const baseline = readBaseline();
  if (baseline) {
    console.log('Baseline metrics:', baseline);
  } else {
    console.log('No baseline found, this is the first run');
  }
  
  const comment = generateComment(currentMetrics, baseline);
  
  fs.writeFileSync(OUTPUT_FILE, comment, 'utf8');
  console.log(`PR comment written to ${OUTPUT_FILE}`);
  
  console.log('\n--- Preview ---');
  console.log(comment);
}

main();

#!/usr/bin/env node
/**
 * Motion Performance Testing Script
 * Tests animation performance, frame rates, and motion smoothness
 * Part of UX Ops Pipeline - Priority 2
 */

const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const RESULTS_DIR = path.join(__dirname, '../motion-test-results');
const BASE_URL = process.env.BASE_URL || 'http://localhost:4173';
const TARGET_FPS = 60;
// Configurable thresholds for CI vs local environments
// CI headless environments have lower performance headroom
const MAX_FRAME_TIME = parseFloat(process.env.MOTION_P95_MS || '16.67'); // ms (1000ms / 60fps)
const ACCEPTABLE_DROPPED_FRAMES_RATE = parseFloat(process.env.MOTION_DROP_PERCENT || '1') / 100; // percentage

const MOTION_TESTS = [
  {
    name: 'Page Transition',
    url: BASE_URL,
    action: async (page) => {
      // Robust navigation: try clicking link, fallback to direct navigation
      const dashboardLink = page.locator('a[href="/dashboard"]');
      if (await dashboardLink.count() > 0) {
        await dashboardLink.click();
      } else {
        await page.goto(`${BASE_URL}/dashboard`, { waitUntil: 'networkidle' });
      }
      await page.waitForTimeout(1000);
    }
  },
  {
    name: 'Modal Animation',
    url: `${BASE_URL}/dashboard`,
    action: async (page) => {
      const modalButton = page.locator('button:has-text("Open")').first();
      if (await modalButton.count() > 0) {
        await modalButton.click();
        await page.waitForTimeout(500);
      }
    }
  },
  {
    name: 'Scroll Performance',
    url: `${BASE_URL}/dashboard`,
    action: async (page) => {
      await page.evaluate(() => {
        window.scrollTo({ top: 1000, behavior: 'smooth' });
      });
      await page.waitForTimeout(1000);
    }
  }
];

async function measureFrameRate(page, duration = 2000, dropThresholdMs = 16.67, minFrames = 60) {
  const metrics = await page.evaluate(({ durationMs, dropThresholdMs, minFrames }) => {
    return new Promise((resolve) => {
      const frames = [];
      let startTime = null;
      let endTime = 0;
      let lastTime = 0;
      let droppedFrames = 0;
      let finished = false;
      
      function finish(reason) {
        if (finished) return;
        finished = true;
        
        if (frames.length === 0) {
          resolve({
            valid: false,
            reason: reason || 'no frames captured',
            fps: 0,
            avgFrameTime: 0,
            frameCount: 0,
            droppedFrames: 0,
            droppedRate: 0,
            p95FrameTime: 0,
            maxFrameTime: 0
          });
          return;
        }
        
        if (frames.length < minFrames) {
          resolve({
            valid: false,
            reason: `insufficient frames: ${frames.length} < ${minFrames}`,
            fps: 0,
            avgFrameTime: 0,
            frameCount: frames.length,
            droppedFrames,
            droppedRate: 0,
            p95FrameTime: 0,
            maxFrameTime: 0
          });
          return;
        }
        
        const avgFrameTime = frames.reduce((a, b) => a + b, 0) / frames.length;
        const fps = 1000 / avgFrameTime;
        const sortedFrames = [...frames].sort((a, b) => a - b);
        const p95Index = Math.floor(sortedFrames.length * 0.95);
        const droppedRate = (droppedFrames / frames.length) * 100;
        
        resolve({
          valid: true,
          fps: Math.round(fps * 10) / 10,
          avgFrameTime: Math.round(avgFrameTime * 100) / 100,
          frameCount: frames.length,
          droppedFrames,
          droppedRate: Math.round(droppedRate * 100) / 100,
          p95FrameTime: Math.round(sortedFrames[p95Index] * 100) / 100,
          maxFrameTime: Math.round(Math.max(...frames) * 100) / 100
        });
      }
      
      function measureFrame(currentTime) {
        if (finished) return;
        
        // Initialize timing on first frame using rAF timestamp
        if (startTime === null) {
          startTime = currentTime;
          endTime = startTime + durationMs;
          lastTime = currentTime;
          requestAnimationFrame(measureFrame);
          return;
        }
        
        const frameDuration = currentTime - lastTime;
        
        // Guard against negative durations (shouldn't happen with single time base)
        if (frameDuration >= 0) {
          frames.push(frameDuration);
          if (frameDuration > dropThresholdMs) {
            droppedFrames++;
          }
        }
        
        lastTime = currentTime;
        
        if (currentTime >= endTime) {
          finish('duration complete');
        } else {
          requestAnimationFrame(measureFrame);
        }
      }
      
      setTimeout(() => finish('timeout'), durationMs + 1000);
      
      requestAnimationFrame(measureFrame);
    });
  }, { durationMs: duration, dropThresholdMs, minFrames });
  
  return metrics;
}

async function runMotionTests() {
  console.log('🎬 Starting Motion Performance Tests...\n');
  console.log(`Thresholds: P95 ≤ ${MAX_FRAME_TIME}ms, Dropped ≤ ${ACCEPTABLE_DROPPED_FRAMES_RATE * 100}%\n`);
  
  if (!fs.existsSync(RESULTS_DIR)) {
    fs.mkdirSync(RESULTS_DIR, { recursive: true });
  }
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();
  
  page.setDefaultTimeout(10000);
  page.setDefaultNavigationTimeout(10000);
  
  const results = [];
  let allTestsPassed = true;
  
  for (const test of MOTION_TESTS) {
    console.log(`Testing: ${test.name}`);
    
    try {
      await page.goto(test.url, { waitUntil: 'networkidle' });
      
      // Warm-up period to stabilize rendering
      await page.waitForTimeout(300);
      
      const baselineMetrics = await measureFrameRate(page, 1000, MAX_FRAME_TIME, 60);
      
      if (!baselineMetrics.valid) {
        throw new Error(`Baseline measurement invalid: ${baselineMetrics.reason}`);
      }
      
      await test.action(page);
      
      // Short wait after action before measuring
      await page.waitForTimeout(200);
      
      const actionMetrics = await measureFrameRate(page, 2000, MAX_FRAME_TIME, 60);
      
      if (!actionMetrics.valid) {
        throw new Error(`Action measurement invalid: ${actionMetrics.reason}`);
      }
      
      const passed = 
        actionMetrics.p95FrameTime <= MAX_FRAME_TIME &&
        actionMetrics.droppedRate <= ACCEPTABLE_DROPPED_FRAMES_RATE * 100;
      
      if (!passed) {
        allTestsPassed = false;
      }
      
      const result = {
        name: test.name,
        baseline: baselineMetrics,
        action: actionMetrics,
        passed,
        thresholds: {
          targetFPS: TARGET_FPS,
          maxFrameTime: MAX_FRAME_TIME,
          maxDroppedRate: ACCEPTABLE_DROPPED_FRAMES_RATE * 100
        }
      };
      
      results.push(result);
      
      console.log(`  Baseline FPS: ${baselineMetrics.fps}`);
      console.log(`  Action FPS: ${actionMetrics.fps}`);
      console.log(`  P95 Frame Time: ${actionMetrics.p95FrameTime}ms (threshold: ${MAX_FRAME_TIME}ms)`);
      console.log(`  Dropped Frames: ${actionMetrics.droppedRate}% (threshold: ${ACCEPTABLE_DROPPED_FRAMES_RATE * 100}%)`);
      console.log(`  Status: ${passed ? '✅ PASS' : '❌ FAIL'}\n`);
      
    } catch (error) {
      console.error(`  ❌ Error: ${error.message}\n`);
      results.push({
        name: test.name,
        error: error.message,
        passed: false
      });
      allTestsPassed = false;
    }
  }
  
  await browser.close();
  
  const reportPath = path.join(RESULTS_DIR, 'motion-test-report.json');
  fs.writeFileSync(reportPath, JSON.stringify({
    timestamp: new Date().toISOString(),
    passed: allTestsPassed,
    results
  }, null, 2));
  
  console.log(`\n📊 Results saved to: ${reportPath}`);
  console.log(`\n${allTestsPassed ? '✅ All motion tests PASSED' : '❌ Some motion tests FAILED'}`);
  
  process.exit(allTestsPassed ? 0 : 1);
}

async function checkServer() {
  try {
    const response = await fetch(BASE_URL);
    return response.ok;
  } catch {
    return false;
  }
}

(async () => {
  const serverRunning = await checkServer();
  
  if (!serverRunning) {
    console.error(`❌ Error: Development server not running on ${BASE_URL}`);
    console.error('Please start the server with: pnpm run preview');
    process.exit(1);
  }
  
  await runMotionTests();
})();

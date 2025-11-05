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
const TARGET_FPS = 60;
const MAX_FRAME_TIME = 16.67; // ms (1000ms / 60fps)
const ACCEPTABLE_DROPPED_FRAMES_RATE = 0.01; // 1%

const MOTION_TESTS = [
  {
    name: 'Page Transition',
    url: 'http://localhost:4173',
    action: async (page) => {
      await page.click('a[href="/dashboard"]');
      await page.waitForTimeout(1000);
    }
  },
  {
    name: 'Modal Animation',
    url: 'http://localhost:4173/dashboard',
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
    url: 'http://localhost:4173/dashboard',
    action: async (page) => {
      await page.evaluate(() => {
        window.scrollTo({ top: 1000, behavior: 'smooth' });
      });
      await page.waitForTimeout(1000);
    }
  }
];

async function measureFrameRate(page, duration = 2000) {
  const metrics = await page.evaluate((duration) => {
    return new Promise((resolve) => {
      const frames = [];
      const startTime = performance.now();
      const endTime = startTime + duration;
      const maxFrames = 1200;
      let lastTime = startTime;
      let frameCount = 0;
      let droppedFrames = 0;
      let finished = false;
      
      function finish() {
        if (finished) return;
        finished = true;
        
        if (frames.length === 0) {
          resolve({
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
        
        const avgFrameTime = frames.reduce((a, b) => a + b, 0) / frames.length;
        const fps = 1000 / avgFrameTime;
        const droppedRate = droppedFrames / frameCount;
        
        resolve({
          fps: Math.round(fps * 10) / 10,
          avgFrameTime: Math.round(avgFrameTime * 100) / 100,
          frameCount,
          droppedFrames,
          droppedRate: Math.round(droppedRate * 10000) / 100,
          p95FrameTime: Math.round(frames.sort((a, b) => a - b)[Math.floor(frames.length * 0.95)] * 100) / 100,
          maxFrameTime: Math.round(Math.max(...frames) * 100) / 100
        });
      }
      
      function measureFrame(currentTime) {
        if (finished) return;
        
        const frameDuration = currentTime - lastTime;
        frames.push(frameDuration);
        frameCount++;
        
        if (frameDuration > 16.67) {
          droppedFrames++;
        }
        
        lastTime = currentTime;
        
        if (currentTime >= endTime || frameCount >= maxFrames) {
          finish();
        } else {
          requestAnimationFrame(measureFrame);
        }
      }
      
      setTimeout(finish, duration + 500);
      
      requestAnimationFrame(measureFrame);
    });
  }, duration);
  
  return metrics;
}

async function runMotionTests() {
  console.log('🎬 Starting Motion Performance Tests...\n');
  
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
      
      const baselineMetrics = await measureFrameRate(page, 1000);
      
      await test.action(page);
      const actionMetrics = await measureFrameRate(page, 2000);
      
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

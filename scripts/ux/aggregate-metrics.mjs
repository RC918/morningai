#!/usr/bin/env node

/**
 * UX Metrics Aggregator
 * 
 * Fetches UX metrics from recent PRs and consolidates them into a single JSON file.
 * 
 * Metrics collected:
 * - i18n coverage (%)
 * - A11y violations (critical/serious counts)
 * - Motion P95 frame time (ms)
 * - VRT mismatch rate (%)
 * - Lighthouse FCP/LCP (ms)
 * 
 * Usage:
 *   node scripts/ux/aggregate-metrics.mjs [--limit=30]
 * 
 * Environment variables:
 *   GITHUB_TOKEN - GitHub API token (required)
 */

import { Octokit } from '@octokit/rest';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const REPO_OWNER = 'RC918';
const REPO_NAME = 'morningai';
const DEFAULT_LIMIT = 30;

const THRESHOLDS = {
  i18n: { target: 95, unit: '%' },
  a11y: { critical: 0, serious: 2 },
  motion: { p95: 16.67, unit: 'ms' },
  vrt: { mismatch: 0.1, unit: '%' },
  lighthouse: { fcp: 1000, lcp: 2500, unit: 'ms' }
};

class MetricsAggregator {
  constructor(token) {
    this.octokit = new Octokit({ auth: token });
    this.metrics = [];
  }

  async fetchRecentPRs(limit = DEFAULT_LIMIT) {
    console.log(`Fetching last ${limit} merged PRs...`);
    
    const { data: pulls } = await this.octokit.pulls.list({
      owner: REPO_OWNER,
      repo: REPO_NAME,
      state: 'closed',
      sort: 'updated',
      direction: 'desc',
      per_page: limit * 2 // Fetch more to account for unmerged PRs
    });

    // Filter only merged PRs
    const mergedPRs = pulls
      .filter(pr => pr.merged_at)
      .slice(0, limit);

    console.log(`Found ${mergedPRs.length} merged PRs`);
    return mergedPRs;
  }

  async fetchPRMetrics(pr) {
    console.log(`Processing PR #${pr.number}: ${pr.title}`);

    const metrics = {
      pr: pr.number,
      title: pr.title,
      merged_at: pr.merged_at,
      author: pr.user.login,
      url: pr.html_url,
      sha: pr.merge_commit_sha,
      apps: {},
      bundleSize: null
    };

    // Fetch check runs for this PR
    try {
      const { data: checkRuns } = await this.octokit.checks.listForRef({
        owner: REPO_OWNER,
        repo: REPO_NAME,
        ref: pr.merge_commit_sha,
        per_page: 100
      });

      // Extract metrics from check runs
      for (const app of ['frontend-dashboard', 'owner-console']) {
        metrics.apps[app] = await this.extractAppMetrics(checkRuns.check_runs, app, pr);
      }

      // Extract Lighthouse metrics from PR comments
      metrics.lighthouse = await this.extractLighthouseMetrics(pr);

      // Extract bundle size from PR comments
      metrics.bundleSize = await this.extractBundleSizeMetrics(pr);

    } catch (error) {
      console.error(`Error fetching metrics for PR #${pr.number}:`, error.message);
    }

    return metrics;
  }

  async extractAppMetrics(checkRuns, appName, pr) {
    const metrics = {
      i18n: null,
      a11y: null,
      motion: null,
      vrt: null
    };

    // Try to find and parse artifacts for each metric type
    const metricTypes = ['i18n', 'a11y', 'motion', 'vrt'];
    
    for (const metricType of metricTypes) {
      try {
        // Find the check run for this metric
        const checkRun = checkRuns.find(run => 
          run.name.toLowerCase().includes(metricType) && 
          run.name.includes(appName)
        );
        
        if (checkRun) {
          // Try to download and parse the artifact
          const parsedMetric = await this.downloadAndParseArtifact(checkRun, metricType, appName, pr);
          
          if (parsedMetric) {
            metrics[metricType] = parsedMetric;
          } else if (checkRun.conclusion === 'success') {
            // Fallback: mark as available if we can't parse but check passed
            metrics[metricType] = {
              status: 'available',
              check_run_id: checkRun.id
            };
          }
        }
      } catch (error) {
        console.error(`Error extracting ${metricType} for ${appName}:`, error.message);
      }
    }

    return metrics;
  }

  async downloadAndParseArtifact(checkRun, metricType, appName, pr) {
    try {
      // List artifacts for this workflow run
      const { data: artifacts } = await this.octokit.actions.listWorkflowRunArtifacts({
        owner: REPO_OWNER,
        repo: REPO_NAME,
        run_id: checkRun.check_suite.id
      });

      // Find the artifact for this metric and app
      const artifactName = `${metricType}-test-results-${appName}`;
      const artifact = artifacts.artifacts.find(a => 
        a.name.includes(metricType) && a.name.includes(appName)
      );

      if (!artifact) {
        return null;
      }

      // Download the artifact
      const { data: download } = await this.octokit.actions.downloadArtifact({
        owner: REPO_OWNER,
        repo: REPO_NAME,
        artifact_id: artifact.id,
        archive_format: 'zip'
      });

      // Parse the artifact based on metric type
      // Note: In production, we would extract the ZIP and parse JSON files
      // For now, we'll use a simplified approach based on check run output
      return await this.parseMetricFromCheckRun(checkRun, metricType);

    } catch (error) {
      // Artifact download might fail due to permissions or expiration
      // Fall back to parsing from check run output
      return await this.parseMetricFromCheckRun(checkRun, metricType);
    }
  }

  async parseMetricFromCheckRun(checkRun, metricType) {
    try {
      // Get check run details including output
      const { data: checkRunDetails } = await this.octokit.checks.get({
        owner: REPO_OWNER,
        repo: REPO_NAME,
        check_run_id: checkRun.id
      });

      const output = checkRunDetails.output?.text || checkRunDetails.output?.summary || '';
      
      if (metricType === 'i18n') {
        // Parse i18n coverage percentage
        // Look for patterns like "Coverage: 100%" or "coverage: 95.5%"
        const coverageMatch = output.match(/coverage[:\s]+(\d+(?:\.\d+)?)\s*%/i);
        if (coverageMatch) {
          const coverage = parseFloat(coverageMatch[1]);
          return {
            status: 'parsed',
            value: coverage,
            unit: '%',
            passed: coverage >= THRESHOLDS.i18n.target,
            check_run_id: checkRun.id
          };
        }
      } else if (metricType === 'a11y') {
        // Parse a11y violations
        // Look for patterns like "Critical: 0, Serious: 1"
        const criticalMatch = output.match(/critical[:\s]+(\d+)/i);
        const seriousMatch = output.match(/serious[:\s]+(\d+)/i);
        
        if (criticalMatch || seriousMatch) {
          const critical = criticalMatch ? parseInt(criticalMatch[1]) : 0;
          const serious = seriousMatch ? parseInt(seriousMatch[1]) : 0;
          
          return {
            status: 'parsed',
            critical,
            serious,
            passed: critical <= THRESHOLDS.a11y.critical && serious <= THRESHOLDS.a11y.serious,
            check_run_id: checkRun.id
          };
        }
      } else if (metricType === 'motion') {
        // Parse motion P95 frame time
        // Look for patterns like "P95: 16.7ms" or "p95FrameTime: 16.67"
        const p95Match = output.match(/p95[:\s]+(\d+(?:\.\d+)?)\s*(?:ms)?/i);
        if (p95Match) {
          const p95 = parseFloat(p95Match[1]);
          return {
            status: 'parsed',
            value: p95,
            unit: 'ms',
            passed: p95 <= THRESHOLDS.motion.p95,
            check_run_id: checkRun.id
          };
        }
      } else if (metricType === 'vrt') {
        // Parse VRT mismatch percentage
        const mismatchMatch = output.match(/mismatch[:\s]+(\d+(?:\.\d+)?)\s*%/i);
        if (mismatchMatch) {
          const mismatch = parseFloat(mismatchMatch[1]);
          return {
            status: 'parsed',
            value: mismatch,
            unit: '%',
            passed: mismatch <= THRESHOLDS.vrt.mismatch,
            check_run_id: checkRun.id
          };
        }
      }

      return null;
    } catch (error) {
      console.error(`Error parsing ${metricType} from check run:`, error.message);
      return null;
    }
  }

  async extractLighthouseMetrics(pr) {
    try {
      // Fetch PR comments to find Lighthouse results
      const { data: comments } = await this.octokit.issues.listComments({
        owner: REPO_OWNER,
        repo: REPO_NAME,
        issue_number: pr.number,
        per_page: 100
      });

      // Look for Lighthouse CI comment
      const lighthouseComment = comments.find(comment => 
        comment.body && comment.body.includes('Lighthouse CI') && comment.body.includes('FCP')
      );

      if (lighthouseComment) {
        // Parse FCP and LCP from comment body
        const fcpMatch = lighthouseComment.body.match(/First Contentful Paint.*?(\d+\.?\d*)\s*s/i);
        const lcpMatch = lighthouseComment.body.match(/Largest Contentful Paint.*?(\d+\.?\d*)\s*s/i);

        return {
          fcp: fcpMatch ? parseFloat(fcpMatch[1]) * 1000 : null, // Convert to ms
          lcp: lcpMatch ? parseFloat(lcpMatch[1]) * 1000 : null,
          comment_url: lighthouseComment.html_url
        };
      }
    } catch (error) {
      console.error(`Error extracting Lighthouse metrics for PR #${pr.number}:`, error.message);
    }

    return null;
  }

  async extractBundleSizeMetrics(pr) {
    try {
      // Fetch PR comments to find bundle size reports
      const { data: comments } = await this.octokit.issues.listComments({
        owner: REPO_OWNER,
        repo: REPO_NAME,
        issue_number: pr.number,
        per_page: 100
      });

      // Look for bundle size comment (from bundlewatch, size-limit, or similar tools)
      const bundleSizeComment = comments.find(comment => 
        comment.body && (
          comment.body.includes('Bundle Size') ||
          comment.body.includes('bundle size') ||
          comment.body.includes('Size Change') ||
          comment.body.includes('size-limit')
        )
      );

      if (bundleSizeComment) {
        const body = bundleSizeComment.body;
        
        // Try to parse bundle size in KB or MB
        // Patterns: "123.45 KB", "1.23 MB", "Total: 456 KB"
        const kbMatch = body.match(/(?:total|size)[:\s]+(\d+(?:\.\d+)?)\s*KB/i);
        const mbMatch = body.match(/(?:total|size)[:\s]+(\d+(?:\.\d+)?)\s*MB/i);
        
        let totalSize = null;
        if (kbMatch) {
          totalSize = parseFloat(kbMatch[1]); // in KB
        } else if (mbMatch) {
          totalSize = parseFloat(mbMatch[1]) * 1024; // Convert MB to KB
        }

        // Try to parse change/delta
        const changeMatch = body.match(/([+-]?\d+(?:\.\d+)?)\s*KB/);
        const changePercent = body.match(/([+-]?\d+(?:\.\d+)?)\s*%/);

        return {
          total_kb: totalSize,
          change_kb: changeMatch ? parseFloat(changeMatch[1]) : null,
          change_percent: changePercent ? parseFloat(changePercent[1]) : null,
          comment_url: bundleSizeComment.html_url
        };
      }

      // Fallback: Try to extract from check runs
      const { data: checkRuns } = await this.octokit.checks.listForRef({
        owner: REPO_OWNER,
        repo: REPO_NAME,
        ref: pr.merge_commit_sha,
        per_page: 100
      });

      const bundleCheckRun = checkRuns.check_runs.find(run => 
        run.name.toLowerCase().includes('bundle') || 
        run.name.toLowerCase().includes('size')
      );

      if (bundleCheckRun) {
        const output = bundleCheckRun.output?.text || bundleCheckRun.output?.summary || '';
        const kbMatch = output.match(/(\d+(?:\.\d+)?)\s*KB/i);
        
        if (kbMatch) {
          return {
            total_kb: parseFloat(kbMatch[1]),
            change_kb: null,
            change_percent: null,
            check_run_id: bundleCheckRun.id
          };
        }
      }

    } catch (error) {
      console.error(`Error extracting bundle size for PR #${pr.number}:`, error.message);
    }

    return null;
  }

  evaluateMetric(value, threshold, comparison = 'lte') {
    if (value === null || value === undefined) return 'unknown';
    
    if (comparison === 'lte') {
      return value <= threshold ? 'pass' : 'fail';
    } else if (comparison === 'gte') {
      return value >= threshold ? 'pass' : 'fail';
    }
    
    return 'unknown';
  }

  async aggregateMetrics(limit = DEFAULT_LIMIT) {
    const prs = await this.fetchRecentPRs(limit);
    
    for (const pr of prs) {
      const metrics = await this.fetchPRMetrics(pr);
      this.metrics.push(metrics);
    }

    return this.generateReport();
  }

  generateReport() {
    const report = {
      generated_at: new Date().toISOString(),
      repo: `${REPO_OWNER}/${REPO_NAME}`,
      total_prs: this.metrics.length,
      thresholds: THRESHOLDS,
      metrics: this.metrics,
      summary: this.generateSummary()
    };

    return report;
  }

  generateSummary() {
    const summary = {
      apps: {},
      trends: {}
    };

    // Calculate summary statistics for each app
    for (const app of ['frontend-dashboard', 'owner-console']) {
      const appMetrics = this.metrics
        .map(m => m.apps[app])
        .filter(Boolean);

      // Count available and parsed metrics
      const i18nParsed = appMetrics.filter(m => m.i18n?.status === 'parsed');
      const a11yParsed = appMetrics.filter(m => m.a11y?.status === 'parsed');
      const motionParsed = appMetrics.filter(m => m.motion?.status === 'parsed');
      const vrtParsed = appMetrics.filter(m => m.vrt?.status === 'parsed');

      summary.apps[app] = {
        total_prs: appMetrics.length,
        i18n: {
          available: appMetrics.filter(m => m.i18n).length,
          parsed: i18nParsed.length,
          avg_coverage: i18nParsed.length > 0 
            ? i18nParsed.reduce((sum, m) => sum + m.i18n.value, 0) / i18nParsed.length 
            : null,
          pass_rate: i18nParsed.length > 0
            ? (i18nParsed.filter(m => m.i18n.passed).length / i18nParsed.length) * 100
            : null
        },
        a11y: {
          available: appMetrics.filter(m => m.a11y).length,
          parsed: a11yParsed.length,
          avg_critical: a11yParsed.length > 0
            ? a11yParsed.reduce((sum, m) => sum + m.a11y.critical, 0) / a11yParsed.length
            : null,
          avg_serious: a11yParsed.length > 0
            ? a11yParsed.reduce((sum, m) => sum + m.a11y.serious, 0) / a11yParsed.length
            : null,
          pass_rate: a11yParsed.length > 0
            ? (a11yParsed.filter(m => m.a11y.passed).length / a11yParsed.length) * 100
            : null
        },
        motion: {
          available: appMetrics.filter(m => m.motion).length,
          parsed: motionParsed.length,
          avg_p95: motionParsed.length > 0
            ? motionParsed.reduce((sum, m) => sum + m.motion.value, 0) / motionParsed.length
            : null,
          pass_rate: motionParsed.length > 0
            ? (motionParsed.filter(m => m.motion.passed).length / motionParsed.length) * 100
            : null
        },
        vrt: {
          available: appMetrics.filter(m => m.vrt).length,
          parsed: vrtParsed.length,
          avg_mismatch: vrtParsed.length > 0
            ? vrtParsed.reduce((sum, m) => sum + m.vrt.value, 0) / vrtParsed.length
            : null,
          pass_rate: vrtParsed.length > 0
            ? (vrtParsed.filter(m => m.vrt.passed).length / vrtParsed.length) * 100
            : null
        }
      };

      // Generate trend data (last 10 PRs)
      const recentMetrics = this.metrics.slice(0, 10).reverse();
      summary.trends[app] = {
        i18n: recentMetrics.map(m => ({
          pr: m.pr,
          value: m.apps[app]?.i18n?.value || null,
          passed: m.apps[app]?.i18n?.passed || null
        })),
        a11y: recentMetrics.map(m => ({
          pr: m.pr,
          critical: m.apps[app]?.a11y?.critical || null,
          serious: m.apps[app]?.a11y?.serious || null,
          passed: m.apps[app]?.a11y?.passed || null
        })),
        motion: recentMetrics.map(m => ({
          pr: m.pr,
          value: m.apps[app]?.motion?.value || null,
          passed: m.apps[app]?.motion?.passed || null
        })),
        vrt: recentMetrics.map(m => ({
          pr: m.pr,
          value: m.apps[app]?.vrt?.value || null,
          passed: m.apps[app]?.vrt?.passed || null
        }))
      };
    }

    // Calculate Lighthouse summary
    const lighthouseMetrics = this.metrics
      .map(m => m.lighthouse)
      .filter(Boolean);

    if (lighthouseMetrics.length > 0) {
      const fcpValues = lighthouseMetrics.map(m => m.fcp).filter(Boolean);
      const lcpValues = lighthouseMetrics.map(m => m.lcp).filter(Boolean);

      summary.lighthouse = {
        total_prs: lighthouseMetrics.length,
        fcp_avg: fcpValues.length > 0 ? fcpValues.reduce((a, b) => a + b, 0) / fcpValues.length : null,
        lcp_avg: lcpValues.length > 0 ? lcpValues.reduce((a, b) => a + b, 0) / lcpValues.length : null,
        fcp_pass_rate: fcpValues.length > 0
          ? (fcpValues.filter(v => v <= THRESHOLDS.lighthouse.fcp).length / fcpValues.length) * 100
          : null,
        lcp_pass_rate: lcpValues.length > 0
          ? (lcpValues.filter(v => v <= THRESHOLDS.lighthouse.lcp).length / lcpValues.length) * 100
          : null
      };

      // Lighthouse trend data
      const recentLighthouse = this.metrics.slice(0, 10).reverse();
      summary.trends.lighthouse = recentLighthouse.map(m => ({
        pr: m.pr,
        fcp: m.lighthouse?.fcp || null,
        lcp: m.lighthouse?.lcp || null
      }));
    }

    // Calculate bundle size summary
    const bundleSizeMetrics = this.metrics
      .map(m => m.bundleSize)
      .filter(Boolean);

    if (bundleSizeMetrics.length > 0) {
      const totalSizes = bundleSizeMetrics.map(m => m.total_kb).filter(Boolean);
      const changes = bundleSizeMetrics.map(m => m.change_kb).filter(Boolean);

      summary.bundleSize = {
        total_prs: bundleSizeMetrics.length,
        avg_size_kb: totalSizes.length > 0
          ? totalSizes.reduce((a, b) => a + b, 0) / totalSizes.length
          : null,
        avg_change_kb: changes.length > 0
          ? changes.reduce((a, b) => a + b, 0) / changes.length
          : null,
        total_change_kb: changes.length > 0
          ? changes.reduce((a, b) => a + b, 0)
          : null
      };

      // Bundle size trend data
      const recentBundleSize = this.metrics.slice(0, 10).reverse();
      summary.trends.bundleSize = recentBundleSize.map(m => ({
        pr: m.pr,
        total_kb: m.bundleSize?.total_kb || null,
        change_kb: m.bundleSize?.change_kb || null,
        change_percent: m.bundleSize?.change_percent || null
      }));
    }

    return summary;
  }

  async saveReport(outputPath) {
    const report = this.generateReport();
    
    // Ensure output directory exists
    const outputDir = path.dirname(outputPath);
    await fs.mkdir(outputDir, { recursive: true });

    // Write report
    await fs.writeFile(
      outputPath,
      JSON.stringify(report, null, 2),
      'utf-8'
    );

    console.log(`\n✅ Report saved to: ${outputPath}`);
    console.log(`📊 Total PRs analyzed: ${report.total_prs}`);
    console.log(`📅 Generated at: ${report.generated_at}`);
    
    return report;
  }
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  
  if (!token) {
    console.error('❌ Error: GITHUB_TOKEN environment variable is required');
    process.exit(1);
  }

  // Parse command line arguments
  const args = process.argv.slice(2);
  const limitArg = args.find(arg => arg.startsWith('--limit='));
  const limit = limitArg ? parseInt(limitArg.split('=')[1]) : DEFAULT_LIMIT;

  console.log('🚀 UX Metrics Aggregator');
  console.log('========================\n');

  const aggregator = new MetricsAggregator(token);
  
  try {
    await aggregator.aggregateMetrics(limit);
    
    const outputPath = path.join(__dirname, '../../metrics/ux-metrics.json');
    await aggregator.saveReport(outputPath);
    
    console.log('\n✨ Aggregation complete!');
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();

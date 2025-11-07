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
      apps: {}
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

    // Try to find and download artifacts for each metric type
    const metricTypes = ['i18n', 'a11y', 'motion', 'vrt'];
    
    for (const metricType of metricTypes) {
      try {
        // Find the check run for this metric
        const checkName = `${metricType.charAt(0).toUpperCase() + metricType.slice(1)} Coverage Check (${appName})`;
        const checkRun = checkRuns.find(run => run.name.includes(metricType) && run.name.includes(appName));
        
        if (checkRun && checkRun.conclusion === 'success') {
          // For now, we'll mark as available but not download artifacts
          // In a full implementation, we would download and parse artifacts here
          metrics[metricType] = {
            status: 'available',
            check_run_id: checkRun.id
          };
        }
      } catch (error) {
        console.error(`Error extracting ${metricType} for ${appName}:`, error.message);
      }
    }

    return metrics;
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
      apps: {}
    };

    // Calculate summary statistics for each app
    for (const app of ['frontend-dashboard', 'owner-console']) {
      const appMetrics = this.metrics
        .map(m => m.apps[app])
        .filter(Boolean);

      summary.apps[app] = {
        total_prs: appMetrics.length,
        i18n_available: appMetrics.filter(m => m.i18n?.status === 'available').length,
        a11y_available: appMetrics.filter(m => m.a11y?.status === 'available').length,
        motion_available: appMetrics.filter(m => m.motion?.status === 'available').length,
        vrt_available: appMetrics.filter(m => m.vrt?.status === 'available').length
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
        lcp_avg: lcpValues.length > 0 ? lcpValues.reduce((a, b) => a + b, 0) / lcpValues.length : null
      };
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

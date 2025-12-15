#!/usr/bin/env node

/**
 * Unit tests for PR Template Path Validation Script
 * Uses Node.js built-in test runner (node:test)
 * 
 * Run with: node --test scripts/tests/validate-pr-template-paths.test.mjs
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

import {
  extractRelativeLinks,
  findPRTemplates,
  validateTemplate,
  validateAllTemplates,
  PR_TEMPLATE_PATHS,
} from '../validate-pr-template-paths.mjs';

describe('extractRelativeLinks', () => {
  it('should extract simple relative paths', () => {
    const content = '[Link](../docs/README.md)';
    const links = extractRelativeLinks(content);
    
    assert.strictEqual(links.length, 1);
    assert.strictEqual(links[0].raw, '../docs/README.md');
    assert.strictEqual(links[0].normalized, '../docs/README.md');
    assert.strictEqual(links[0].line, 1);
  });

  it('should extract paths starting with ./', () => {
    const content = '[Link](./local/file.md)';
    const links = extractRelativeLinks(content);
    
    assert.strictEqual(links.length, 1);
    assert.strictEqual(links[0].normalized, './local/file.md');
  });

  it('should remove anchor fragments', () => {
    const content = '[Link](../CONTRIBUTING.md#section-name)';
    const links = extractRelativeLinks(content);
    
    assert.strictEqual(links.length, 1);
    assert.strictEqual(links[0].raw, '../CONTRIBUTING.md#section-name');
    assert.strictEqual(links[0].normalized, '../CONTRIBUTING.md');
  });

  it('should remove title attributes', () => {
    const content = '[Link](../docs/guide.md "Guide Title")';
    const links = extractRelativeLinks(content);
    
    assert.strictEqual(links.length, 1);
    assert.strictEqual(links[0].raw, '../docs/guide.md "Guide Title"');
    assert.strictEqual(links[0].normalized, '../docs/guide.md');
  });

  it('should handle both anchor and title', () => {
    const content = '[Link](../docs/guide.md#section "Title")';
    const links = extractRelativeLinks(content);
    
    assert.strictEqual(links.length, 1);
    assert.strictEqual(links[0].normalized, '../docs/guide.md');
  });

  it('should ignore absolute URLs', () => {
    const content = '[Link](https://example.com/path)';
    const links = extractRelativeLinks(content);
    
    assert.strictEqual(links.length, 0);
  });

  it('should ignore mailto links', () => {
    const content = '[Email](mailto:test@example.com)';
    const links = extractRelativeLinks(content);
    
    assert.strictEqual(links.length, 0);
  });

  it('should ignore local anchor links', () => {
    const content = '[Section](#local-section)';
    const links = extractRelativeLinks(content);
    
    assert.strictEqual(links.length, 0);
  });

  it('should ignore absolute paths', () => {
    const content = '[Link](/absolute/path.md)';
    const links = extractRelativeLinks(content);
    
    assert.strictEqual(links.length, 0);
  });

  it('should extract multiple links from same line', () => {
    const content = '[A](../a.md) and [B](../b.md)';
    const links = extractRelativeLinks(content);
    
    assert.strictEqual(links.length, 2);
    assert.strictEqual(links[0].normalized, '../a.md');
    assert.strictEqual(links[1].normalized, '../b.md');
  });

  it('should extract links from multiple lines with correct line numbers', () => {
    const content = 'Line 1\n[Link](../file.md)\nLine 3';
    const links = extractRelativeLinks(content);
    
    assert.strictEqual(links.length, 1);
    assert.strictEqual(links[0].line, 2);
  });

  it('should handle image links', () => {
    const content = '![Image](../images/screenshot.png)';
    const links = extractRelativeLinks(content);
    
    assert.strictEqual(links.length, 1);
    assert.strictEqual(links[0].normalized, '../images/screenshot.png');
  });

  it('should handle empty content', () => {
    const links = extractRelativeLinks('');
    assert.strictEqual(links.length, 0);
  });

  it('should handle content with no links', () => {
    const content = 'Just some text without any links.';
    const links = extractRelativeLinks(content);
    assert.strictEqual(links.length, 0);
  });

  it('should handle single quotes in title', () => {
    const content = "[Link](../docs/guide.md 'Guide Title')";
    const links = extractRelativeLinks(content);
    
    assert.strictEqual(links.length, 1);
    assert.strictEqual(links[0].normalized, '../docs/guide.md');
  });
});

describe('findPRTemplates', () => {
  let tempDir;

  it('should find standard PR template', () => {
    tempDir = mkdtempSync(join(tmpdir(), 'pr-template-test-'));
    mkdirSync(join(tempDir, '.github'), { recursive: true });
    writeFileSync(join(tempDir, '.github/pull_request_template.md'), '# PR Template');
    
    const templates = findPRTemplates(tempDir);
    
    assert.strictEqual(templates.length, 1);
    assert.strictEqual(templates[0], '.github/pull_request_template.md');
    
    rmSync(tempDir, { recursive: true });
  });

  it('should find templates in PULL_REQUEST_TEMPLATE directory', () => {
    tempDir = mkdtempSync(join(tmpdir(), 'pr-template-test-'));
    mkdirSync(join(tempDir, '.github/PULL_REQUEST_TEMPLATE'), { recursive: true });
    writeFileSync(join(tempDir, '.github/PULL_REQUEST_TEMPLATE/feature.md'), '# Feature');
    writeFileSync(join(tempDir, '.github/PULL_REQUEST_TEMPLATE/bugfix.md'), '# Bugfix');
    
    const templates = findPRTemplates(tempDir);
    
    assert.strictEqual(templates.length, 2);
    assert.ok(templates.includes('.github/PULL_REQUEST_TEMPLATE/feature.md'));
    assert.ok(templates.includes('.github/PULL_REQUEST_TEMPLATE/bugfix.md'));
    
    rmSync(tempDir, { recursive: true });
  });

  it('should find root-level PR template', () => {
    tempDir = mkdtempSync(join(tmpdir(), 'pr-template-test-'));
    writeFileSync(join(tempDir, 'PULL_REQUEST_TEMPLATE.md'), '# PR Template');
    
    const templates = findPRTemplates(tempDir);
    
    assert.strictEqual(templates.length, 1);
    assert.strictEqual(templates[0], 'PULL_REQUEST_TEMPLATE.md');
    
    rmSync(tempDir, { recursive: true });
  });

  it('should return empty array when no templates exist', () => {
    tempDir = mkdtempSync(join(tmpdir(), 'pr-template-test-'));
    
    const templates = findPRTemplates(tempDir);
    
    assert.strictEqual(templates.length, 0);
    
    rmSync(tempDir, { recursive: true });
  });

  it('should find multiple templates from different locations', () => {
    tempDir = mkdtempSync(join(tmpdir(), 'pr-template-test-'));
    mkdirSync(join(tempDir, '.github'), { recursive: true });
    writeFileSync(join(tempDir, '.github/pull_request_template.md'), '# PR Template');
    writeFileSync(join(tempDir, 'PULL_REQUEST_TEMPLATE.md'), '# Root Template');
    
    const templates = findPRTemplates(tempDir);
    
    assert.strictEqual(templates.length, 2);
    
    rmSync(tempDir, { recursive: true });
  });
});

describe('validateTemplate', () => {
  let tempDir;

  it('should pass when all paths are valid', () => {
    tempDir = mkdtempSync(join(tmpdir(), 'pr-template-test-'));
    mkdirSync(join(tempDir, '.github'), { recursive: true });
    mkdirSync(join(tempDir, 'docs'), { recursive: true });
    writeFileSync(join(tempDir, 'README.md'), '# README');
    writeFileSync(join(tempDir, 'docs/guide.md'), '# Guide');
    writeFileSync(join(tempDir, '.github/pull_request_template.md'), 
      '[README](../README.md)\n[Guide](../docs/guide.md)');
    
    const result = validateTemplate('.github/pull_request_template.md', tempDir);
    
    assert.strictEqual(result.valid, true);
    assert.strictEqual(result.errors.length, 0);
    assert.strictEqual(result.checked, 2);
    
    rmSync(tempDir, { recursive: true });
  });

  it('should fail when path does not exist', () => {
    tempDir = mkdtempSync(join(tmpdir(), 'pr-template-test-'));
    mkdirSync(join(tempDir, '.github'), { recursive: true });
    writeFileSync(join(tempDir, '.github/pull_request_template.md'), 
      '[Missing](../DOES_NOT_EXIST.md)');
    
    const result = validateTemplate('.github/pull_request_template.md', tempDir);
    
    assert.strictEqual(result.valid, false);
    assert.strictEqual(result.errors.length, 1);
    assert.strictEqual(result.errors[0].path, '../DOES_NOT_EXIST.md');
    assert.ok(result.errors[0].message.includes('File not found'));
    
    rmSync(tempDir, { recursive: true });
  });

  it('should report correct line number for errors', () => {
    tempDir = mkdtempSync(join(tmpdir(), 'pr-template-test-'));
    mkdirSync(join(tempDir, '.github'), { recursive: true });
    writeFileSync(join(tempDir, '.github/pull_request_template.md'), 
      'Line 1\nLine 2\n[Missing](../missing.md)\nLine 4');
    
    const result = validateTemplate('.github/pull_request_template.md', tempDir);
    
    assert.strictEqual(result.errors[0].line, 3);
    
    rmSync(tempDir, { recursive: true });
  });

  it('should validate paths with anchor fragments correctly', () => {
    tempDir = mkdtempSync(join(tmpdir(), 'pr-template-test-'));
    mkdirSync(join(tempDir, '.github'), { recursive: true });
    writeFileSync(join(tempDir, 'README.md'), '# README');
    writeFileSync(join(tempDir, '.github/pull_request_template.md'), 
      '[Section](../README.md#section)');
    
    const result = validateTemplate('.github/pull_request_template.md', tempDir);
    
    assert.strictEqual(result.valid, true);
    
    rmSync(tempDir, { recursive: true });
  });

  it('should handle multiple errors', () => {
    tempDir = mkdtempSync(join(tmpdir(), 'pr-template-test-'));
    mkdirSync(join(tempDir, '.github'), { recursive: true });
    writeFileSync(join(tempDir, '.github/pull_request_template.md'), 
      '[A](../a.md)\n[B](../b.md)\n[C](../c.md)');
    
    const result = validateTemplate('.github/pull_request_template.md', tempDir);
    
    assert.strictEqual(result.valid, false);
    assert.strictEqual(result.errors.length, 3);
    
    rmSync(tempDir, { recursive: true });
  });

  it('should pass when template has no relative links', () => {
    tempDir = mkdtempSync(join(tmpdir(), 'pr-template-test-'));
    mkdirSync(join(tempDir, '.github'), { recursive: true });
    writeFileSync(join(tempDir, '.github/pull_request_template.md'), 
      '# PR Template\n\nNo links here.');
    
    const result = validateTemplate('.github/pull_request_template.md', tempDir);
    
    assert.strictEqual(result.valid, true);
    assert.strictEqual(result.checked, 0);
    
    rmSync(tempDir, { recursive: true });
  });
});

describe('validateAllTemplates', () => {
  let tempDir;

  it('should return success when no templates exist', () => {
    tempDir = mkdtempSync(join(tmpdir(), 'pr-template-test-'));
    
    const result = validateAllTemplates(tempDir);
    
    assert.strictEqual(result.success, true);
    
    rmSync(tempDir, { recursive: true });
  });

  it('should return success when all templates are valid', () => {
    tempDir = mkdtempSync(join(tmpdir(), 'pr-template-test-'));
    mkdirSync(join(tempDir, '.github'), { recursive: true });
    writeFileSync(join(tempDir, 'README.md'), '# README');
    writeFileSync(join(tempDir, '.github/pull_request_template.md'), 
      '[README](../README.md)');
    
    const result = validateAllTemplates(tempDir);
    
    assert.strictEqual(result.success, true);
    assert.strictEqual(result.totalErrors, 0);
    
    rmSync(tempDir, { recursive: true });
  });

  it('should return failure when any template has errors', () => {
    tempDir = mkdtempSync(join(tmpdir(), 'pr-template-test-'));
    mkdirSync(join(tempDir, '.github'), { recursive: true });
    writeFileSync(join(tempDir, '.github/pull_request_template.md'), 
      '[Missing](../missing.md)');
    
    const result = validateAllTemplates(tempDir);
    
    assert.strictEqual(result.success, false);
    assert.strictEqual(result.totalErrors, 1);
    
    rmSync(tempDir, { recursive: true });
  });
});

describe('PR_TEMPLATE_PATHS', () => {
  it('should include standard GitHub template paths', () => {
    assert.ok(PR_TEMPLATE_PATHS.includes('.github/pull_request_template.md'));
    assert.ok(PR_TEMPLATE_PATHS.includes('.github/PULL_REQUEST_TEMPLATE'));
  });
});

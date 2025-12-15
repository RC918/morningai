#!/usr/bin/env node

/**
 * PR Template Path Validation Script
 * Issue: #2514
 * 
 * This script validates that relative paths in PR templates point to existing files.
 * It supports multiple PR template locations per GitHub conventions:
 * - .github/pull_request_template.md
 * - .github/PULL_REQUEST_TEMPLATE/*.md
 * - PULL_REQUEST_TEMPLATE.md (repo root)
 * 
 * Features:
 * - Extracts markdown links with relative paths (../ or ./)
 * - Removes anchor fragments (#...) and titles ("...") for file existence check
 * - Validates each path exists relative to the template's directory
 * - Outputs clear error messages for debugging
 */

import { existsSync, readdirSync, readFileSync, statSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = resolve(__dirname, '..');

/**
 * Known PR template locations per GitHub conventions
 */
export const PR_TEMPLATE_PATHS = [
  '.github/pull_request_template.md',
  '.github/PULL_REQUEST_TEMPLATE',
  'PULL_REQUEST_TEMPLATE.md',
  'pull_request_template.md',
];

/**
 * Extract relative path links from markdown content
 * Handles: [text](../path), [text](./path), [text](../path#anchor), [text](../path "title")
 * 
 * @param {string} content - Markdown file content
 * @returns {Array<{raw: string, normalized: string, line: number}>} - Extracted links
 */
export function extractRelativeLinks(content) {
  const links = [];
  const lines = content.split('\n');
  
  // Regex to match markdown links: [text](target)
  // Captures the target part which may include path, anchor, and title
  const linkRegex = /\]\(([^)]+)\)/g;
  
  lines.forEach((line, index) => {
    let match;
    while ((match = linkRegex.exec(line)) !== null) {
      const raw = match[1].trim();
      
      // Only process relative paths (starting with ./ or ../)
      if (!raw.startsWith('./') && !raw.startsWith('../')) {
        continue;
      }
      
      // Normalize: remove title (space followed by quoted string at end)
      // e.g., "../path.md \"title\"" -> "../path.md"
      let normalized = raw.replace(/\s+["'][^"']*["']\s*$/, '').trim();
      
      // Normalize: remove anchor fragment
      // e.g., "../path.md#section" -> "../path.md"
      normalized = normalized.replace(/#.*$/, '');
      
      // Normalize: remove angle brackets if present
      // e.g., "<../path.md>" -> "../path.md"
      normalized = normalized.replace(/^<|>$/g, '');
      
      links.push({
        raw,
        normalized,
        line: index + 1,
      });
    }
  });
  
  return links;
}

/**
 * Find all PR template files in the repository
 * 
 * @param {string} repoRoot - Repository root directory
 * @returns {string[]} - Array of template file paths (relative to repo root)
 */
export function findPRTemplates(repoRoot) {
  const templates = [];
  
  for (const templatePath of PR_TEMPLATE_PATHS) {
    const fullPath = join(repoRoot, templatePath);
    
    if (!existsSync(fullPath)) {
      continue;
    }
    
    const stat = statSync(fullPath);
    
    if (stat.isFile() && templatePath.endsWith('.md')) {
      templates.push(templatePath);
    } else if (stat.isDirectory()) {
      // Scan directory for .md files
      try {
        const files = readdirSync(fullPath);
        for (const file of files) {
          if (file.endsWith('.md')) {
            templates.push(join(templatePath, file));
          }
        }
      } catch (err) {
        console.error(`Warning: Could not read directory ${templatePath}: ${err.message}`);
      }
    }
  }
  
  return templates;
}

/**
 * Validate a single PR template file
 * 
 * @param {string} templatePath - Path to template (relative to repo root)
 * @param {string} repoRoot - Repository root directory
 * @returns {{valid: boolean, errors: Array<{path: string, line: number, message: string}>, checked: number}}
 */
export function validateTemplate(templatePath, repoRoot) {
  const fullTemplatePath = join(repoRoot, templatePath);
  const templateDir = dirname(fullTemplatePath);
  
  const content = readFileSync(fullTemplatePath, 'utf8');
  const links = extractRelativeLinks(content);
  
  const errors = [];
  
  for (const link of links) {
    // Resolve the path relative to the template's directory
    const resolvedPath = resolve(templateDir, link.normalized);
    
    if (!existsSync(resolvedPath)) {
      errors.push({
        path: link.normalized,
        raw: link.raw,
        line: link.line,
        message: `File not found: ${link.normalized}`,
        resolvedPath,
      });
    }
  }
  
  return {
    valid: errors.length === 0,
    errors,
    checked: links.length,
  };
}

/**
 * Main validation function
 * 
 * @param {string} repoRoot - Repository root directory
 * @returns {{success: boolean, results: Object}}
 */
export function validateAllTemplates(repoRoot) {
  console.log('=== PR Template Path Validation ===\n');
  
  const templates = findPRTemplates(repoRoot);
  
  if (templates.length === 0) {
    console.log('No PR templates found in repository.');
    return { success: true, results: {} };
  }
  
  console.log(`Found ${templates.length} PR template(s):\n`);
  templates.forEach(t => console.log(`  - ${t}`));
  console.log('');
  
  const results = {};
  let totalErrors = 0;
  let totalChecked = 0;
  
  for (const template of templates) {
    console.log(`Validating: ${template}`);
    
    const result = validateTemplate(template, repoRoot);
    results[template] = result;
    totalChecked += result.checked;
    
    if (result.valid) {
      console.log(`  Checked ${result.checked} link(s) - All valid\n`);
    } else {
      totalErrors += result.errors.length;
      console.log(`  Checked ${result.checked} link(s) - ${result.errors.length} error(s):\n`);
      
      for (const error of result.errors) {
        console.log(`    Line ${error.line}: ${error.message}`);
        console.log(`      Raw link: ${error.raw}`);
        console.log(`      Expected at: ${error.resolvedPath}\n`);
      }
    }
  }
  
  console.log('=== Summary ===');
  console.log(`Templates checked: ${templates.length}`);
  console.log(`Total links checked: ${totalChecked}`);
  console.log(`Total errors: ${totalErrors}`);
  
  if (totalErrors > 0) {
    console.log('\nPlease fix the invalid paths in the PR template(s).');
    console.log('Paths should be relative to the template file location.');
  } else {
    console.log('\nAll paths are valid!');
  }
  
  return {
    success: totalErrors === 0,
    results,
    totalChecked,
    totalErrors,
  };
}

// Run if executed directly (not imported)
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const repoRoot = process.argv[2] || rootDir;
  const result = validateAllTemplates(repoRoot);
  process.exit(result.success ? 0 : 1);
}

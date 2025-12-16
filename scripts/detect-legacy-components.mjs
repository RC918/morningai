#!/usr/bin/env node

/**
 * Legacy Component Detection Script (AST-based)
 * Issue: #2513
 * 
 * This script uses the TypeScript compiler API to accurately detect imports
 * of deprecated/legacy components in application code. Unlike regex-based
 * approaches, AST parsing correctly handles:
 * - Comments (single-line //, multi-line /* *\/)
 * - String literals containing component names
 * - Template literals
 * - Multiline imports
 * 
 * Usage:
 *   node scripts/detect-legacy-components.mjs [options]
 * 
 * Options:
 *   --dir <path>         Directory to scan (can be repeated)
 *   --allowlist <path>   Path to allowlist JSON file
 *   --components <list>  Comma-separated list of legacy components
 *   --strict             Exit with code 1 if violations found
 *   --json               Output results as JSON
 * 
 * Environment Variables:
 *   LEGACY_COMPONENT_SCAN_DIRS    Colon-separated list of directories to scan
 *   LEGACY_COMPONENT_ALLOWLIST    Path to allowlist JSON file
 *   LEGACY_COMPONENTS             Comma-separated list of legacy components
 * 
 * Dependencies:
 *   - Node.js >= 18
 *   - TypeScript (available in repo)
 */

import { existsSync, readFileSync, readdirSync, statSync } from 'fs';
import { dirname, extname, join, resolve, relative } from 'path';
import { fileURLToPath } from 'url';
import ts from 'typescript';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = resolve(__dirname, '..');

// Default configuration
const DEFAULT_LEGACY_COMPONENTS = ['LegacyCard', 'LegacyStatCard'];
const DEFAULT_SCAN_DIRS = [
  'handoff/20250928/40_App/owner-console/src',
  'handoff/20250928/40_App/frontend-dashboard/src',
];
const DEFAULT_ALLOWLIST_PATH = '.github/legacy-component-allowlist.json';

/**
 * Parse command line arguments
 */
function parseArgs(args) {
  const options = {
    dirs: [],
    allowlistPath: null,
    components: null,
    strict: false,
    json: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    switch (arg) {
      case '--dir':
        if (args[i + 1]) {
          options.dirs.push(args[++i]);
        }
        break;
      case '--allowlist':
        if (args[i + 1]) {
          options.allowlistPath = args[++i];
        }
        break;
      case '--components':
        if (args[i + 1]) {
          options.components = args[++i].split(',').map(c => c.trim());
        }
        break;
      case '--strict':
        options.strict = true;
        break;
      case '--json':
        options.json = true;
        break;
    }
  }

  return options;
}

/**
 * Load configuration from allowlist file
 */
function loadAllowlist(allowlistPath) {
  const fullPath = resolve(rootDir, allowlistPath);
  
  if (!existsSync(fullPath)) {
    return {
      legacy_components: DEFAULT_LEGACY_COMPONENTS,
      allowed_files: [],
      expires: null,
    };
  }

  try {
    const content = readFileSync(fullPath, 'utf8');
    return JSON.parse(content);
  } catch (err) {
    console.error(`Warning: Could not parse allowlist file: ${err.message}`);
    return {
      legacy_components: DEFAULT_LEGACY_COMPONENTS,
      allowed_files: [],
      expires: null,
    };
  }
}

/**
 * Check if a file is in the allowlist
 */
function isFileAllowed(filePath, allowedFiles) {
  const relativePath = relative(rootDir, filePath);
  
  for (const allowed of allowedFiles) {
    if (relativePath.includes(allowed)) {
      return true;
    }
  }
  
  return false;
}

/**
 * Find all JS/TS files in a directory recursively
 */
function findSourceFiles(dir) {
  const files = [];
  const extensions = ['.js', '.jsx', '.ts', '.tsx'];
  
  function walk(currentDir) {
    if (!existsSync(currentDir)) {
      return;
    }
    
    const entries = readdirSync(currentDir);
    
    for (const entry of entries) {
      const fullPath = join(currentDir, entry);
      
      try {
        const stat = statSync(fullPath);
        
        if (stat.isDirectory()) {
          // Skip node_modules and hidden directories
          if (entry !== 'node_modules' && !entry.startsWith('.')) {
            walk(fullPath);
          }
        } else if (stat.isFile() && extensions.includes(extname(entry))) {
          files.push(fullPath);
        }
      } catch (err) {
        // Skip files we can't access
      }
    }
  }
  
  walk(dir);
  return files;
}

/**
 * Extract imported identifiers from an ImportDeclaration node
 */
function getImportedIdentifiers(node) {
  const identifiers = [];
  
  if (node.importClause) {
    // Default import: import Foo from 'module'
    if (node.importClause.name) {
      identifiers.push(node.importClause.name.text);
    }
    
    // Named imports: import { Foo, Bar } from 'module'
    if (node.importClause.namedBindings) {
      if (ts.isNamedImports(node.importClause.namedBindings)) {
        for (const element of node.importClause.namedBindings.elements) {
          // Use the local name (aliased name if present)
          identifiers.push(element.name.text);
          // Also check the original name if aliased
          if (element.propertyName) {
            identifiers.push(element.propertyName.text);
          }
        }
      } else if (ts.isNamespaceImport(node.importClause.namedBindings)) {
        // Namespace import: import * as Foo from 'module'
        identifiers.push(node.importClause.namedBindings.name.text);
      }
    }
  }
  
  return identifiers;
}

/**
 * Analyze a single file for legacy component imports using AST
 */
function analyzeFile(filePath, legacyComponents) {
  const violations = [];
  
  try {
    const content = readFileSync(filePath, 'utf8');
    
    // Create a source file for parsing
    const sourceFile = ts.createSourceFile(
      filePath,
      content,
      ts.ScriptTarget.Latest,
      true, // setParentNodes
      filePath.endsWith('.tsx') || filePath.endsWith('.jsx')
        ? ts.ScriptKind.TSX
        : filePath.endsWith('.ts')
          ? ts.ScriptKind.TS
          : ts.ScriptKind.JS
    );
    
    // Walk the AST to find import declarations
    function visit(node) {
      if (ts.isImportDeclaration(node)) {
        const importedIdentifiers = getImportedIdentifiers(node);
        
        for (const identifier of importedIdentifiers) {
          if (legacyComponents.includes(identifier)) {
            const { line, character } = sourceFile.getLineAndCharacterOfPosition(node.getStart());
            
            violations.push({
              component: identifier,
              line: line + 1, // 1-indexed
              column: character + 1,
              importText: node.getText(sourceFile).split('\n')[0], // First line of import
            });
          }
        }
      }
      
      ts.forEachChild(node, visit);
    }
    
    visit(sourceFile);
  } catch (err) {
    console.error(`Warning: Could not analyze ${filePath}: ${err.message}`);
  }
  
  return violations;
}

/**
 * Main detection function
 */
export function detectLegacyComponents(options = {}) {
  // Resolve configuration
  const allowlistPath = options.allowlistPath 
    || process.env.LEGACY_COMPONENT_ALLOWLIST 
    || DEFAULT_ALLOWLIST_PATH;
  
  const allowlist = loadAllowlist(allowlistPath);
  
  const legacyComponents = options.components 
    || (process.env.LEGACY_COMPONENTS ? process.env.LEGACY_COMPONENTS.split(',').map(c => c.trim()) : null)
    || allowlist.legacy_components 
    || DEFAULT_LEGACY_COMPONENTS;
  
  let scanDirs = options.dirs.length > 0 
    ? options.dirs 
    : (process.env.LEGACY_COMPONENT_SCAN_DIRS 
        ? process.env.LEGACY_COMPONENT_SCAN_DIRS.split(':') 
        : DEFAULT_SCAN_DIRS);
  
  // Resolve directories relative to repo root
  scanDirs = scanDirs.map(dir => resolve(rootDir, dir));
  
  const results = {
    filesScanned: 0,
    violations: [],
    legacyComponents,
    scanDirs: scanDirs.map(d => relative(rootDir, d)),
    allowlistPath,
    allowedFiles: allowlist.allowed_files,
  };
  
  // Scan each directory
  for (const dir of scanDirs) {
    if (!existsSync(dir)) {
      continue;
    }
    
    const files = findSourceFiles(dir);
    
    for (const file of files) {
      results.filesScanned++;
      
      // Skip allowed files
      if (isFileAllowed(file, allowlist.allowed_files)) {
        continue;
      }
      
      const fileViolations = analyzeFile(file, legacyComponents);
      
      for (const violation of fileViolations) {
        results.violations.push({
          file: relative(rootDir, file),
          ...violation,
        });
      }
    }
  }
  
  return results;
}

/**
 * Format results for console output
 */
function formatResults(results, json = false) {
  if (json) {
    return JSON.stringify(results, null, 2);
  }
  
  const lines = [];
  
  lines.push('==============================================================================');
  lines.push('Legacy Component Detection (AST-based)');
  lines.push('==============================================================================');
  lines.push('');
  lines.push('Legacy components to detect:');
  for (const comp of results.legacyComponents) {
    lines.push(`  - ${comp}`);
  }
  lines.push('');
  lines.push('Scanning directories:');
  for (const dir of results.scanDirs) {
    lines.push(`  - ${dir}`);
  }
  lines.push('');
  lines.push('==============================================================================');
  lines.push('Results');
  lines.push('==============================================================================');
  lines.push('');
  lines.push(`Files scanned: ${results.filesScanned}`);
  lines.push(`Violations found: ${results.violations.length}`);
  lines.push('');
  
  if (results.violations.length > 0) {
    lines.push('Violations:');
    lines.push('');
    
    // Group by file
    const byFile = {};
    for (const v of results.violations) {
      if (!byFile[v.file]) {
        byFile[v.file] = [];
      }
      byFile[v.file].push(v);
    }
    
    for (const [file, violations] of Object.entries(byFile)) {
      lines.push(`${file}:`);
      for (const v of violations) {
        lines.push(`  Line ${v.line}: ${v.component}`);
        lines.push(`    ${v.importText}`);
      }
      lines.push('');
    }
    
    lines.push('==============================================================================');
    lines.push('Migration Guide');
    lines.push('==============================================================================');
    lines.push('');
    lines.push('Replace legacy components with shared-ui alternatives:');
    lines.push('');
    lines.push('  LegacyCard -> Card, StatCard, StatusCard, SettingsCard, or SectionCard');
    lines.push('  LegacyStatCard -> StatCard');
    lines.push('');
    lines.push('See CONTRIBUTING_DESIGN_SYSTEM.md for the LegacyCard replacement decision flow.');
    lines.push('');
    lines.push('If you need to temporarily allow a file, add it to:');
    lines.push(`  ${results.allowlistPath}`);
    lines.push('');
  } else {
    lines.push('\x1b[32mNo legacy component imports detected!\x1b[0m');
  }
  
  return lines.join('\n');
}

// Run if executed directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const options = parseArgs(process.argv.slice(2));
  const results = detectLegacyComponents(options);
  
  console.log(formatResults(results, options.json));
  
  if (results.violations.length > 0) {
    if (options.strict) {
      console.log('\x1b[31mSTRICT MODE: Failing due to legacy component violations.\x1b[0m');
      process.exit(1);
    } else {
      console.log('\x1b[33mWARNING MODE: Violations detected but not blocking.\x1b[0m');
      process.exit(0);
    }
  } else {
    process.exit(0);
  }
}

#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const findPackageJsonFiles = (dir, excludeDirs = ['node_modules', '.next', 'dist', '.venv']) => {
  const files = [];
  
  const walk = (currentPath) => {
    const entries = fs.readdirSync(currentPath, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(currentPath, entry.name);
      
      if (entry.isDirectory()) {
        if (!excludeDirs.includes(entry.name)) {
          walk(fullPath);
        }
      } else if (entry.name === 'package.json') {
        files.push(fullPath);
      }
    }
  };
  
  walk(dir);
  return files;
};

const analyzeDependencies = (files) => {
  const allDeps = new Map();
  const allDevDeps = new Map();
  const packageLocations = new Map();
  
  for (const file of files) {
    try {
      const content = JSON.parse(fs.readFileSync(file, 'utf8'));
      const relativePath = path.relative(process.cwd(), file);
      
      if (content.dependencies) {
        for (const [name, version] of Object.entries(content.dependencies)) {
          if (!allDeps.has(name)) {
            allDeps.set(name, new Map());
          }
          if (!allDeps.get(name).has(version)) {
            allDeps.get(name).set(version, []);
          }
          allDeps.get(name).get(version).push(relativePath);
        }
      }
      
      if (content.devDependencies) {
        for (const [name, version] of Object.entries(content.devDependencies)) {
          if (!allDevDeps.has(name)) {
            allDevDeps.set(name, new Map());
          }
          if (!allDevDeps.get(name).has(version)) {
            allDevDeps.get(name).set(version, []);
          }
          allDevDeps.get(name).get(version).push(relativePath);
        }
      }
      
      packageLocations.set(relativePath, content.name || relativePath);
    } catch (error) {
      console.error(`Error parsing ${file}:`, error.message);
    }
  }
  
  return { allDeps, allDevDeps, packageLocations };
};

const findDuplicates = (depsMap) => {
  const duplicates = [];
  
  for (const [name, versions] of depsMap.entries()) {
    if (versions.size > 1) {
      duplicates.push({
        name,
        versions: Array.from(versions.entries()).map(([version, files]) => ({
          version,
          count: files.length,
          files: files.slice(0, 5) // Show first 5 files
        }))
      });
    }
  }
  
  return duplicates.sort((a, b) => b.versions.length - a.versions.length);
};

const main = () => {
  console.log('🔍 Auditing package.json files...\n');
  
  const rootDir = process.cwd();
  const files = findPackageJsonFiles(rootDir);
  
  console.log(`Found ${files.length} package.json files\n`);
  
  const { allDeps, allDevDeps, packageLocations } = analyzeDependencies(files);
  
  console.log('📊 Dependency Analysis:\n');
  console.log(`Total unique dependencies: ${allDeps.size}`);
  console.log(`Total unique devDependencies: ${allDevDeps.size}\n`);
  
  const depDuplicates = findDuplicates(allDeps);
  const devDepDuplicates = findDuplicates(allDevDeps);
  
  console.log('🔴 Dependencies with multiple versions:\n');
  console.log(`Found ${depDuplicates.length} dependencies with version conflicts\n`);
  
  for (const dup of depDuplicates.slice(0, 20)) {
    console.log(`📦 ${dup.name}`);
    for (const { version, count, files } of dup.versions) {
      console.log(`  ${version} (${count} packages)`);
      for (const file of files) {
        console.log(`    - ${file}`);
      }
    }
    console.log('');
  }
  
  if (depDuplicates.length > 20) {
    console.log(`... and ${depDuplicates.length - 20} more\n`);
  }
  
  console.log('🟡 DevDependencies with multiple versions:\n');
  console.log(`Found ${devDepDuplicates.length} devDependencies with version conflicts\n`);
  
  for (const dup of devDepDuplicates.slice(0, 10)) {
    console.log(`📦 ${dup.name}`);
    for (const { version, count, files } of dup.versions) {
      console.log(`  ${version} (${count} packages)`);
      for (const file of files) {
        console.log(`    - ${file}`);
      }
    }
    console.log('');
  }
  
  if (devDepDuplicates.length > 10) {
    console.log(`... and ${devDepDuplicates.length - 10} more\n`);
  }
  
  const report = {
    totalPackages: files.length,
    totalDependencies: allDeps.size,
    totalDevDependencies: allDevDeps.size,
    dependenciesWithConflicts: depDuplicates.length,
    devDependenciesWithConflicts: devDepDuplicates.length,
    topConflicts: depDuplicates.slice(0, 50).map(d => ({
      name: d.name,
      versionCount: d.versions.length,
      versions: d.versions.map(v => v.version)
    }))
  };
  
  fs.writeFileSync(
    path.join(rootDir, 'DEPENDENCY_AUDIT_REPORT.json'),
    JSON.stringify(report, null, 2)
  );
  
  console.log('✅ Report saved to DEPENDENCY_AUDIT_REPORT.json\n');
};

main();

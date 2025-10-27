#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const packages = [
  'handoff/20250928/40_App/frontend-dashboard/package.json',
  'handoff/20250928/40_App/owner-console/package.json',
  'frontend-dashboard-deploy/package.json'
];

const loadPackageJson = (filePath) => {
  const fullPath = path.join(process.cwd(), filePath);
  return JSON.parse(fs.readFileSync(fullPath, 'utf8'));
};

const main = () => {
  console.log('📊 Comparing package.json files...\n');
  
  const pkgs = packages.map(p => ({
    path: p,
    data: loadPackageJson(p)
  }));
  
  const allDeps = new Set();
  const allDevDeps = new Set();
  
  pkgs.forEach(pkg => {
    if (pkg.data.dependencies) {
      Object.keys(pkg.data.dependencies).forEach(dep => allDeps.add(dep));
    }
    if (pkg.data.devDependencies) {
      Object.keys(pkg.data.devDependencies).forEach(dep => allDevDeps.add(dep));
    }
  });
  
  console.log(`Total unique dependencies: ${allDeps.size}`);
  console.log(`Total unique devDependencies: ${allDevDeps.size}\n`);
  
  console.log('🔍 Dependencies differences:\n');
  
  const depDiffs = [];
  allDeps.forEach(dep => {
    const versions = pkgs.map(pkg => ({
      name: path.basename(path.dirname(pkg.path)),
      version: pkg.data.dependencies?.[dep] || null
    }));
    
    const uniqueVersions = new Set(versions.filter(v => v.version !== null).map(v => v.version));
    
    if (uniqueVersions.size > 1 || versions.some(v => v.version === null)) {
      depDiffs.push({ dep, versions });
    }
  });
  
  if (depDiffs.length > 0) {
    console.log(`Found ${depDiffs.length} dependencies with differences:\n`);
    depDiffs.forEach(({ dep, versions }) => {
      console.log(`📦 ${dep}`);
      versions.forEach(({ name, version }) => {
        console.log(`  ${name}: ${version || 'NOT PRESENT'}`);
      });
      console.log('');
    });
  } else {
    console.log('✅ All dependencies are identical!\n');
  }
  
  console.log('🔍 DevDependencies differences:\n');
  
  const devDepDiffs = [];
  allDevDeps.forEach(dep => {
    const versions = pkgs.map(pkg => ({
      name: path.basename(path.dirname(pkg.path)),
      version: pkg.data.devDependencies?.[dep] || null
    }));
    
    const uniqueVersions = new Set(versions.filter(v => v.version !== null).map(v => v.version));
    
    if (uniqueVersions.size > 1 || versions.some(v => v.version === null)) {
      devDepDiffs.push({ dep, versions });
    }
  });
  
  if (devDepDiffs.length > 0) {
    console.log(`Found ${devDepDiffs.length} devDependencies with differences:\n`);
    devDepDiffs.forEach(({ dep, versions }) => {
      console.log(`📦 ${dep}`);
      versions.forEach(({ name, version }) => {
        console.log(`  ${name}: ${version || 'NOT PRESENT'}`);
      });
      console.log('');
    });
  } else {
    console.log('✅ All devDependencies are identical!\n');
  }
  
  console.log('📝 Generating unified dependencies...\n');
  
  const unifiedDeps = {};
  const unifiedDevDeps = {};
  
  allDeps.forEach(dep => {
    const versions = pkgs
      .map(pkg => pkg.data.dependencies?.[dep])
      .filter(v => v !== undefined);
    
    if (versions.length > 0) {
      unifiedDeps[dep] = versions[0];
    }
  });
  
  allDevDeps.forEach(dep => {
    const versions = pkgs
      .map(pkg => pkg.data.devDependencies?.[dep])
      .filter(v => v !== undefined);
    
    if (versions.length > 0) {
      unifiedDevDeps[dep] = versions[0];
    }
  });
  
  const report = {
    summary: {
      totalDependencies: allDeps.size,
      totalDevDependencies: allDevDeps.size,
      dependenciesWithDifferences: depDiffs.length,
      devDependenciesWithDifferences: devDepDiffs.length
    },
    dependencyDifferences: depDiffs,
    devDependencyDifferences: devDepDiffs,
    unifiedDependencies: unifiedDeps,
    unifiedDevDependencies: unifiedDevDeps
  };
  
  fs.writeFileSync(
    path.join(process.cwd(), 'PACKAGE_COMPARISON_REPORT.json'),
    JSON.stringify(report, null, 2)
  );
  
  console.log('✅ Report saved to PACKAGE_COMPARISON_REPORT.json\n');
};

main();

#!/usr/bin/env node

/**
 * Quick Merge Script - Merge translations between JSON files
 * 
 * Usage:
 *   npm run merge -- <source-file> <target-file> <output-file> <source-prefix> <target-prefix>
 * 
 * Example:
 *   npm run merge -- file1.json file2.json merged.json "BUI_" "TRA_"
 */

const { execSync } = require('child_process');

const args = process.argv.slice(2);

if (args.length !== 5) {
  console.error('Error: Invalid number of arguments');
  console.log('\nUsage:');
  console.log('  npm run merge -- <source-file> <target-file> <output-file> <source-prefix> <target-prefix>');
  console.log('\nExample:');
  console.log('  npm run merge -- file1.json file2.json merged.json "BUI_" "TRA_"');
  process.exit(1);
}

const [sourceFile, targetFile, outputFile, sourcePrefix, targetPrefix] = args;

const command = `node dist/index.js -m merge-json -sf "${sourceFile}" -tf "${targetFile}" -o "${outputFile}" -sp "${sourcePrefix}" -tp "${targetPrefix}"`;

try {
  console.log('Running merge...\n');
  execSync(command, { stdio: 'inherit' });
} catch (error) {
  process.exit(1);
}

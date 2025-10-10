#!/usr/bin/env node

import * as fs from 'fs';
import * as path from 'path';
import { MXMLConverter } from './converter';
import { JSONMerger } from './merger';

interface CliOptions {
  mode: 'mxml-to-json' | 'json-to-mxml' | 'merge-json';
  input: string;
  output: string;
  template?: string;
  sourceFile?: string;
  targetFile?: string;
  sourcePrefix?: string;
  targetPrefix?: string;
}

function parseArgs(): CliOptions | null {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    showHelp();
    return null;
  }

  const options: Partial<CliOptions> = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    switch (arg) {
      case '--mode':
      case '-m':
        const mode = args[++i];
        if (mode !== 'mxml-to-json' && mode !== 'json-to-mxml' && mode !== 'merge-json') {
          console.error('Error: Invalid mode. Use "mxml-to-json", "json-to-mxml", or "merge-json"');
          return null;
        }
        options.mode = mode;
        break;
      
      case '--input':
      case '-i':
        options.input = args[++i];
        break;
      
      case '--output':
      case '-o':
        options.output = args[++i];
        break;
      
      case '--template':
      case '-t':
        options.template = args[++i];
        break;
      
      case '--source-file':
      case '-sf':
        options.sourceFile = args[++i];
        break;
      
      case '--target-file':
      case '-tf':
        options.targetFile = args[++i];
        break;
      
      case '--source-prefix':
      case '-sp':
        options.sourcePrefix = args[++i];
        break;
      
      case '--target-prefix':
      case '-tp':
        options.targetPrefix = args[++i];
        break;
      
      default:
        console.error(`Error: Unknown option "${arg}"`);
        return null;
    }
  }

  // Validation based on mode
  if (!options.mode) {
    console.error('Error: Missing required argument --mode');
    showHelp();
    return null;
  }

  if (options.mode === 'merge-json') {
    if (!options.sourceFile || !options.targetFile || !options.output || !options.sourcePrefix || !options.targetPrefix) {
      console.error('Error: merge-json mode requires --source-file, --target-file, --output, --source-prefix, and --target-prefix');
      showHelp();
      return null;
    }
  } else {
    if (!options.input || !options.output) {
      console.error('Error: Missing required arguments --input and --output');
      showHelp();
      return null;
    }
  }

  return options as CliOptions;
}

function showHelp(): void {
  console.log(`
No Man's Sky Localization Converter
====================================

Usage:
  npm start -- --mode <mode> [options]

Modes:
  1. mxml-to-json: Convert MXML to JSON
  2. json-to-mxml: Convert JSON to MXML
  3. merge-json: Merge translations between two JSON files based on key prefix

Options for mxml-to-json and json-to-mxml:
  -m, --mode <mode>         Conversion mode: "mxml-to-json" or "json-to-mxml"
  -i, --input <file>        Input file path
  -o, --output <file>       Output file path
  -t, --template <file>     (Optional) Template MXML file for json-to-mxml mode

Options for merge-json:
  -m, --mode merge-json          Set mode to merge-json
  -sf, --source-file <file>      Source JSON file (contains translations)
  -tf, --target-file <file>      Target JSON file (to be updated)
  -o, --output <file>            Output file path
  -sp, --source-prefix <prefix>  Prefix of keys in source file (e.g., "BUI_")
  -tp, --target-prefix <prefix>  Prefix of keys in target file (e.g., "TRA_")

General Options:
  -h, --help                Show this help message

Examples:
  # Convert MXML to JSON
  npm start -- --mode mxml-to-json --input ../NMS_LOC1_ENGLISH.MXML --output output.json

  # Convert JSON to MXML
  npm start -- --mode json-to-mxml --input output.json --output NMS_LOC1_ENGLISH_NEW.MXML

  # Convert JSON to MXML with template
  npm start -- --mode json-to-mxml --input output.json --output new.MXML --template ../NMS_LOC1_ENGLISH.MXML

  # Merge translations from source to target based on prefix
  npm start -- --mode merge-json --source-file file1.json --target-file file2.json --output merged.json --source-prefix "BUI_" --target-prefix "TRA_"
  `);
}

async function main(): Promise<void> {
  const options = parseArgs();
  
  if (!options) {
    process.exit(1);
  }

  try {
    if (options.mode === 'merge-json') {
      // Validate files for merge-json mode
      if (!fs.existsSync(options.sourceFile!)) {
        console.error(`Error: Source file not found: ${options.sourceFile}`);
        process.exit(1);
      }
      if (!fs.existsSync(options.targetFile!)) {
        console.error(`Error: Target file not found: ${options.targetFile}`);
        process.exit(1);
      }

      const merger = new JSONMerger();
      console.log(`Starting merge process...`);
      console.log(`Source file: ${options.sourceFile} (prefix: "${options.sourcePrefix}")`);
      console.log(`Target file: ${options.targetFile} (prefix: "${options.targetPrefix}")`);
      console.log(`Output: ${options.output}`);

      await merger.merge({
        sourceFile: options.sourceFile!,
        targetFile: options.targetFile!,
        sourcePrefix: options.sourcePrefix!,
        targetPrefix: options.targetPrefix!,
        outputFile: options.output
      });
    } else {
      // Validate files for MXML conversion modes
      if (!fs.existsSync(options.input!)) {
        console.error(`Error: Input file not found: ${options.input}`);
        process.exit(1);
      }

      if (options.template && !fs.existsSync(options.template)) {
        console.error(`Error: Template file not found: ${options.template}`);
        process.exit(1);
      }

      const converter = new MXMLConverter();
      console.log(`Starting conversion: ${options.mode}`);
      console.log(`Input: ${options.input}`);
      console.log(`Output: ${options.output}`);
      
      if (options.mode === 'mxml-to-json') {
        await converter.mxmlToJson(options.input!, options.output);
      } else {
        await converter.jsonToMxml(options.input!, options.output, options.template);
      }
      
      console.log('\n✓ Conversion completed successfully!');
    }
  } catch (error) {
    console.error('\n✗ Operation failed:', error);
    process.exit(1);
  }
}

main();

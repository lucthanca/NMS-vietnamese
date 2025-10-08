#!/usr/bin/env node

import * as fs from 'fs';
import * as path from 'path';
import { MXMLConverter } from './converter';

interface CliOptions {
  mode: 'mxml-to-json' | 'json-to-mxml';
  input: string;
  output: string;
  template?: string;
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
        if (mode !== 'mxml-to-json' && mode !== 'json-to-mxml') {
          console.error('Error: Invalid mode. Use "mxml-to-json" or "json-to-mxml"');
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
      
      default:
        console.error(`Error: Unknown option "${arg}"`);
        return null;
    }
  }

  if (!options.mode || !options.input || !options.output) {
    console.error('Error: Missing required arguments');
    showHelp();
    return null;
  }

  return options as CliOptions;
}

function showHelp(): void {
  console.log(`
No Man's Sky Localization Converter
====================================

Usage:
  npm start -- --mode <mode> --input <input-file> --output <output-file> [--template <template-file>]

Options:
  -m, --mode <mode>         Conversion mode: "mxml-to-json" or "json-to-mxml"
  -i, --input <file>        Input file path
  -o, --output <file>       Output file path
  -t, --template <file>     (Optional) Template MXML file for json-to-mxml mode
  -h, --help                Show this help message

Examples:
  # Convert MXML to JSON
  npm start -- --mode mxml-to-json --input ../NMS_LOC1_ENGLISH.MXML --output output.json

  # Convert JSON to MXML
  npm start -- --mode json-to-mxml --input output.json --output NMS_LOC1_ENGLISH_NEW.MXML

  # Convert JSON to MXML with template
  npm start -- --mode json-to-mxml --input output.json --output new.MXML --template ../NMS_LOC1_ENGLISH.MXML
  `);
}

async function main(): Promise<void> {
  const options = parseArgs();
  
  if (!options) {
    process.exit(1);
  }

  // Check if input file exists
  if (!fs.existsSync(options.input)) {
    console.error(`Error: Input file not found: ${options.input}`);
    process.exit(1);
  }

  // Check if template file exists (if provided)
  if (options.template && !fs.existsSync(options.template)) {
    console.error(`Error: Template file not found: ${options.template}`);
    process.exit(1);
  }

  const converter = new MXMLConverter();

  try {
    console.log(`Starting conversion: ${options.mode}`);
    console.log(`Input: ${options.input}`);
    console.log(`Output: ${options.output}`);
    
    if (options.mode === 'mxml-to-json') {
      await converter.mxmlToJson(options.input, options.output);
    } else {
      await converter.jsonToMxml(options.input, options.output, options.template);
    }
    
    console.log('\n✓ Conversion completed successfully!');
  } catch (error) {
    console.error('\n✗ Conversion failed:', error);
    process.exit(1);
  }
}

main();

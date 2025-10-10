import * as fs from 'fs';

export interface MergeOptions {
  sourceFile: string;
  targetFile: string;
  sourcePrefix: string;
  targetPrefix: string;
  outputFile: string;
}

export interface MergeResult {
  merged: number;
  notFound: string[];
}

export class JSONMerger {
  /**
   * Remove prefix from a key
   */
  private removePrefix(key: string, prefix: string): string {
    if (key.startsWith(prefix)) {
      return key.substring(prefix.length);
    }
    return key;
  }

  /**
   * Merge translations from source file to target file based on key matching (without prefix)
   * @param options Merge options
   * @returns Merge result with statistics
   */
  async merge(options: MergeOptions): Promise<MergeResult> {
    try {
      // Read both files
      const sourceContent = fs.readFileSync(options.sourceFile, 'utf-8');
      const targetContent = fs.readFileSync(options.targetFile, 'utf-8');

      const sourceData: Record<string, string> = JSON.parse(sourceContent);
      const targetData: Record<string, string> = JSON.parse(targetContent);

      // Create a map of source keys without prefix
      const sourceMap = new Map<string, string>();
      for (const [key, value] of Object.entries(sourceData)) {
        const keyWithoutPrefix = this.removePrefix(key, options.sourcePrefix);
        sourceMap.set(keyWithoutPrefix, value);
      }

      // Process target file
      const result: Record<string, string> = {};
      const notFound: string[] = [];
      let mergedCount = 0;

      for (const [targetKey, targetValue] of Object.entries(targetData)) {
        const keyWithoutPrefix = this.removePrefix(targetKey, options.targetPrefix);
        
        if (sourceMap.has(keyWithoutPrefix)) {
          // Found matching key in source, use source value
          result[targetKey] = sourceMap.get(keyWithoutPrefix)!;
          mergedCount++;
        } else {
          // Not found, keep original value and add to notFound list
          result[targetKey] = targetValue;
          notFound.push(targetKey);
        }
      }

      // Write output file
      fs.writeFileSync(options.outputFile, JSON.stringify(result, null, 2), 'utf-8');

      // Export not found keys to separate file
      if (notFound.length > 0) {
        const notFoundData: Record<string, string> = {};
        notFound.forEach(key => {
          notFoundData[key] = targetData[key];
        });
        
        // Generate not found filename by adding suffix before extension
        const outputPath = options.outputFile;
        const lastDotIndex = outputPath.lastIndexOf('.');
        const notFoundPath = lastDotIndex > 0
          ? outputPath.substring(0, lastDotIndex) + '_not_found' + outputPath.substring(lastDotIndex)
          : outputPath + '_not_found.json';
        
        fs.writeFileSync(notFoundPath, JSON.stringify(notFoundData, null, 2), 'utf-8');
        console.log(`\n📄 Not found keys exported to: ${notFoundPath}`);
      }

      console.log(`\n✓ Merge completed successfully!`);
      console.log(`  - Total keys in target: ${Object.keys(targetData).length}`);
      console.log(`  - Merged from source: ${mergedCount}`);
      console.log(`  - Not found in source: ${notFound.length}`);
      
      if (notFound.length > 0) {
        console.log(`\nKeys not found in source file (after removing prefix "${options.targetPrefix}"):`);
        notFound.forEach(key => {
          const keyWithoutPrefix = this.removePrefix(key, options.targetPrefix);
          console.log(`  - ${key} (looking for: ${keyWithoutPrefix})`);
        });
      }

      return {
        merged: mergedCount,
        notFound
      };
    } catch (error) {
      console.error('Error during merge:', error);
      throw error;
    }
  }
}

import * as fs from 'fs';
import * as path from 'path';

export interface TranslationData {
  [key: string]: string;
}

export interface TranslatorOptions {
  templateMxmlPath: string;
  dataFolder: string;
  outputMxmlPath: string;
  notFoundJsonPath?: string;
}

export class MXMLTranslator {
  /**
   * Load all JSON files from data folder and merge them
   */
  private loadAllJsonData(dataFolder: string): TranslationData {
    const allData: TranslationData = {};
    
    try {
      const files = fs.readdirSync(dataFolder);
      const jsonFiles = files.filter(file => file.endsWith('.json'));
      
      console.log(`📂 Found ${jsonFiles.length} JSON files in ${dataFolder}`);
      
      for (const file of jsonFiles) {
        const filePath = path.join(dataFolder, file);
        try {
          const content = fs.readFileSync(filePath, 'utf-8');
          const data: TranslationData = JSON.parse(content);
          
          // Merge data
          Object.assign(allData, data);
          console.log(`  ✓ Loaded ${file}: ${Object.keys(data).length} entries`);
        } catch (error) {
          console.warn(`  ⚠ Failed to load ${file}:`, error);
        }
      }
      
      console.log(`\n📊 Total loaded entries: ${Object.keys(allData).length}\n`);
      return allData;
    } catch (error) {
      console.error('Error loading JSON data:', error);
      throw error;
    }
  }

  /**
   * Process MXML template with translation data
   */
  async translate(options: TranslatorOptions): Promise<void> {
    console.log('🚀 Starting translation process...\n');
    
    // Step 1: Load all JSON data
    const translationData = this.loadAllJsonData(options.dataFolder);
    const usedKeys = new Set<string>();
    
    // Step 2: Read template MXML
    console.log('📖 Reading template MXML...');
    if (!fs.existsSync(options.templateMxmlPath)) {
      throw new Error(`Template file not found: ${options.templateMxmlPath}`);
    }
    
    const xmlContent = fs.readFileSync(options.templateMxmlPath, 'utf-8');
    console.log('  ✓ Template loaded\n');
    
    // Step 3: Process MXML entries
    console.log('🔄 Processing translations...');
    let processedCount = 0;
    let notFoundCount = 0;
    
    const entryRegex = /<Property name="Table" value="TkLocalisationEntry" _id="([^"]+)"[^>]*>([\s\S]*?)<\/Property>/g;
    
    const newXmlContent = xmlContent.replace(entryRegex, (match, id, entryContent) => {
      // Extract current English value
      const englishRegex = /<Property name="English" value="([^"]*)"[^>]*\/>/;
      const englishMatch = englishRegex.exec(entryContent);
      
      if (!englishMatch) {
        return match; // Keep original if no English property found
      }
      
      const currentEnglishValue = englishMatch[1];
      
      // Check if we have translation for this ID
      if (translationData.hasOwnProperty(id)) {
        const vietnameseValue = translationData[id];
        usedKeys.add(id);
        processedCount++;
        
        // Replace: English -> French (backup original), Vietnamese -> English
        const updatedEntry = entryContent
          // First, update French with current English value
          // .replace(
          //   /<Property name="French" value="[^"]*"[^>]*\/>/,
          //   `<Property name="French" value="${currentEnglishValue}" />`
          // )
          // Then, update English with Vietnamese value
          .replace(
            /<Property name="English" value="[^"]*"[^>]*\/>/,
            `<Property name="English" value="${vietnameseValue}" />`
          );
        
        return `<Property name="Table" value="TkLocalisationEntry" _id="${id}">${updatedEntry}</Property>`;
      } else {
        notFoundCount++;
        return match; // Keep original if no translation found
      }
    });
    
    console.log(`  ✓ Processed: ${processedCount} entries`);
    console.log(`  ℹ Not found: ${notFoundCount} entries\n`);
    
    // Step 4: Write output MXML
    console.log('💾 Writing output MXML...');
    const outputDir = path.dirname(options.outputMxmlPath);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    fs.writeFileSync(options.outputMxmlPath, newXmlContent, 'utf-8');
    console.log(`  ✓ Output saved: ${options.outputMxmlPath}\n`);
    
    // Step 5: Write not found keys to JSON
    const notFoundKeys: TranslationData = {};
    for (const key in translationData) {
      if (!usedKeys.has(key)) {
        notFoundKeys[key] = translationData[key];
      }
    }
    
    if (Object.keys(notFoundKeys).length > 0) {
      const notFoundPath = options.notFoundJsonPath || 
        path.join(path.dirname(options.outputMxmlPath), 'not_found_in_template.json');
      
      console.log('📝 Writing unused translation keys...');
      fs.writeFileSync(notFoundPath, JSON.stringify(notFoundKeys, null, 2), 'utf-8');
      console.log(`  ✓ Unused keys saved: ${notFoundPath}`);
      console.log(`  ℹ Total unused: ${Object.keys(notFoundKeys).length} entries\n`);
    } else {
      console.log('✅ All translation keys were used!\n');
    }
    
    // Summary
    console.log('═══════════════════════════════════════');
    console.log('📊 TRANSLATION SUMMARY');
    console.log('═══════════════════════════════════════');
    console.log(`Total translations loaded: ${Object.keys(translationData).length}`);
    console.log(`Entries processed: ${processedCount}`);
    console.log(`Entries not found in template: ${notFoundCount}`);
    console.log(`Unused translation keys: ${Object.keys(notFoundKeys).length}`);
    console.log('═══════════════════════════════════════');
    console.log('\n✅ Translation completed successfully!');
  }
}

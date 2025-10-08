import * as fs from 'fs';
import * as path from 'path';

export interface LocalizationEntry {
  [key: string]: string;
}

export class MXMLConverter {
  /**
   * Escape special XML characters to preserve HTML entities
   */
  private escapeXmlEntities(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');
  }

  /**
   * Unescape XML entities for JSON output
   */
  private unescapeXmlEntities(text: string): string {
    return text
      .replace(/&apos;/g, "'")
      .replace(/&quot;/g, '"')
      .replace(/&gt;/g, '>')
      .replace(/&lt;/g, '<')
      .replace(/&amp;/g, '&');
  }

  /**
   * Convert MXML to simplified JSON format
   * @param mxmlPath Path to MXML file
   * @param jsonPath Output path for JSON file
   */
  async mxmlToJson(mxmlPath: string, jsonPath: string): Promise<void> {
    try {
      const xmlContent = fs.readFileSync(mxmlPath, 'utf-8');
      const entries: LocalizationEntry = {};

      // Use regex to extract entries while preserving HTML entities
      const entryRegex = /<Property name="Table" value="TkLocalisationEntry" _id="([^"]+)"[^>]*>([\s\S]*?)<\/Property>/g;
      let entryMatch;

      while ((entryMatch = entryRegex.exec(xmlContent)) !== null) {
        const id = entryMatch[1];
        const entryContent = entryMatch[2];

        // Extract English property value while preserving entities
        const englishRegex = /<Property name="English" value="([^"]*)"[^>]*\/>/;
        const englishMatch = englishRegex.exec(entryContent);

        if (englishMatch) {
          // Store the raw value with HTML entities preserved
          entries[id] = englishMatch[1];
        }
      }

      // Write to JSON file
      fs.writeFileSync(jsonPath, JSON.stringify(entries, null, 2), 'utf-8');
      console.log(`✓ Successfully converted MXML to JSON: ${jsonPath}`);
    } catch (error) {
      console.error('Error converting MXML to JSON:', error);
      throw error;
    }
  }

  /**
   * Convert simplified JSON back to MXML format
   * @param jsonPath Path to JSON file
   * @param mxmlPath Output path for MXML file
   * @param templatePath Optional: Path to template MXML file for structure reference
   */
  async jsonToMxml(jsonPath: string, mxmlPath: string, templatePath?: string): Promise<void> {
    try {
      const jsonContent = fs.readFileSync(jsonPath, 'utf-8');
      const entries: LocalizationEntry = JSON.parse(jsonContent);

      // Build XML manually to preserve HTML entities
      let xmlContent = '<?xml version="1.0" encoding="utf-8"?>\n';
      xmlContent += '<!--File created using MBINCompiler version (6.06.0.1)-->\n';
      xmlContent += '<Data template="cTkLocalisationTable">\n';
      xmlContent += '\t<Property name="Table">\n';

      Object.entries(entries).forEach(([id, text]) => {
        xmlContent += `\t\t<Property name="Table" value="TkLocalisationEntry" _id="${id}">\n`;
        xmlContent += `\t\t\t<Property name="Id" value="${id}" />\n`;
        xmlContent += `\t\t\t<Property name="English" value="${text}" />\n`;
        xmlContent += '\t\t\t<Property name="French" value="" />\n';
        xmlContent += '\t\t\t<Property name="Italian" value="" />\n';
        xmlContent += '\t\t\t<Property name="German" value="" />\n';
        xmlContent += '\t\t\t<Property name="Spanish" value="" />\n';
        xmlContent += '\t\t\t<Property name="Russian" value="" />\n';
        xmlContent += '\t\t\t<Property name="Polish" value="" />\n';
        xmlContent += '\t\t\t<Property name="Dutch" value="" />\n';
        xmlContent += '\t\t\t<Property name="Portuguese" value="" />\n';
        xmlContent += '\t\t\t<Property name="LatinAmericanSpanish" value="" />\n';
        xmlContent += '\t\t\t<Property name="BrazilianPortuguese" value="" />\n';
        xmlContent += '\t\t\t<Property name="SimplifiedChinese" value="" />\n';
        xmlContent += '\t\t\t<Property name="TraditionalChinese" value="" />\n';
        xmlContent += '\t\t\t<Property name="TencentChinese" value="" />\n';
        xmlContent += '\t\t\t<Property name="Korean" value="" />\n';
        xmlContent += '\t\t\t<Property name="Japanese" value="" />\n';
        xmlContent += '\t\t\t<Property name="USEnglish" value="" />\n';
        xmlContent += '\t\t</Property>\n';
      });

      xmlContent += '\t</Property>\n';
      xmlContent += '</Data>\n';

      fs.writeFileSync(mxmlPath, xmlContent, 'utf-8');
      console.log(`✓ Successfully converted JSON to MXML: ${mxmlPath}`);
    } catch (error) {
      console.error('Error converting JSON to MXML:', error);
      throw error;
    }
  }

}

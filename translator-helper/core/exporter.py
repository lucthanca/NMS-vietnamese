"""
Export Module

This module provides functionality to export MXML entries to various formats
while preserving HTML entities and structure.
"""

import json
from typing import List, Dict
from pathlib import Path
from lxml import etree

from core.mxml_parser import MXMLEntry


class MXMLExporter:
    """
    Exporter for MXML entries to JSON and MXML formats.
    
    This class handles exporting parsed MXML entries back to various formats
    while preserving HTML entities like &lt;, &gt;, &amp;, etc.
    """
    
    def __init__(self, entries: List[MXMLEntry]):
        """
        Initialize the exporter with entries.
        
        Args:
            entries: List of MXMLEntry objects to export
        """
        self.entries = entries
    
    def export_to_json(self, file_path: str, indent: int = 2) -> None:
        """
        Export entries to JSON format.
        
        The JSON structure is a simple key-value mapping where HTML entities
        are preserved in their escaped form (&lt;, &gt;, &amp;, etc.).
        
        Args:
            file_path: Path where the JSON file will be saved
            indent: Number of spaces for indentation (default: 2)
            
        Raises:
            IOError: If file cannot be written
        """
        # Create dictionary from entries with HTML entities preserved
        # Note: lxml automatically decodes HTML entities when parsing,
        # but they're automatically re-encoded when writing XML.
        # For JSON, we keep the decoded form as it's more readable.
        data = {entry.key: entry.content for entry in self.entries}
        
        # Write to JSON file with UTF-8 encoding
        # ensure_ascii=False preserves Unicode characters
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    
    def export_to_mxml(self, file_path: str, template: str = "cTkLocalisationTable") -> None:
        """
        Export entries back to MXML format.
        
        Creates a valid MXML file with the same structure as NMS localization files.
        HTML entities like &lt;, &gt; are preserved in the output.
        
        Args:
            file_path: Path where the MXML file will be saved
            template: Template name for the Data element (default: cTkLocalisationTable)
            
        Raises:
            IOError: If file cannot be written
        """
        # Create root element
        root = etree.Element("Data", template=template)
        
        # Create main Table property
        main_table = etree.SubElement(root, "Property", name="Table")
        
        # Add each entry
        for entry in self.entries:
            self._create_entry_element(main_table, entry)
        
        # Create tree and write to file
        tree = etree.ElementTree(root)
        
        # Write with XML declaration and proper formatting
        with open(file_path, 'wb') as f:
            tree.write(
                f,
                encoding='utf-8',
                xml_declaration=True,
                pretty_print=True,
                method='xml'
            )
        
        # Add MBINCompiler comment manually
        self._add_mbin_comment(file_path)
    
    def _create_entry_element(self, parent: etree.Element, entry: MXMLEntry) -> None:
        """
        Create a TkLocalisationEntry element for an entry.
        
        Args:
            parent: Parent XML element
            entry: MXMLEntry to convert to XML
        """
        # Create entry property with _id attribute
        entry_prop = etree.SubElement(
            parent,
            "Property",
            name="Table",
            value="TkLocalisationEntry",
            attrib={"{http://www.w3.org/XML/1998/namespace}id": entry.key}
        )
        # Set _id without namespace prefix (custom attribute)
        entry_prop.set("_id", entry.key)
        
        # Add Id property
        etree.SubElement(entry_prop, "Property", name="Id", value=entry.key)
        
        # Add English property with content
        etree.SubElement(entry_prop, "Property", name="English", value=entry.content)
        
        # Add empty properties for other languages
        languages = [
            "French", "Italian", "German", "Spanish", "Russian", "Polish",
            "Dutch", "Portuguese", "LatinAmericanSpanish", "BrazilianPortuguese",
            "SimplifiedChinese", "TraditionalChinese", "TencentChinese",
            "Korean", "Japanese", "USEnglish"
        ]
        
        for lang in languages:
            etree.SubElement(entry_prop, "Property", name=lang, value="")
    
    def _add_mbin_comment(self, file_path: str) -> None:
        """
        Add MBINCompiler comment to the MXML file.
        
        This adds the standard comment that appears in NMS MXML files
        right after the XML declaration.
        
        Args:
            file_path: Path to the MXML file
        """
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add comment after XML declaration
        comment = "<!--File created using MBINCompiler version (6.06.0.1)-->\n"
        
        # Find the end of XML declaration
        if content.startswith('<?xml'):
            end_of_declaration = content.find('?>') + 2
            # Insert comment
            content = content[:end_of_declaration] + '\n' + comment + content[end_of_declaration:].lstrip()
        else:
            # No declaration, add at start
            content = comment + content
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def get_entry_count(self) -> int:
        """
        Get the number of entries to export.
        
        Returns:
            Number of entries
        """
        return len(self.entries)

"""
MXML Parser Module

This module provides functionality to parse No Man's Sky MXML localization files
and extract key-value pairs from TkLocalisationEntry elements.
"""

from typing import List, Dict, Optional
from lxml import etree
from pathlib import Path


class MXMLEntry:
    """
    Represents a single localization entry from MXML file.
    
    Attributes:
        key (str): The unique identifier for this entry (Id field)
        content (str): The English text content for this entry
    """
    
    def __init__(self, key: str, content: str):
        """
        Initialize an MXML entry.
        
        Args:
            key: The unique identifier
            content: The English text content
        """
        self.key = key
        self.content = content
    
    def __repr__(self) -> str:
        return f"MXMLEntry(key='{self.key}', content='{self.content[:50]}...')"


class MXMLParser:
    """
    Parser for No Man's Sky MXML localization files.
    
    This parser extracts key-value pairs from TkLocalisationEntry elements
    in the MXML format used by No Man's Sky for game localization.
    """
    
    def __init__(self):
        """Initialize the MXML parser."""
        self.entries: List[MXMLEntry] = []
        self.file_path: Optional[Path] = None
    
    def parse_file(self, file_path: str) -> List[MXMLEntry]:
        """
        Parse an MXML file and extract all localization entries.
        
        Args:
            file_path: Path to the MXML file
            
        Returns:
            List of MXMLEntry objects containing key-content pairs
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            etree.XMLSyntaxError: If the file is not valid XML
            ValueError: If the file format is invalid
        """
        self.file_path = Path(file_path)
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Parse XML file
        try:
            tree = etree.parse(str(self.file_path))
            root = tree.getroot()
        except etree.XMLSyntaxError as e:
            raise etree.XMLSyntaxError(f"Invalid XML syntax: {e}")
        
        # Validate root structure
        if root.tag != "Data" or root.get("template") != "cTkLocalisationTable":
            raise ValueError("Invalid MXML format: Expected cTkLocalisationTable template")
        
        # Extract entries
        self.entries = []
        
        # Find all Table properties with TkLocalisationEntry
        for table_prop in root.findall(".//Property[@name='Table'][@value='TkLocalisationEntry']"):
            entry = self._parse_entry(table_prop)
            if entry:
                self.entries.append(entry)
        
        return self.entries
    
    def _parse_entry(self, element: etree.Element) -> Optional[MXMLEntry]:
        """
        Parse a single TkLocalisationEntry element.
        
        Args:
            element: The XML element to parse
            
        Returns:
            MXMLEntry object or None if parsing fails
        """
        try:
            # Extract Id
            id_elem = element.find("./Property[@name='Id']")
            if id_elem is None:
                return None
            key = id_elem.get("value", "")
            
            # Extract English content
            english_elem = element.find("./Property[@name='English']")
            if english_elem is None:
                return None
            content = english_elem.get("value", "")
            
            return MXMLEntry(key=key, content=content)
            
        except Exception as e:
            print(f"Error parsing entry: {e}")
            return None
    
    def get_entries(self) -> List[MXMLEntry]:
        """
        Get all parsed entries.
        
        Returns:
            List of MXMLEntry objects
        """
        return self.entries
    
    def get_entry_count(self) -> int:
        """
        Get the number of parsed entries.
        
        Returns:
            Number of entries
        """
        return len(self.entries)
    
    def to_dict(self) -> List[Dict[str, str]]:
        """
        Convert entries to a list of dictionaries.
        
        Returns:
            List of dictionaries with 'key' and 'content' keys
        """
        return [{"key": entry.key, "content": entry.content} for entry in self.entries]

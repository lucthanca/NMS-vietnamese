# Get JSON data from a file
import json
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_json_data(file_path):
  with open(file_path, 'r', encoding='utf-8') as file:
    return json.load(file)
  
  # Write JSON data to a file
def write_json_data(file_path, data):
  with open(file_path, 'w', encoding='utf-8') as file:
    json.dump(data, file, indent=4)
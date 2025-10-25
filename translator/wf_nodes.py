import logging
from pathlib import Path
import json
from datetime import datetime
from langchain_core.messages.human import HumanMessage
from langchain_core.messages.system import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from promts import SYSTEM_PROMPT, get_translation_prompt
from state import State
from utils import get_json_data

load_dotenv()

#Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))

def load_json_file(state: State):
  loc_name = state['loc_name']
  start_time = datetime.now()
  logger.info(f"🚀 [LOAD_JSON_FILE] Loading JSON file for file Localization: {loc_name}")
  logger.info(f"⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

  try:
    """
    Load the JSON file into memory from input folder
    """
    loc_file = Path("input") / loc_name
    if not loc_file.exists():
      logger.error(f"Requirement file not found: {loc_file}")
      end_time = datetime.now()
      execution_time = (end_time - start_time).total_seconds()
      logger.error(f" [LOAD_JSON_FILE] File not found for Localization: {loc_name}")
      logger.error(f"⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
      logger.error(f"⏱️ Execution time: {execution_time:.2f} seconds")
      state['string_part_state'] = 3  # failed
      return False
    return {
      total_strings: get_json_data(loc_file)
    }

  except Exception as e:
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    logger.error(f"❌ [LOAD_JSON_FILE] Error loading JSON file for Localization: {loc_name}. Error: {str(e)}")
    logger.error(f"⏰ End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.error(f"⏱️ Execution time: {execution_time:.2f} seconds")
    logger.error(f"💥 Error: {str(e)}")
    state['string_part_state'] = 3  # failed
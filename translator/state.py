from typing import Dict

class State(Dict):
  string_part_state: int #0: start, 1: in progress: 2: completed, 3: failed
  loc_name: str
  current_string_patch: list[dict[str, str]]
  total_strings: list[dict[str, str]]
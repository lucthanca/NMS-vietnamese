"""
Translation configuration.
"""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class WorkflowType(Enum):
    """Translation workflow types."""
    SEQUENCE = "sequence"
    FULL_PARALLEL = "full_parallel"


@dataclass
class TranslationConfig:
    """
    Configuration for translation engine.

    Attributes:
        api_key: Gemini API key
        workflow_type: Type of workflow to use (sequence or full_parallel)
        token_limit: Maximum tokens per patch
        max_retries: Maximum number of retries for failed translations
        model_name: Gemini model name
        temperature: Model temperature
    """
    api_key: str
    workflow_type: WorkflowType = WorkflowType.SEQUENCE
    token_limit: int = 50000
    max_retries: int = 3
    model_name: str = "gemini-2.0-flash-exp"
    temperature: float = 0.1

    @classmethod
    def load_from_settings(cls, settings_path: Path) -> "TranslationConfig":
        """Load configuration from settings file."""
        import json
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                data = json.load(f)
                workflow = WorkflowType(data.get('workflow_type', 'sequence'))
                return cls(
                    api_key=data.get('api_key', ''),
                    workflow_type=workflow,
                    token_limit=data.get('token_limit', 50000),
                    max_retries=data.get('max_retries', 3)
                )
        return cls(api_key='')

    def save_to_settings(self, settings_path: Path):
        """Save configuration to settings file."""
        import json
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_path, 'w') as f:
            json.dump({
                'api_key': self.api_key,
                'workflow_type': self.workflow_type.value,
                'token_limit': self.token_limit,
                'max_retries': self.max_retries
            }, f, indent=2)

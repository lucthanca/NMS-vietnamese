"""Workflows package."""
from .sequence_wf import create_sequence_workflow
from .parallel_wf import create_parallel_workflow

__all__ = ['create_sequence_workflow', 'create_parallel_workflow']

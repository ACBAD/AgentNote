"""
AgentNote - 基于AI的自动化Notebook生成和执行框架
"""

__version__ = "1.0.0"
__author__ = "AgentNote Team"

from .core.config import config
from .agents.note_agent import NoteAgent

__all__ = ['config', 'NoteAgent']
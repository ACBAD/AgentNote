"""
AgentNote - 基于OODA循环的自动化Notebook生成和执行框架
"""

__version__ = "1.0.1"
__author__ = "AgentNote Team"

from .core.config import config
from .agents.commander_agent import CommanderAgent

__all__ = ['config', 'CommanderAgent']
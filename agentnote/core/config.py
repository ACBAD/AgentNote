import os
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class NotebookConfig:
    update_mode: str = "append"
    notebook_name: str = "ooda_notebook.ipynb"
    code_cell_tag: str = "agent-code-cell"
    markdown_cell_tag: str = "agent-markdown-cell"
    max_cells: int = 300
    sleep_interval: int = 1
    export_json: bool = True
    json_output_file: str = "ooda_notebook_cells.json"

    context_max_cells: int = 10
    include_code_in_context: bool = True
    include_markdown_in_context: bool = True
    include_outputs_in_context: bool = True
    add_timestamp: bool = True

@dataclass
class DeepSeekConfig:
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4000
    think_mode: bool = False
    debug: bool = False

@dataclass
class AgentConfig:
    max_retries: int = 3
    retry_delay: int = 2
    enable_auto_fix: bool = True
    enable_execution: bool = True
    commander_debug: bool = False

@dataclass
class OODAConfig:
    max_circles: int = 5
    max_phase_retries: int = 3
    max_task_retries: int = 2
    enable_circle_reflection: bool = True
    enable_phase_reflection: bool = True
    enable_task_reflection: bool = True

@dataclass
class Config:
    notebook: NotebookConfig = field(default_factory=NotebookConfig)
    deepseek: DeepSeekConfig = field(default_factory=DeepSeekConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    ooda: OODAConfig = field(default_factory=OODAConfig)
    
    def update_from_dict(self, config_dict: Dict[str, Any]):
        """从字典更新配置"""
        for section, values in config_dict.items():
            if hasattr(self, section):
                section_obj = getattr(self, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)

# 全局配置实例
config = Config()
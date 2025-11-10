import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class NotebookConfig:
    update_mode: str = "append"
    notebook_name: str = "agent_generated_notebook.ipynb"
    code_cell_tag: str = "agent-code-cell"
    markdown_cell_tag: str = "agent-markdown-cell"
    max_cells: int = 300
    sleep_interval: int = 1
    export_json: bool = True
    json_output_file: str = "agent_notebook_cells.json"

    context_max_cells: int = 5
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
    max_tokens: int = 1000000

@dataclass
class AgentConfig:
    max_retries: int = 3
    retry_delay: int = 2
    enable_auto_fix: bool = True
    enable_execution: bool = True

class Config:
    def __init__(self):
        self.notebook = NotebookConfig()
        self.deepseek = DeepSeekConfig()
        self.agent = AgentConfig()
    
    def update_from_dict(self, config_dict: Dict[str, Any]):
        """从字典更新配置"""
        if 'notebook' in config_dict:
            for key, value in config_dict['notebook'].items():
                if hasattr(self.notebook, key):
                    setattr(self.notebook, key, value)
        
        if 'deepseek' in config_dict:
            for key, value in config_dict['deepseek'].items():
                if hasattr(self.deepseek, key):
                    setattr(self.deepseek, key, value)
        
        if 'agent' in config_dict:
            for key, value in config_dict['agent'].items():
                if hasattr(self.agent, key):
                    setattr(self.agent, key, value)

# 全局配置实例
config = Config()
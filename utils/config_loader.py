import yaml
import os
from typing import Dict, Any
from ..core.config import config

from pathlib import Path

def load_config_from_yaml(file_path: str = "config.yaml"):
    """从YAML文件加载配置"""
    # 使用pathlib处理路径
    config_path = Path(file_path)
    
    # 如果文件不存在，尝试在脚本同目录查找
    if not config_path.exists():
        config_path = Path(__file__).parent / file_path
    
    print(f"查找配置文件: {config_path.absolute()}")
    
    if not config_path.exists():
        print(f"配置文件 {config_path} 不存在，使用默认配置")
        return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        config.update_from_dict(config_data)
        print("配置已从YAML文件加载")
        
    except Exception as e:
        print(f"加载配置文件时出错: {e}")

def save_config_to_yaml(file_path: str = "config.yaml"):
    """保存配置到YAML文件"""
    try:
        config_data = {
            'notebook': {
                'update_mode': config.notebook.update_mode,
                'notebook_name': config.notebook.notebook_name,
                'code_cell_tag': config.notebook.code_cell_tag,
                'markdown_cell_tag': config.notebook.markdown_cell_tag,
                'max_cells': config.notebook.max_cells,
                'sleep_interval': config.notebook.sleep_interval,
                'export_json': config.notebook.export_json,
                'json_output_file': config.notebook.json_output_file,
            },
            'deepseek': {
                'api_key': config.deepseek.api_key,
                'base_url': config.deepseek.base_url,
                'model': config.deepseek.model,
                'temperature': config.deepseek.temperature,
                'max_tokens': config.deepseek.max_tokens,
            },
            'agent': {
                'max_retries': config.agent.max_retries,
                'retry_delay': config.agent.retry_delay,
                'enable_auto_fix': config.agent.enable_auto_fix,
                'enable_execution': config.agent.enable_execution,
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        print(f"配置已保存到: {file_path}")
        
    except Exception as e:
        print(f"保存配置到YAML时出错: {e}")
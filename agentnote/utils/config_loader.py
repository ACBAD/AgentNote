import yaml
import os
from typing import Dict, Any
from ..core.config import config
from ..utils.setup_logger import get_logger
from pathlib import Path
from dataclasses import asdict

logger = get_logger('ConfigLoader')

def load_config_from_yaml(file_path: str = "config.yaml"):
    """从YAML文件加载配置"""
    # 使用pathlib处理路径
    config_path = Path(file_path)
    
    # 如果文件不存在，尝试在脚本同目录查找
    if not config_path.exists():
        config_path = Path(__file__).parent / file_path
    
    logger.info(f"查找配置文件: {config_path.absolute()}")
    
    if not config_path.exists():
        logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    config.update_from_dict(config_data)
    logger.info("配置已从YAML文件加载")

def save_config_to_yaml(file_path: str = "config.yaml"):
    """保存配置到YAML文件"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(asdict(config), f, default_flow_style=False, allow_unicode=True, indent=2)
    
    logger.info(f"配置已保存到: {file_path}")
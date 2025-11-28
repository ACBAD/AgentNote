from enum import Enum
from typing import Any, Dict 

class OutputType(Enum):
    MARKDOWN = "markdown"
    CODE = "code"
    EXECUTION_RESULT = "execution_result"

class Output:
    """输出"""
    
    def __init__(self, output_type: OutputType, content: str, execute: bool = False):
        self.output_type = output_type
        self.content = content
        self.execute = execute
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'output_type': self.output_type.value,
            'content': self.content,
            'execute': self.execute
        }
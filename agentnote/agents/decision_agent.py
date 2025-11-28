from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..core.output import Output

class DecisionAgent(BaseAgent):
    """决策智能体"""
    
    def __init__(self, api_key: str, notebook_manager=None): 
        super().__init__(api_key, "decision", notebook_manager) 
        
    def execute_task(self, task_description: str, context: Dict[str, Any]) -> List[Output]:
        """执行决策任务"""
        system_prompt = self._get_prompt('system_prompts', 'decision_agent')
        user_prompt = self._get_retry_prompt(task_description, context)
        
        response = self.generate_response(system_prompt, user_prompt)
        
        outputs = []
        if response:
            # 决策阶段主要生成决策分析和建议
            python_code, markdown_content = self.parser.extract_python_code(response)
            
            if markdown_content:
                outputs.append(self.create_markdown_output(markdown_content))
            
            if python_code:
                # 决策阶段的代码可能需要执行来验证决策
                outputs.append(self.create_code_output(python_code, execute=True))
        
        return outputs
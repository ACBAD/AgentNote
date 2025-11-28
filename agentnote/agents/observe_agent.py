from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..core.output import Output

class ObserveAgent(BaseAgent):
    """观察智能体"""
    
    def __init__(self, api_key: str, notebook_manager=None):  # 修复：添加notebook_manager参数
        super().__init__(api_key, "observe", notebook_manager)  # 修复：传递notebook_manager给基类
        
    def execute_task(self, task_description: str, context: Dict[str, Any]) -> List[Output]:
        """执行观察任务"""
        system_prompt = self._get_prompt('system_prompts', 'observe_agent')
        user_prompt = self._get_retry_prompt(task_description, context)
        
        response = self.generate_response(system_prompt, user_prompt)
        
        outputs = []
        if response:
            # 观察阶段主要生成分析代码
            python_code, markdown_content = self.parser.extract_python_code(response)
            
            if markdown_content:
                outputs.append(self.create_markdown_output(markdown_content))
            
            if python_code:
                # 观察阶段的代码需要执行来获取数据
                outputs.append(self.create_code_output(python_code, execute=True))
        
        return outputs
import time
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from ..core.circle import Circle
from ..core.context import Context
from ..core.notebook_manager import NotebookManager
from ..core.evaluator import PhaseEvaluator, CircleEvaluator 
from ..core.output import Output, OutputType

class CommanderAgent(BaseAgent, PhaseEvaluator, CircleEvaluator):
    """指挥官智能体"""
    
    def __init__(self, api_key: str, notebook_manager=None):  # 修复：添加notebook_manager参数
        super().__init__(api_key, "commander", notebook_manager)  # 修复：传递notebook_manager给基类
        self.current_circle = None
        self.mission_history = []
    
    def execute_mission(self, mission_description: str) -> bool:
        """执行任务"""
        print(f"开始执行任务: {mission_description}")
        
        # 初始化上下文
        context = Context()
        context.set_mission(mission_description)
        
        # 创建新的循环，传入评估器（self）
        self.current_circle = Circle(mission_description, context, self.client, self, self)
        
        # 执行OODA循环
        success = self.current_circle.execute()
        
        # 记录任务历史
        self.mission_history.append({
            'mission': mission_description,
            'success': success,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        return success
    
    # PhaseEvaluator 接口实现 - 修改：增加goal和cell_context参数
    def evaluate_phase_success(self, phase_type: str, context: Dict[str, Any], goal: str, cell_context: str) -> bool:
        """评估阶段是否成功 - 基于goal和cell_context"""

        system_prompt = self._get_prompt('system_prompts', 'phase_evaluator')
        user_prompt = self._get_prompt('evaluation_prompts', 'phase_success',
                                     phase_type=phase_type,
                                     goal=goal,
                                     cell_context=cell_context,
                                     context=str(context))
        
        response = self.generate_response(system_prompt, user_prompt)
        
        # 解析响应，假设响应包含"是"或"成功"等肯定词表示成功
        if response and any(keyword in response.lower() for keyword in ['是', '成功', '完成', '可以', '通过', '达成目标']):
            return True
        return False
    
    # CircleEvaluator 接口实现 - 修改：增加goal和cell_context参数
    def evaluate_circle_success(self, context: Dict[str, Any], goal: str, cell_context: str) -> bool:
        """评估循环是否成功 - 基于goal和cell_context"""

        system_prompt = self._get_prompt('system_prompts', 'circle_evaluator')
        user_prompt = self._get_prompt('evaluation_prompts', 'circle_success',
                                     goal=goal,
                                     cell_context=cell_context,
                                     context=str(context))
        
        response = self.generate_response(system_prompt, user_prompt)
        
        # 解析响应
        if response and any(keyword in response.lower() for keyword in ['是', '成功', '完成', '达成', '目标实现']):
            return True
        return False
    
    def execute_task(self, task_description: str, context: Dict[str, Any]) -> List[Output]:
        """执行指挥官任务"""
        system_prompt = self._get_prompt('system_prompts', 'commander')
        user_prompt = self._get_prompt('task_prompts', 'commander_task',
                                     task_description=task_description,
                                     context=str(context))
        
        response = self.generate_response(system_prompt, user_prompt)
        
        # 解析响应并创建输出
        outputs = []
        if response:
            # 提取代码和文本
            python_code, markdown_content = self.parser.extract_python_code(response)
            
            if markdown_content:
                outputs.append(self.create_markdown_output(markdown_content))
            
            if python_code:
                outputs.append(self.create_code_output(python_code))
        
        return outputs
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        if self.current_circle:
            circle_status = self.current_circle.get_status()
        else:
            circle_status = None
            
        return {
            'current_circle': circle_status,
            'mission_history': self.mission_history,
            'total_missions': len(self.mission_history),
            'successful_missions': len([m for m in self.mission_history if m['success']])
        }
import time
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from ..core.circle import Circle
from ..core.context import Context
from ..core.notebook_manager import NotebookManager
from ..core.evaluator import PhaseEvaluator, CircleEvaluator 
from ..core.output import Output, OutputType
from ..utils.setup_logger import get_logger

logger = get_logger('CommanderAgent', debug=True)

class CommanderAgent(BaseAgent, PhaseEvaluator, CircleEvaluator):
    """指挥官智能体"""
    
    def __init__(self, api_key: str, notebook_manager: Optional[NotebookManager] = None):  # 修复：添加notebook_manager参数
        super().__init__(api_key, "commander", notebook_manager)  # 修复：传递notebook_manager给基类
        self.current_circle = None
        self.mission_history = []
    
    def execute_mission(self, mission_description: str) -> bool:
        """执行任务"""
        logger.info(f"开始执行任务")
        
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
        system_prompt = self._get_prompt('system_prompts', 'phase_evaluator')
        user_prompt = self._get_prompt('evaluation_prompts', 'phase_success',
                                     phase_type=phase_type,
                                     goal=goal,
                                     cell_context=cell_context,
                                     context=str(context))
        
        response = self.generate_response(system_prompt, user_prompt)
        return self._parse_evaluation_result(response)
    
    # CircleEvaluator 接口实现 - 修改：增加goal和cell_context参数
    def evaluate_circle_success(self, context: Dict[str, Any], goal: str, cell_context: str) -> bool:
        """评估循环是否成功 - 基于goal和cell_context"""

        system_prompt = self._get_prompt('system_prompts', 'circle_evaluator')
        user_prompt = self._get_prompt('evaluation_prompts', 'circle_success',
                                     goal=goal,
                                     cell_context=cell_context,
                                     context=str(context))
        
        response = self.generate_response(system_prompt, user_prompt)
        
        return self._parse_evaluation_result(response)
    
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
        
    def _parse_evaluation_result(self, response: str) -> bool:
        """
        解析评估器返回的详细文本。
        逻辑：
        1. 打印完整的分析过程（关键调试信息）。
        2. 重点检查输出的【最后一行】。
        3. 采用“否定优先”策略，防止误判（例如“未成功”不应被判定为“成功”）。
        """
        if not response:
            return False
            
        # 1. 显式打印评估器的思考过程，彻底解决"死得不明不白"的问题
        logger.debug(f"\n{'='*20} 评估器分析报告 {'='*20}")
        logger.debug(response.strip())
        logger.debug(f"{'='*56}\n")
        
        # 2. 提取最后一行有效文本
        lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
        if not lines:
            return False
            
        # 取最后一行并转小写
        last_line = lines[-1].lower()
        
        # 3. 判定逻辑
        
        # A. 否定词优先判定 (只要最后一行包含这些词，直接判否)
        negative_keywords = ['否', '未', '不', '失败', 'no', 'false', 'fail', 'not']
        if any(neg in last_line for neg in negative_keywords):
            return False
            
        # B. 肯定词判定
        positive_keywords = ['是', '成功', '完成', '达成', '通过', 'yes', 'true', 'ok', 'pass']
        if any(pos in last_line for pos in positive_keywords):
            return True
            
        # C. 兜底逻辑：如果最后一行既没说行也没说不行（格式乱了），
        # 尝试倒数第二行（有时候模型最后会加一句废话）
        if len(lines) > 1:
            prev_line = lines[-2].lower()
            if any(pos in prev_line for pos in positive_keywords) and not any(neg in prev_line for neg in negative_keywords):
                return True
                
        return False
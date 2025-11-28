import time
from typing import Dict, Any, List
from .phase import Phase, PhaseType
from .context import Context
from .notebook_manager import NotebookManager
from .evaluator import PhaseEvaluator, CircleEvaluator

class Circle:
    """OODA循环"""
    
    def __init__(self, mission: str, context: Context, deepseek_client, circle_evaluator: CircleEvaluator, phase_evaluator: PhaseEvaluator):
        self.mission = mission
        self.context = context
        self.client = deepseek_client
        self.manager = NotebookManager()
        self.circle_evaluator = circle_evaluator
        self.phase_evaluator = phase_evaluator
        self.phases = []
        self.current_phase_index = 0
        self.completed = False
        self.success = False
        self.retry_count = 0
        
        self.goal = f"通过OODA循环完成任务: {mission}"
        self.cell_context = ""  # 存储该循环的所有cell内容
        
        # 初始化notebook
        self.nb = self.manager.initialize_notebook()
        
        # 添加任务标题
        self.manager.add_markdown_cell(self.nb, f"# OODA循环任务: {mission}\n\n开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def execute(self) -> bool:
        """执行OODA循环"""
        max_circles = 5
        
        for circle_num in range(max_circles):
            print(f"\n=== 开始OODA循环 {circle_num + 1} ===")
            
            # 记录循环开始的cell索引
            start_cell_index = len(self.nb.cells)
            
            circle_context = {
                'circle_number': circle_num + 1,
                'goal': self.goal,
                'start_cell_index': start_cell_index
            }
            self.context.set_circle_context(circle_num + 1, circle_context)
            
            # 执行四个阶段，传入共享的NotebookManager
            phases = [
                Phase(PhaseType.OBSERVE, self.context, self.client, self.phase_evaluator, self.manager),
                Phase(PhaseType.ORIENT, self.context, self.client, self.phase_evaluator, self.manager),
                Phase(PhaseType.DECISION, self.context, self.client, self.phase_evaluator, self.manager),
                Phase(PhaseType.ACTION, self.context, self.client, self.phase_evaluator, self.manager)
            ]
            
            success = True
            for phase in phases:
                phase_success, self.nb = phase.execute(self.nb)  # 接收更新后的notebook
                if not phase_success:
                    success = False
                    break
            
            # 收集该循环的所有cell内容作为上下文
            end_cell_index = len(self.nb.cells)
            self.cell_context = self._collect_cell_context(start_cell_index, end_cell_index)
            
            circle_context.update({
                'completed': True,
                'success': success,
                'end_cell_index': end_cell_index,
                'cell_context': self.cell_context
            })
            self.context.set_circle_context(circle_num + 1, circle_context)
            
            # 评估循环是否成功 - 使用注入的评估器，并传入goal和context
            circle_success = self.circle_evaluator.evaluate_circle_success(
                self.context.get_all(),  # 现在包含完整的上下文信息
                self.goal,
                self.cell_context
            )
            
            if circle_success:
                print(f"✅ OODA循环 {circle_num + 1} 执行成功")
                self.success = True
                self.completed = True
                break  # 这里已经正确跳出循环
            else:
                print(f"🔄 OODA循环 {circle_num + 1} 未完成目标，准备下一循环")
                # 更新上下文，为下一循环做准备
                self.context.update({
                    'previous_circle': circle_num + 1,
                    'circle_feedback': f"第{circle_num + 1}循环未达成目标",
                    'circle_goal': self.goal,
                    'circle_context': self.cell_context
                })
        
        # 添加完成标记
        if self.completed:
            status = "成功" if self.success else "未完成"
            self.manager.add_markdown_cell(self.nb, 
                f"## 任务完成\n\n状态: {status}\n完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            self.manager.add_markdown_cell(self.nb,
                f"## 任务终止\n\n已达到最大循环次数\n终止时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return self.success

    
    def _collect_cell_context(self, start_index: int, end_index: int) -> str:
        """收集指定范围内的cell内容作为上下文"""
        context_parts = []
        for i in range(start_index, min(end_index, len(self.nb.cells))):
            cell = self.nb.cells[i]
            if cell.cell_type == 'markdown':
                context_parts.append(f"Markdown Cell {i}: {cell.source}")
            elif cell.cell_type == 'code':
                context_parts.append(f"Code Cell {i}: {cell.source}")
                # 如果有输出，也包含输出
                if hasattr(cell, 'outputs') and cell.outputs:
                    for output in cell.outputs:
                        if output.output_type == 'stream':
                            context_parts.append(f"Output: {output.text}")
                        elif output.output_type == 'execute_result' and 'text/plain' in output.data:
                            context_parts.append(f"Result: {output.data['text/plain']}")
        
        return "\n".join(context_parts)
    
    def get_status(self) -> Dict[str, Any]:
        """获取循环状态"""
        return {
            'mission': self.mission,
            'goal': self.goal,
            'completed': self.completed,
            'success': self.success,
            'current_phase': self.current_phase_index,
            'total_phases': len(self.phases),
            'retry_count': self.retry_count,
            'cell_context_length': len(self.cell_context) if self.cell_context else 0
        }
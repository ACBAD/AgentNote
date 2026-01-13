import time
from enum import Enum
from typing import Dict, Any, List
from .task import Task, TaskType
from .context import Context
from .output import OutputType
from .evaluator import PhaseEvaluator
from ..agents.observe_agent import ObserveAgent
from ..agents.orient_agent import OrientAgent
from ..agents.decision_agent import DecisionAgent
from ..agents.action_agent import ActionAgent
from ..utils.setup_logger import get_logger

logger = get_logger('Phase')

class PhaseType(Enum):
    OBSERVE = "observe"
    ORIENT = "orient"
    DECISION = "decision"
    ACTION = "action"

class Phase:
    """OODA阶段"""
    
    def __init__(self, phase_type: PhaseType, context: Context, deepseek_client, phase_evaluator: PhaseEvaluator, notebook_manager):
        self.phase_type = phase_type
        self.context = context
        self.client = deepseek_client
        self.phase_evaluator = phase_evaluator
        
        self.goal = self._get_phase_goal(phase_type)
        self.cell_context = ""  # 存储该阶段的所有cell内容
        
        # 关键修复：使用共享的NotebookManager创建智能体
        if phase_type == PhaseType.OBSERVE:
            self.agent = ObserveAgent(deepseek_client.api_key, notebook_manager)
        elif phase_type == PhaseType.ORIENT:
            self.agent = OrientAgent(deepseek_client.api_key, notebook_manager)
        elif phase_type == PhaseType.DECISION:
            self.agent = DecisionAgent(deepseek_client.api_key, notebook_manager)
        elif phase_type == PhaseType.ACTION:
            self.agent = ActionAgent(deepseek_client.api_key, notebook_manager)
        
        self.tasks = []
        self.completed = False
        self.success = False
    
    def _get_phase_goal(self, phase_type: PhaseType) -> str:
        """获取阶段目标"""
        phase_goals = {
            PhaseType.OBSERVE: "收集环境信息和数据，了解当前状况",
            PhaseType.ORIENT: "分析理解收集到的信息，形成对情况的认知",
            PhaseType.DECISION: "基于理解做出决策，制定行动计划",
            PhaseType.ACTION: "执行具体的行动，实现目标"
        }
        return phase_goals.get(phase_type, "完成阶段任务")
    
    def execute(self, notebook):
        """执行阶段 - 修复返回逻辑"""
        logger.info(f"执行 {self.phase_type.value} 阶段")
        
        # 添加阶段标题
        phase_titles = {
            PhaseType.OBSERVE: "🔍 观察阶段",
            PhaseType.ORIENT: "🧠 理解阶段", 
            PhaseType.DECISION: "🎯 决策阶段",
            PhaseType.ACTION: "⚡ 行动阶段"
        }
        
        notebook_manager = self.agent.manager
        # 关键修复：获取添加标题后的更新notebook
        notebook = notebook_manager.add_markdown_cell(notebook, f"## {phase_titles[self.phase_type]}")
        
        # 记录阶段开始的cell索引
        start_cell_index = len(notebook.cells)
        
        # 新增：更新阶段上下文
        phase_context = {
            'phase_type': self.phase_type.value,
            'goal': self.goal,
            'start_cell_index': start_cell_index
        }
        self.context.set_phase_context(self.phase_type.value, phase_context)
        
        max_retries = 3
        for attempt in range(max_retries):
            # 1. 指挥官生成任务
            task_description = self._generate_task_description()
            task = Task(TaskType.COMMANDER_TASK, task_description, self.context, self.phase_evaluator, self.goal)
            task_success, notebook = task.execute(notebook)  # 接收更新后的notebook
            
            if not task_success:
                logger.warning(f"指挥官任务失败，重试 {attempt + 1}/{max_retries}")
                continue
            
            # 关键修改：获取指挥官生成的任务描述，用于后续的智能体任务
            commander_generated_description = self._extract_commander_task_description(task)
            
            # 2. 阶段智能体执行任务
            agent_task = Task(TaskType.AGENT_TASK, commander_generated_description, self.context, self.agent, self.goal)
            agent_success, notebook = agent_task.execute(notebook)  # 接收更新后的notebook
            
            if not agent_success:
                logger.warning(f"智能体任务失败，重试 {attempt + 1}/{max_retries}")
                continue
            
            # 3. 指挥官反思任务
            reflection_task = Task(TaskType.REFLECTION_TASK, commander_generated_description, self.context, self.phase_evaluator, self.goal)
            reflection_success, notebook = reflection_task.execute(notebook)  # 接收更新后的notebook
            
            if not reflection_success:
                logger.warning(f"反思任务失败，重试 {attempt + 1}/{max_retries}")
                continue
            
            # 收集该阶段的所有cell内容作为上下文
            end_cell_index = len(notebook.cells)
            self.cell_context = self._collect_cell_context(notebook, start_cell_index, end_cell_index)
            
            # 新增：更新阶段完成状态到上下文
            phase_context.update({
                'completed': True,
                'success': True,
                'end_cell_index': end_cell_index,
                'cell_context': self.cell_context
            })
            self.context.set_phase_context(self.phase_type.value, phase_context)
            
            # 评估阶段是否成功 - 使用注入的评估器，并传入goal和context
            phase_success = self.phase_evaluator.evaluate_phase_success(
                self.phase_type.value, 
                self.context.get_all(),  # 现在包含完整的上下文信息
                self.goal,
                self.cell_context
            )
            
            if phase_success:
                logger.info(f"✅ {self.phase_type.value} 阶段执行成功")
                self.success = True
                self.completed = True
                return True, notebook
            else:
                logger.warning(f"🔄 {self.phase_type.value} 阶段未完成，重试 {attempt + 1}/{max_retries}")
        
        logger.warning(f"❌ {self.phase_type.value} 阶段执行失败")
        return False, notebook

    def _extract_commander_task_description(self, commander_task):
        """从指挥官任务输出中提取生成的任务描述"""
        # 优先从markdown输出中提取任务描述
        for output in commander_task.outputs:
            if output.output_type == OutputType.MARKDOWN:
                # 提取任务描述的关键部分
                content = output.content
                # 可以添加更复杂的解析逻辑，这里简单返回整个内容
                return content
        
        # 如果没有markdown输出，检查是否有其他输出
        if commander_task.outputs:
            # 如果有其他类型的输出，使用第一个输出的内容
            return commander_task.outputs[0].content
        
        # 如果没有任何输出，回退到原始描述
        return commander_task.description
    
    def _collect_cell_context(self, notebook, start_index: int, end_index: int) -> str:
        """收集指定范围内的cell内容作为上下文"""
        context_parts = [f"阶段目标: {self.goal}"]
        for i in range(start_index, min(end_index, len(notebook.cells))):
            cell = notebook.cells[i]
            if cell.cell_type == 'markdown':
                context_parts.append(f"Markdown Cell {i}: {cell.source}")
            elif cell.cell_type == 'code':
                context_parts.append(f"Code Cell {i}: {cell.source}")
        
        return "\n".join(context_parts)
    
    def _generate_task_description(self) -> str:
        """生成任务描述"""
        phase_descriptions = {
            PhaseType.OBSERVE: "观察环境，收集相关信息",
            PhaseType.ORIENT: "分析理解收集到的信息", 
            PhaseType.DECISION: "基于理解做出决策",
            PhaseType.ACTION: "执行具体的行动"
        }
        
        mission = self.context.get('mission', '未知任务')
        return f"任务: {mission}\n阶段: {self.phase_type.value}\n要求: {phase_descriptions[self.phase_type]}\n目标: {self.goal}"
    
    def get_status(self) -> Dict[str, Any]:
        """获取阶段状态"""
        return {
            'phase_type': self.phase_type.value,
            'goal': self.goal,
            'completed': self.completed,
            'success': self.success,
            'tasks_completed': len([t for t in self.tasks if t.completed]),
            'cell_context_length': len(self.cell_context) if self.cell_context else 0
        }
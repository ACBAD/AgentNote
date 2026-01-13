from enum import Enum
from typing import Dict, Any, List
from .output import Output
from .context import Context
from .output import Output, OutputType
from ..agents.base_agent import BaseAgent
from ..core.evaluator import PhaseEvaluator
from ..core.output import Output, OutputType
from ..utils.setup_logger import get_logger

logger = get_logger('Task')

class TaskType(Enum):
    COMMANDER_TASK = "commander_task"
    AGENT_TASK = "agent_task" 
    REFLECTION_TASK = "reflection_task"

class Task:
    """任务"""
    
    def __init__(self, task_type: TaskType, description: str, context: Context, agent: BaseAgent, goal: str = ""):
        self.task_type = task_type
        self.description = description
        self.context = context
        self.agent = agent
        self.outputs = []
        self.completed = False
        self.success = False
        self.error_count = 0
        
        # 新增：任务的目标和上下文
        self.goal = goal or self._generate_task_goal(task_type, description)
        self.cell_context = ""  # 存储该任务的所有cell内容
        
        # 新增：获取任务名称和智能体名称
        self.task_name = task_type.value
        if hasattr(agent, 'agent_type'):
            self.agent_name = agent.agent_type
        else:
            self.agent_name = "unknown"
        
        # 新增：存储执行历史，用于重试时提供更多上下文
        self.execution_history = []
    
    def _generate_task_goal(self, task_type: TaskType, description: str) -> str:
        """生成任务目标"""
        task_goals = {
            TaskType.COMMANDER_TASK: "为当前阶段生成明确的任务指令",
            TaskType.AGENT_TASK: "执行具体的智能体任务",
            TaskType.REFLECTION_TASK: "评估当前阶段执行情况"
        }
        return task_goals.get(task_type, f"完成{task_type.value}任务")
    
    def _collect_cell_context(self, notebook, start_index: int, end_index: int) -> str:
        """收集指定范围内的cell内容作为上下文"""
        context_parts = [f"任务目标: {self.goal}"]
        for i in range(start_index, min(end_index, len(notebook.cells))):
            cell = notebook.cells[i]
            if cell.cell_type == 'markdown':
                context_parts.append(f"Markdown: {cell.source}")
            elif cell.cell_type == 'code':
                context_parts.append(f"Code: {cell.source}")
        
        return "\n".join(context_parts)
    
    def _extract_error_details(self, notebook, cell_index: int) -> str:
        """从指定的cell中提取错误详情"""
        if cell_index < 0 or cell_index >= len(notebook.cells):
            return ""
        
        cell = notebook.cells[cell_index]
        if cell.cell_type != 'code' or not hasattr(cell, 'outputs') or not cell.outputs:
            return ""
        
        error_details = []
        for output in cell.outputs:
            if output.output_type == 'error':
                error_msg = f"{output.ename}: {output.evalue}"
                if hasattr(output, 'traceback') and output.traceback:
                    error_msg += f"\n追踪: {' | '.join(output.traceback)}"
                error_details.append(error_msg)
        
        return "\n".join(error_details)
    
    def _build_retry_context(self, attempt: int, error_type: str, error_details: str, previous_outputs: List[Output]) -> Dict[str, Any]:
        """构建重试时的上下文信息"""
        retry_context = {
            'retry_attempt': attempt + 1,
            'previous_errors': self.execution_history.copy(),
            'last_error_type': error_type,
            'last_error_details': error_details,
            'total_errors': len(self.execution_history) + 1
        }
        
        # 如果有之前的输出，也包含在上下文中
        if previous_outputs:
            retry_context['previous_outputs_count'] = len(previous_outputs)
            # 提取之前生成的代码（如果有）
            previous_codes = [output.content for output in previous_outputs if output.output_type == OutputType.CODE]
            if previous_codes:
                retry_context['previous_generated_code'] = previous_codes[-1]  # 只取最后一个代码
        
        return retry_context
    
    def execute(self, notebook):
        """执行任务 - 修复返回逻辑"""
        logger.info(f"执行 {self.task_type.value}: {self.description}")
        
        # 记录任务开始的cell索引
        start_cell_index = len(notebook.cells)
        
        # 新增：在首个Cell中添加三级标题
        title = f"### {self.task_name}-{self.agent_name}"
        notebook_manager = self.agent.manager
        notebook = notebook_manager.add_markdown_cell(notebook, title)
        
        # 更新任务上下文
        task_context = {
            'task_type': self.task_type.value,
            'description': self.description,
            'goal': self.goal,
            'agent_name': self.agent_name,
            'start_cell_index': start_cell_index
        }
        self.context.set_task_context(f"{self.task_type.value}_{self.agent_name}", task_context)
        
        # 如果 agent 是 PhaseEvaluator（而不是 BaseAgent 子类），需要特殊处理
        if hasattr(self.agent, 'evaluate_phase_success') and not hasattr(self.agent, 'execute_task'):
            # 这是评估器，不是真正的智能体，跳过执行
            self.success = True
            self.completed = True
            return True, notebook  # 返回成功状态和notebook
        
        max_retries = 2
        previous_outputs = []  # 存储之前尝试的输出
        
        for attempt in range(max_retries):
            try:
                # 构建重试上下文（如果是重试的话）
                if attempt > 0:
                    retry_context = self._build_retry_context(
                        attempt - 1, 
                        "execution_error", 
                        self.execution_history[-1] if self.execution_history else "未知错误",
                        previous_outputs
                    )
                    self.context.update(retry_context)
                    logger.warning(f"🔄 第 {attempt + 1} 次重试，使用错误上下文: {retry_context}")
                
                # 执行任务（只有真正的智能体才有 execute_task 方法）
                outputs = self.agent.execute_task(self.description, self.context.get_all())
                
                # 保存输出用于可能的后续重试
                if attempt == 0:
                    previous_outputs = outputs.copy()
                
                # 处理输出
                current_cell_index = len(notebook.cells)
                for output in outputs:
                    notebook = self.agent.add_output_to_notebook(output, notebook)
                    self.outputs.append(output)
                    
                    # 新增：将输出内容添加到上下文
                    if output.output_type == OutputType.MARKDOWN:
                        self.context.add_cell_content('markdown', output.content, current_cell_index)
                    elif output.output_type == OutputType.CODE:
                        self.context.add_cell_content('code', output.content, current_cell_index)
                    
                    current_cell_index += 1
                
                # 检查是否有代码执行错误
                has_execution_error = False
                execution_error_details = ""
                
                for output in outputs:
                    if output.output_type == OutputType.CODE and output.execute:
                        # 检查最后一个cell是否有错误
                        last_cell = notebook.cells[-1] if notebook.cells else None
                        if last_cell and last_cell.cell_type == 'code':
                            if hasattr(last_cell, 'outputs') and last_cell.outputs:
                                for cell_output in last_cell.outputs:
                                    if cell_output.output_type == 'error':
                                        has_execution_error = True
                                        # 提取错误详情
                                        execution_error_details = self._extract_error_details(notebook, len(notebook.cells)-1)
                                        # 新增：将错误信息添加到上下文
                                        self.context.add_error(
                                            'code_execution_error',
                                            execution_error_details,
                                            {
                                                'task_type': self.task_type.value,
                                                'description': self.description,
                                                'attempt': attempt + 1
                                            }
                                        )
                                        break
                
                if has_execution_error:
                    # 记录执行错误
                    error_msg = f"代码执行错误 (尝试 {attempt + 1}): {execution_error_details}"
                    self.execution_history.append(error_msg)
                    logger.warning(error_msg)
                    
                    if attempt < max_retries - 1:
                        logger.warning(f"🔄 准备重试 ({attempt + 1}/{max_retries})")
                        self.error_count += 1
                        continue
                    else:
                        # 最后一次尝试也失败了
                        logger.error(f"❌ 达到最大重试次数，任务失败")
                        self.success = False
                        self.completed = True
                        return False, notebook
                
                # 收集该任务的所有cell内容作为上下文
                end_cell_index = len(notebook.cells)
                self.cell_context = self._collect_cell_context(notebook, start_cell_index, end_cell_index)
                
                # 新增：更新任务完成状态到上下文
                task_context.update({
                    'completed': True,
                    'success': True,
                    'end_cell_index': end_cell_index,
                    'cell_context': self.cell_context
                })
                self.context.set_task_context(f"{self.task_type.value}_{self.agent_name}", task_context)
                
                self.success = True
                self.completed = True
                logger.info(f"✅ 任务执行成功 (尝试 {attempt + 1})")
                return True, notebook
                
            except Exception as e:
                # 记录异常错误
                error_msg = f"任务执行异常 (尝试 {attempt + 1}): {str(e)}"
                self.execution_history.append(error_msg)
                # 新增：将异常错误添加到上下文
                self.context.add_error(
                    'task_execution_exception',
                    str(e),
                    {
                        'task_type': self.task_type.value,
                        'description': self.description,
                        'attempt': attempt + 1
                    }
                )
                logger.warning(error_msg)
                
                self.error_count += 1
                
                if attempt < max_retries - 1:
                    logger.warning(f"🔄 准备重试 ({attempt + 1}/{max_retries})")
                    continue
                else:
                    logger.error(f"❌ 达到最大重试次数，任务失败")
                    self.success = False
                    self.completed = True
                    return False, notebook
        
        # 不应该执行到这里，但为了安全起见
        self.success = False
        self.completed = True
        return False, notebook
    
    def get_status(self) -> Dict[str, Any]:
        """获取任务状态"""
        return {
            'task_type': self.task_type.value,
            'description': self.description,
            'goal': self.goal,
            'completed': self.completed,
            'success': self.success,
            'error_count': self.error_count,
            'execution_history': self.execution_history.copy(),
            'outputs_count': len(self.outputs),
            'cell_context_length': len(self.cell_context) if self.cell_context else 0
        }
    
    def get_commander_generated_description(self) -> str:
        """获取指挥官生成的任务描述"""
        # 优先从markdown输出中提取
        for output in self.outputs:
            if output.output_type == OutputType.MARKDOWN:
                return output.content
        
        # 如果没有合适的输出，返回原始描述
        return self.description
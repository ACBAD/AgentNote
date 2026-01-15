import os
import yaml
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..core.deepseek_client import DeepSeekClient
from ..core.content_parser import ContentParser
from ..core.notebook_manager import NotebookManager
from ..core.output import Output, OutputType
from ..core.config import config

class BaseAgent(ABC):
    """基础智能体类"""
    
    def __init__(self, api_key: str, agent_type: str, notebook_manager: Optional[NotebookManager] = None):
        self.agent_type = agent_type
        self.client = DeepSeekClient(api_key, enable_thinking=config.deepseek.think_mode)
        self.parser = ContentParser()
        self.manager = notebook_manager if notebook_manager else NotebookManager()
        self.prompts = self._load_prompts()
        
    def _load_prompts(self) -> Dict[str, Any]:
        """加载提示词模板"""
        prompts_path = os.path.join(os.path.dirname(__file__), '../prompts/prompts.yaml')
        with open(prompts_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _get_prompt(self, category: str, key: str, **kwargs) -> str:
        """获取格式化后的提示词"""
        if category in self.prompts and key in self.prompts[category]:
            template = self.prompts[category][key]
            return template.format(**kwargs)
        return ""
    
    def _get_retry_prompt(self, task_description: str, context: Dict[str, Any]) -> str:
        """获取重试时的提示词，包含错误上下文"""
        error_history = context.get('previous_errors', [])
        previous_code = context.get('previous_generated_code', '')
        retry_attempt = context.get('retry_attempt', 1)
        
        # 新增：获取cell上下文和错误上下文
        cell_context = context.get('cell_context', '暂无上下文')
        recent_errors = context.get('error_context', [])
        
        # 如果有错误历史，使用专门的错误恢复提示词
        if error_history:
            return self._get_prompt('error_recovery_prompts', 'task_retry_with_context',
                                task_description=task_description,
                                context=str(context),
                                cell_context=cell_context,
                                error_history="\n".join([f"- {error}" for error in error_history]),
                                recent_errors="\n".join([f"- {error.get('message', '未知错误')}" for error in recent_errors[-3:]]),
                                previous_code=previous_code if previous_code else "无")
        
        # 否则使用普通提示词，但包含完整的上下文信息
        return self._get_prompt('task_prompts', f'{self.agent_type}_task',
                            task_description=task_description,
                            context=str(context),
                            cell_context=cell_context)
    
    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """生成响应"""
        return self.client.generate_with_retry(system_prompt, user_prompt)
    
    def create_markdown_output(self, content: str) -> Output:
        """创建Markdown输出"""
        return Output(OutputType.MARKDOWN, content)
    
    def create_code_output(self, code: str, execute: bool = True) -> Output:
        """创建代码输出"""
        return Output(OutputType.CODE, code, execute)
    
    def create_execution_output(self, result: str) -> Output:
        """创建执行结果输出"""
        return Output(OutputType.EXECUTION_RESULT, result)
    
    def add_output_to_notebook(self, output: Output, notebook):
        """添加输出到notebook - 修复返回逻辑"""
        if output.output_type == OutputType.MARKDOWN:
            notebook = self.manager.add_markdown_cell(notebook, output.content)
        elif output.output_type == OutputType.CODE:
            notebook = self.manager.add_code_cell(notebook, output.content)
            if output.execute:
                # 执行代码并获取结果
                execution_result = self.manager.execute_cell_safely(
                    self.manager.executor, output.content, len(notebook.cells)-1
                )
                # 重新加载notebook以确保输出被正确保存
                notebook = self.manager.load_notebook()
        elif output.output_type == OutputType.EXECUTION_RESULT:
            notebook = self.manager.add_markdown_cell(notebook, f"**执行结果**:\n```\n{output.content}\n```")
        
        # 确保最终保存notebook
        self.manager.save_notebook(notebook)
        return notebook  # 返回更新后的notebook
    
    @abstractmethod
    def execute_task(self, task_description: str, context: Dict[str, Any]) -> List[Output]:
        """执行任务 - 子类必须实现"""
        pass
import os
import time
import nbformat as nbf
from typing import Dict, Any
from .config import config
from .notebook_exporter import NotebookExporter
from .executor import NotebookExecutor

class NotebookManager:
    """Notebook管理器"""

    def __init__(self, notebook_path: str = None):
        if notebook_path:
            self.notebook_path = notebook_path
        else:
            # 根据配置决定是否添加时间戳
            if config.notebook.add_timestamp:
                base_name = config.notebook.notebook_name
                name, ext = os.path.splitext(base_name)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                self.notebook_path = f"environment/{name}_{timestamp}{ext}"
            else:
                self.notebook_path = f"environment/{config.notebook.notebook_name}"
                
        self._notebook_initialized = False
        self.executor = NotebookExecutor(self)
    
    def initialize_notebook(self):
        """初始化notebook"""
        if self._notebook_initialized:
            return self.load_notebook()
            
        # 确保environment目录存在
        os.makedirs("environment", exist_ok=True)
        
        # 如果文件不存在，创建新的notebook
        if not os.path.exists(self.notebook_path):
            nb = nbf.v4.new_notebook()
            # 添加初始标记
            initial_markdown = f"# OODA循环生成的 Notebook\n\n创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n"
            self.add_markdown_cell(nb, initial_markdown)
            print(f"创建新的Notebook: {self.notebook_path}")
        else:
            # 加载现有notebook
            nb = self.load_notebook()
            print(f"加载现有Notebook: {self.notebook_path}")
        
        self._notebook_initialized = True
        return nb
    
    def load_notebook(self):
        """加载现有的notebook"""
        if not os.path.exists(self.notebook_path):
            # 如果文件不存在，创建一个新的
            nb = nbf.v4.new_notebook()
            self.save_notebook(nb)
            return nb
        
        with open(self.notebook_path, 'r', encoding='utf-8') as f:
            return nbf.read(f, as_version=4)
    
    def save_notebook(self, nb):
        """保存notebook"""
        with open(self.notebook_path, 'w', encoding='utf-8') as f:
            nbf.write(nb, f)
            f.flush()
            os.fsync(f.fileno())
    

    def add_markdown_cell(self, nb, markdown_text: str):
        """添加markdown cell"""
        cell = nbf.v4.new_markdown_cell(source=markdown_text)
        if hasattr(config.notebook, 'markdown_cell_tag'):
            cell.metadata["tags"] = [config.notebook.markdown_cell_tag]
        nb.cells.append(cell)
        # 关键修复：确保添加cell后立即保存，并返回正确的notebook对象
        self.save_notebook(nb)
        return nb  # 返回notebook，而不是cell

    def add_code_cell(self, nb, code_text: str):
        """添加代码cell"""
        cell = nbf.v4.new_code_cell(source=code_text)
        if hasattr(config.notebook, 'code_cell_tag'):
            cell.metadata["tags"] = [config.notebook.code_cell_tag]
        nb.cells.append(cell)
        # 关键修复：确保添加cell后立即保存，并返回正确的notebook对象
        self.save_notebook(nb)
        return nb  # 返回notebook，而不是cell
    
    def get_cell_count(self, nb):
        """获取cell数量"""
        return len(nb.cells)
    
    def cleanup_old_cells(self, nb):
        """清理旧的cell以保持数量限制"""
        if len(nb.cells) <= config.notebook.max_cells:
            return nb
        
        # 只保留最近的cell
        nb.cells = nb.cells[-config.notebook.max_cells:]
        self.save_notebook(nb)
        print(f"已清理cell，当前数量: {len(nb.cells)}")
        return nb
    
    def execute_cell_safely(self, executor, code: str, cell_index: int) -> Dict[str, Any]:
        """安全执行单个cell代码"""
        result = executor.execute_single_cell(code, cell_index)
        
        # 关键修复：执行后强制重新加载notebook以获取最新输出，然后保存
        time.sleep(0.5)  # 添加短暂延迟确保文件写入完成
        nb = self.load_notebook()
        self.save_notebook(nb)
        
        return result
    
    def get_notebook_context(self, nb) -> str:
        """获取notebook的上下文内容"""
        if not nb.cells:
            return "Notebook目前为空"
        
        # 从配置中获取参数
        max_cells = config.notebook.context_max_cells
        include_code = config.notebook.include_code_in_context
        include_markdown = config.notebook.include_markdown_in_context
        include_outputs = config.notebook.include_outputs_in_context
        
        context = "## 已生成的Notebook内容:\n\n"
        
        # 获取最近的cell，基于配置的数量限制
        recent_cells = nb.cells[-max_cells:] if len(nb.cells) > max_cells else nb.cells
        
        for i, cell in enumerate(recent_cells, start=len(nb.cells)-len(recent_cells)+1):
            if cell.cell_type == 'markdown' and include_markdown:
                context += f"### Markdown Cell {i}:\n{cell.source}\n\n"
            elif cell.cell_type == 'code' and include_code:
                context += f"### Code Cell {i}:\n```python\n{cell.source}\n```\n"
                
                # 如果有执行结果且配置为包含输出，也包含进来
                if include_outputs and hasattr(cell, 'outputs') and cell.outputs:
                    context += "#### 执行结果:\n"
                    for output in cell.outputs:
                        if output.output_type == 'stream':
                            context += f"输出: {output.text}\n"
                        elif output.output_type == 'execute_result' and 'text/plain' in output.data:
                            context += f"结果: {output.data['text/plain']}\n"
                        elif output.output_type == 'error':
                            # 特别包含错误信息
                            context += f"❌ 执行错误: {output.ename}: {output.evalue}\n"
                            if hasattr(output, 'traceback') and output.traceback:
                                context += f"错误追踪: {' | '.join(output.traceback)}\n"
                    context += "\n"
        
        return context
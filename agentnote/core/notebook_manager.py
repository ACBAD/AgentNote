import os
import time
import nbformat as nbf
from typing import Dict, Any
from .config import config
from .notebook_generator import NotebookGenerator
from .notebook_exporter import NotebookExporter

class NotebookManager:
    """Notebook管理器"""

    def __init__(self):
        # 根据配置决定是否添加时间戳
        if config.notebook.add_timestamp:
            base_name = config.notebook.notebook_name
            name, ext = os.path.splitext(base_name)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.notebook_path = f"{name}_{timestamp}{ext}"
        else:
            self.notebook_path = config.notebook.notebook_name
            
        self._notebook_initialized = False  # 标记是否已初始化
    
    def initialize_notebook(self):
        """初始化notebook - 只在程序启动时调用一次"""
        if self._notebook_initialized:
            return self.load_notebook()
            
        # 如果文件不存在，创建新的notebook
        if not os.path.exists(self.notebook_path):
            nb = NotebookGenerator.create_notebook()
            # 添加初始标记
            initial_markdown = f"# AgentNote 生成的 Notebook\n\n创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n"
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
            nb = NotebookGenerator.create_notebook()
            self.save_notebook(nb)
            return nb
        
        try:
            with open(self.notebook_path, 'r', encoding='utf-8') as f:
                return nbf.read(f, as_version=4)
        except Exception as e:
            print(f"加载notebook失败: {e}，创建新的notebook")
            nb = NotebookGenerator.create_notebook()
            self.save_notebook(nb)
            return nb
    
    def save_notebook(self, nb):
        """保存notebook"""
        try:
            with open(self.notebook_path, 'w', encoding='utf-8') as f:
                nbf.write(nb, f)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            print(f"保存notebook失败: {e}")
    
    def add_markdown_cell(self, nb, markdown_text: str):
        """添加markdown cell"""
        cell = NotebookGenerator.create_markdown_cell(
            markdown_text, 
            tags=[config.notebook.markdown_cell_tag]
        )
        nb.cells.append(cell)
        self.save_notebook(nb)
        return cell
    
    def add_code_cell(self, nb, code_text: str):
        """添加代码cell"""
        cell = NotebookGenerator.create_code_cell(
            code_text, 
            tags=[config.notebook.code_cell_tag]
        )
        nb.cells.append(cell)
        self.save_notebook(nb)
        return cell
    
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
    
    def get_last_cell_output(self, nb):
        """获取最后一个cell的输出"""
        if not nb.cells:
            return None
        
        last_cell = nb.cells[-1]
        if last_cell.cell_type != 'code':
            return None
        
        cell_data = NotebookExporter.extract_cell_data(last_cell, len(nb.cells)-1)
        return cell_data
    
    def execute_cell_safely(self, executor, code: str, cell_index: int) -> Dict[str, Any]:
        """安全执行单个cell代码"""
        return executor.execute_single_cell(code, cell_index)
    
    def add_error_cell(self, nb, code: str, error_info: str):
        """添加包含错误信息的代码cell"""
        # 添加代码cell
        cell = self.add_code_cell(nb, code)
        
        # 手动添加错误输出到cell
        try:
            # 创建错误输出
            error_output = nbf.v4.new_output(
                output_type="error",
                ename="ExecutionError",
                evalue=error_info,
                traceback=[error_info]
            )
            cell.outputs.append(error_output)
            
            # 保存notebook
            self.save_notebook(nb)
        except Exception as e:
            print(f"添加错误输出失败: {e}")
        
        return cell
    
    def get_notebook_context(self, nb) -> str:
        """获取notebook的上下文内容（包括所有执行过的代码，无论对错）"""
        if not nb.cells:
            return "Notebook目前为空"
        
        # 从配置中获取参数
        max_cells = config.notebook.context_max_cells
        include_code = config.notebook.include_code_in_context
        include_markdown = config.notebook.include_markdown_in_context
        include_outputs = config.notebook.include_outputs_in_context
        
        context = "## 已生成的Notebook内容（包括执行成功和失败的代码）:\n\n"
        
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
        
        print("********************Notebook Context******************************")
        print(context)
        print("*******************************************************************")
        return context
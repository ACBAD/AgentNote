import subprocess
import os
from typing import Dict, Any, Optional
from .config import config

class NotebookExecutor:
    """Notebook执行器 - 直接执行整个notebook保持上下文一致性"""
    
    def __init__(self, notebook_manager):
        self.manager = notebook_manager
        self.timeout = 600  # 10分钟超时
    
    def execute_single_cell(self, code: str, cell_index: int, timeout: int = None) -> Dict[str, Any]:
        """执行单个cell - 通过执行整个notebook来保持上下文"""
        timeout = timeout or self.timeout
        notebook_path = self.manager.notebook_path
        
        # 确保notebook存在
        if not os.path.exists(notebook_path):
            return {
                'success': False,
                'error': f'Notebook文件不存在: {notebook_path}',
                'output': '',
                'stdout': '',
                'stderr': f'文件 {notebook_path} 不存在',
                'execution_count': None
            }
        
        # 执行整个notebook
        result = self._execute_entire_notebook(notebook_path, timeout)
        
        if result and result.get('success'):
            # 重新加载notebook获取最新状态
            nb = self.manager.load_notebook()
            
            # 找到对应的cell（应该是最后一个代码cell）
            code_cells = [i for i, cell in enumerate(nb.cells) if cell.cell_type == 'code']
            if not code_cells:
                return {
                    'success': False,
                    'error': 'Notebook中没有代码cell',
                    'output': '',
                    'stdout': '',
                    'stderr': '',
                    'execution_count': None
                }
            
            # 获取最后一个代码cell
            last_code_cell_index = code_cells[-1]
            last_code_cell = nb.cells[last_code_cell_index]
            
            # 检查cell是否有错误输出
            has_error = False
            error_details = ""
            if hasattr(last_code_cell, 'outputs') and last_code_cell.outputs:
                for output in last_code_cell.outputs:
                    if output.output_type == 'error':
                        has_error = True
                        error_details = f"{output.ename}: {output.evalue}"
                        if hasattr(output, 'traceback') and output.traceback:
                            error_details += f"\n追踪: {' | '.join(output.traceback)}"
                        break
            
            # 构建执行结果 - 根据是否有错误判断成功与否
            execution_result = {
                'success': not has_error,
                'error': error_details if has_error else None,
                'output': self._extract_cell_output(last_code_cell),
                'stdout': result.get('stdout', ''),
                'stderr': result.get('stderr', ''),
                'execution_count': last_code_cell.get('execution_count', len(code_cells))
            }
            return execution_result
        else:
            # 执行失败
            return {
                'success': False,
                'error': result.get('error', '执行失败') if result else '执行失败',
                'output': '',
                'stdout': result.get('stdout', '') if result else '',
                'stderr': result.get('stderr', '') if result else '',
                'execution_count': None
            }
    
    def _execute_entire_notebook(self, notebook_path: str, timeout: int = None) -> Dict[str, Any]:
        """执行整个notebook文件"""
        timeout = timeout or self.timeout
        
        # 使用jupyter命令行工具执行整个notebook，允许错误继续执行
        cmd = ['jupyter', 'nbconvert', '--execute', '--inplace', '--allow-errors', '--to', 'notebook', notebook_path]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8'
            )
            
            time.sleep(1)
            
            # 强制重新加载notebook以确保输出被正确保存
            nb = self.manager.load_notebook()
            self.manager.save_notebook(nb)
            
            # 注意：即使有cell执行错误，nbconvert --allow-errors 也可能返回0
            return {
                'success': result.returncode == 0,
                'error': result.stderr if result.returncode != 0 else None,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"执行notebook时发生异常: {str(e)}",
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def _extract_cell_output(self, cell) -> str:
        """从cell中提取输出内容"""
        if not hasattr(cell, 'outputs') or not cell.outputs:
            return ""
        
        output_text = []
        for output in cell.outputs:
            if output.output_type == "stream":
                output_text.append(output.text)
            elif output.output_type == "execute_result" and 'text/plain' in output.data:
                output_text.append(str(output.data['text/plain']))
            elif output.output_type == "error":
                # 特别处理错误输出
                error_msg = f"{output.ename}: {output.evalue}"
                if hasattr(output, 'traceback') and output.traceback:
                    error_msg += f"\n追踪: {' | '.join(output.traceback)}"
                output_text.append(error_msg)
        
        return "\n".join(output_text)
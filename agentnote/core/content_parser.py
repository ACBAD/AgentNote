import re
import ast
from typing import Tuple, Optional

class ContentParser:
    """内容解析器 - 专门处理Python代码和Markdown的分离"""
    
    @staticmethod
    def extract_python_code(content: str) -> Tuple[Optional[str], str]:
        """
        从内容中提取Python代码
        
        Args:
            content: DeepSeek返回的内容字符串
            
        Returns:
            tuple: (python_code, markdown_content)
                   python_code: 提取的Python代码，如果没有则为None
                   markdown_content: 去除Python代码后的Markdown内容
        """
        if not content:
            return None, ""
        
        # 定义Python代码块的正则表达式模式
        code_block_pattern = r'```(?:python)?\s*(.*?)\s*```'
        
        # 查找所有代码块
        code_blocks = re.findall(code_block_pattern, content, re.DOTALL)
        
        # 提取Python代码（只取第一个Python代码块）
        python_code = None
        if code_blocks:
            python_code = code_blocks[0].strip()
        
        # 从原始内容中移除代码块，得到Markdown内容
        markdown_content = re.sub(code_block_pattern, '', content, flags=re.DOTALL).strip()
        
        # 清理Markdown内容中的多余空行
        markdown_content = re.sub(r'\n\s*\n', '\n\n', markdown_content)
        
        return python_code, markdown_content
    
    @staticmethod
    def validate_python_code(code: str) -> Tuple[bool, str]:
        """验证Python代码的语法"""
        if not code:
            return False, "代码为空"
        
        try:
            # 尝试编译代码来检查语法
            compile(code, '<string>', 'exec')
            return True, "代码语法正确"
        except SyntaxError as e:
            return False, f"语法错误: {e}"
        except Exception as e:
            return False, f"代码验证错误: {e}"
    
    @staticmethod
    def extract_imports(code: str) -> list:
        """提取代码中的导入语句"""
        if not code:
            return []
        
        try:
            tree = ast.parse(code)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(ast.unparse(node))
            
            return imports
        except:
            return []
    
    @staticmethod
    def contains_execution_errors(output_data: dict) -> bool:
        """检查输出数据中是否包含执行错误"""
        if not output_data.get("outputs"):
            return False
        
        for output in output_data["outputs"]:
            if output.get("output_type") == "error":
                return True
        
        return False
    
    @staticmethod
    def get_error_message(output_data: dict) -> str:
        """从输出数据中提取错误信息"""
        if not output_data.get("outputs"):
            return ""
        
        for output in output_data["outputs"]:
            if output.get("output_type") == "error":
                return f"{output.get('ename', '')}: {output.get('evalue', '')}"
        
        return ""
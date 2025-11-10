import nbformat as nbf
from .config import config

class NotebookGenerator:
    """Notebook生成器"""
    
    @staticmethod
    def create_code_cell(source_code: str, tags=None, metadata=None):
        """创建代码cell"""
        cell = nbf.v4.new_code_cell(source=source_code)
        if tags:
            cell.metadata["tags"] = tags
        if metadata:
            cell.metadata.update(metadata)
        return cell
    
    @staticmethod
    def create_markdown_cell(markdown_text: str, tags=None, metadata=None):
        """创建markdown cell"""
        cell = nbf.v4.new_markdown_cell(source=markdown_text)
        if tags:
            cell.metadata["tags"] = tags
        if metadata:
            cell.metadata.update(metadata)
        return cell
    
    @staticmethod
    def create_notebook():
        """创建新的notebook"""
        return nbf.v4.new_notebook()
    
    @staticmethod
    def add_cell_to_notebook(nb, cell):
        """添加cell到notebook"""
        nb.cells.append(cell)
        return nb
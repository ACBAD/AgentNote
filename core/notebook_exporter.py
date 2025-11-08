import json
import os
from datetime import datetime
import nbformat as nbf
from .config import config

class NotebookExporter:
    """Notebook导出器"""
    
    @staticmethod
    def extract_cell_data(cell, cell_index: int):
        """提取cell的数据"""
        cell_data = {
            "index": cell_index,
            "cell_type": cell.cell_type,
            "source": cell.source,
            "execution_count": cell.get('execution_count', None),
            "metadata": dict(cell.metadata) if hasattr(cell, 'metadata') else {}
        }
        
        # 添加输出信息
        if hasattr(cell, 'outputs') and cell.outputs:
            cell_data["outputs"] = []
            for output in cell.outputs:
                output_data = {
                    "output_type": output.output_type
                }
                
                if output.output_type == "execute_result":
                    output_data["data"] = {
                        k: str(v)[:500] + "..." if len(str(v)) > 500 else str(v) 
                        for k, v in output.data.items()
                    } if hasattr(output, 'data') else {}
                    output_data["execution_count"] = output.get('execution_count', None)
                
                elif output.output_type == "stream":
                    output_data["text"] = output.text[:1000] + "..." if len(output.text) > 1000 else output.text
                
                elif output.output_type == "error":
                    output_data["ename"] = output.ename
                    output_data["evalue"] = output.evalue
                    output_data["traceback"] = output.traceback
                
                elif output.output_type == "display_data":
                    output_data["data"] = {
                        k: "[binary data]" if k.startswith('image/') else str(v)[:500] + "..." if len(str(v)) > 500 else str(v)
                        for k, v in output.data.items()
                    } if hasattr(output, 'data') else {}
                
                cell_data["outputs"].append(output_data)
        
        return cell_data
    
    @staticmethod
    def export_notebook_to_json(notebook_path: str, output_file: str = None):
        """导出notebook的所有cell输入输出到JSON"""
        if not os.path.exists(notebook_path):
            print(f"Notebook文件不存在: {notebook_path}")
            return None
        
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                nb = nbf.read(f, as_version=4)
            
            notebook_data = {
                "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "notebook_path": notebook_path,
                "cells": []
            }
            
            for i, cell in enumerate(nb.cells):
                cell_data = NotebookExporter.extract_cell_data(cell, i)
                notebook_data["cells"].append(cell_data)
            
            # 如果指定了输出文件，则保存到文件
            output_file = output_file or config.notebook.json_output_file
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(notebook_data, f, indent=2, ensure_ascii=False)
                print(f"Notebook cell数据已导出到: {output_file}")
            
            return notebook_data
            
        except Exception as e:
            print(f"导出notebook到JSON时出错: {e}")
            return None
    
    @staticmethod
    def save_notebook(nb, notebook_path: str = None):
        """保存notebook到文件"""
        notebook_path = notebook_path or config.notebook.notebook_name
        with open(notebook_path, 'w', encoding='utf-8') as f:
            nbf.write(nb, f)
            f.flush()
            os.fsync(f.fileno())
        print(f"Notebook已保存: {notebook_path}")
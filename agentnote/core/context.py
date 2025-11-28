from typing import Dict, Any, Optional, List

class Context:
    """上下文管理器"""
    
    def __init__(self):
        self._data = {}
        self._phase_context = {}
        self._circle_context = {}
        self._task_context = {}
        self._cell_context = []  
        self._error_context = []  
    
    def set_mission(self, mission: str):
        """设置任务"""
        self._data['mission'] = mission
    
    def update(self, new_data: Dict[str, Any]):
        """更新上下文"""
        self._data.update(new_data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文值"""
        return self._data.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有上下文"""
        # 返回完整的上下文信息，包括cell内容
        context_copy = self._data.copy()
        context_copy['cell_context'] = self.get_cell_context_summary()
        context_copy['error_context'] = self._error_context.copy()
        return context_copy
    
    def set_phase_context(self, phase: str, context: Dict[str, Any]):
        """设置阶段上下文"""
        self._phase_context[phase] = context
    
    def get_phase_context(self, phase: str) -> Dict[str, Any]:
        """获取阶段上下文"""
        return self._phase_context.get(phase, {})
    
    def set_circle_context(self, circle: int, context: Dict[str, Any]):
        """设置循环上下文"""
        self._circle_context[circle] = context
    
    def get_circle_context(self, circle: int) -> Dict[str, Any]:
        """获取循环上下文"""
        return self._circle_context.get(circle, {})
    
    def set_task_context(self, task_id: str, context: Dict[str, Any]):
        """设置任务上下文"""
        self._task_context[task_id] = context
    
    def get_task_context(self, task_id: str) -> Dict[str, Any]:
        """获取任务上下文"""
        return self._task_context.get(task_id, {})
    
    def add_cell_content(self, cell_type: str, content: str, cell_index: int = None):
        """添加cell内容到上下文"""
        cell_info = {
            'type': cell_type,
            'content': content,
            'index': cell_index if cell_index is not None else len(self._cell_context)
        }
        self._cell_context.append(cell_info)
    
    def get_cell_context(self) -> List[Dict[str, Any]]:
        """获取所有cell上下文"""
        return self._cell_context.copy()
    
    def get_cell_context_summary(self, max_cells: int = 10) -> str:
        """获取cell上下文的摘要信息"""
        if not self._cell_context:
            return "暂无cell内容"
        
        recent_cells = self._cell_context[-max_cells:] if len(self._cell_context) > max_cells else self._cell_context
        
        summary = []
        for cell in recent_cells:
            cell_type_emoji = "📝" if cell['type'] == 'markdown' else "💻"
            summary.append(f"{cell_type_emoji} {cell['type']} Cell {cell['index']}: {cell['content'][:100]}...")
        
        return "\n".join(summary)
    
    def add_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """添加错误信息到上下文"""
        error_info = {
            'type': error_type,
            'message': error_message,
            'context': context or {},
            'timestamp': self._get_timestamp()
        }
        self._error_context.append(error_info)
    
    def get_error_context(self) -> List[Dict[str, Any]]:
        """获取错误上下文"""
        return self._error_context.copy()
    
    def get_recent_errors(self, count: int = 3) -> List[Dict[str, Any]]:
        """获取最近的错误信息"""
        return self._error_context[-count:] if self._error_context else []
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def clear(self):
        """清空上下文"""
        self._data.clear()
        self._phase_context.clear()
        self._circle_context.clear()
        self._task_context.clear()
        self._cell_context.clear()
        self._error_context.clear()
from abc import ABC, abstractmethod
from typing import Dict, Any

class PhaseEvaluator(ABC):
    @abstractmethod
    def evaluate_phase_success(self, phase_type: str, context: Dict[str, Any], goal: str, cell_context: str) -> bool:  
        pass

class CircleEvaluator(ABC):
    @abstractmethod
    def evaluate_circle_success(self, context: Dict[str, Any], goal: str, cell_context: str) -> bool:  
        pass
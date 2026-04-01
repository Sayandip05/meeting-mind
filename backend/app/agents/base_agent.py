"""Base agent class with LangSmith tracing support"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from langsmith import traceable
from app.config import get_settings

settings = get_settings()


class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.project_name = settings.langsmith_project
    
    @traceable(project_name=settings.langsmith_project)
    def execute(self, **kwargs) -> Any:
        """Execute the agent's main task with tracing"""
        return self._run(**kwargs)
    
    @abstractmethod
    def _run(self, **kwargs) -> Any:
        """Override this method in subclasses"""
        pass
    
    def get_name(self) -> str:
        return self.name

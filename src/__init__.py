"""
员工离职数据分析系统 - 源代码包
"""

__version__ = "1.0.0"
__author__ = "MiniMax Agent"

from .data_loader import DataLoader
from .data_processor import DataProcessor
from .analytics import Analytics
from .database import Database
from .ai_analyzer import AIAnalyzer
from .exporter import Exporter

__all__ = [
    "DataLoader",
    "DataProcessor",
    "Analytics",
    "Database",
    "AIAnalyzer",
    "Exporter"
]

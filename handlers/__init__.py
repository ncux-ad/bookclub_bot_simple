"""
@file: handlers/__init__.py
@description: Инициализация пакета обработчиков
@dependencies: handlers.user_handlers, handlers.admin_handlers
@created: 2024-01-15
"""

from .user_handlers import router as user_router
from .admin_handlers import router as admin_router
from .unknown_handlers import router as unknown_router

__all__ = ['user_router', 'admin_router', 'unknown_router'] 
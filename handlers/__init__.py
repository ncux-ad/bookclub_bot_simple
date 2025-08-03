"""
@file: handlers/__init__.py
@description: Инициализация обработчиков
@dependencies: handlers.user_handlers, handlers.admin_handlers, handlers.unknown_handlers, handlers.book_handlers
@created: 2025-01-03
"""

from .user_handlers import router as user_router
from .admin_handlers import router as admin_router
from .unknown_handlers import router as unknown_router
from .book_handlers import router as book_router

__all__ = ['user_router', 'admin_router', 'unknown_router', 'book_router'] 
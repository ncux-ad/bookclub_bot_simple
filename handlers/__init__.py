"""
@file: handlers/__init__.py
@description: Инициализация пакета обработчиков
@dependencies: handlers.user_handlers, handlers.admin_handlers
@created: 2024-01-15
"""

from .user_handlers import router as user_router
from .admin_handlers import router as admin_router
from .book_handlers import router as book_router
from .library_handlers import router as library_router
from .admin_book_handlers import router as admin_book_router
from .unknown_handlers import router as unknown_router

__all__ = ['user_router', 'admin_router', 'book_router', 'library_router', 'admin_book_router', 'unknown_router'] 
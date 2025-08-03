"""
@file: services/__init__.py
@description: Инициализация пакета сервисов
@dependencies: services.users, services.books, services.events
@created: 2024-01-15
"""

from .users import UserService
from .books import BookService
from .events import EventService

__all__ = ['UserService', 'BookService', 'EventService'] 
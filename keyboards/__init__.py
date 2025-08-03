"""
@file: keyboards/__init__.py
@description: Инициализация пакета клавиатур
@dependencies: keyboards.inline
@created: 2024-01-15
"""

from .inline import *

__all__ = ['create_books_keyboard', 'create_book_keyboard', 'create_back_keyboard', 'create_admin_keyboard'] 
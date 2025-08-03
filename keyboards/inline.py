"""
@file: keyboards/inline.py
@description: Inline клавиатуры для бота
@dependencies: aiogram.types
@created: 2024-01-15
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List, Any


def create_books_keyboard(books: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру со списком книг
    
    Args:
        books (Dict[str, Any]): Словарь с данными книг
        
    Returns:
        InlineKeyboardMarkup: Inline клавиатура с кнопками книг
    """
    keyboard = []
    
    for book_title in books.keys():
        keyboard.append([
            InlineKeyboardButton(
                text=book_title, 
                callback_data=f"book:{book_title}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_book_keyboard(book_title: str, formats: List[str]) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру для выбора формата книги
    
    Args:
        book_title (str): Название книги
        formats (List[str]): Список доступных форматов
        
    Returns:
        InlineKeyboardMarkup: Inline клавиатура с кнопками форматов
    """
    keyboard = []
    
    for fmt in formats:
        keyboard.append([
            InlineKeyboardButton(
                text=fmt, 
                callback_data=f"download:{book_title}:{fmt.lower()}"
            )
        ])
    
    # Кнопка возврата
    keyboard.append([
        InlineKeyboardButton(text="« Назад", callback_data="back_to_books")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_back_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру с кнопкой возврата"""
    keyboard = [
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_books")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_admin_keyboard() -> InlineKeyboardMarkup:
    """
    Создать клавиатуру администратора
    
    Returns:
        InlineKeyboardMarkup: Inline клавиатура с функциями администратора:
            - Статистика
            - Управление пользователями
            - Управление книгами
            - Управление событиями
    """
    keyboard = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="📚 Управление книгами", callback_data="admin_books")],
        [InlineKeyboardButton(text="📅 Управление событиями", callback_data="admin_events")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 
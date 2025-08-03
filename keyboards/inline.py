"""
@file: keyboards/inline.py
@description: Inline клавиатуры для бота
@dependencies: aiogram.types
@created: 2025-01-03
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


def create_book_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для подтверждения данных книги
    """
    keyboard = [
        [
            InlineKeyboardButton(text="📚 Изменить название", callback_data="edit_title"),
            InlineKeyboardButton(text="✍️ Изменить автора", callback_data="edit_author")
        ],
        [
            InlineKeyboardButton(text="📝 Изменить описание", callback_data="edit_description")
        ],
        [
            InlineKeyboardButton(text="🔗 Яндекс.Книги", callback_data="add_yandex"),
            InlineKeyboardButton(text="🔗 ЛитРес", callback_data="add_litres")
        ],
        [
            InlineKeyboardButton(text="🎧 Аудиокнига", callback_data="add_audio")
        ],
        [
            InlineKeyboardButton(text="✅ Добавить книгу", callback_data="confirm_add")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_skip_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой "Пропустить"
    """
    keyboard = [
        [
            InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_book_selection_keyboard(books: list, event_id: str = None) -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора книги
    
    Args:
        books: Список книг
        event_id: ID события (если выбор для события)
    """
    keyboard = []
    
    for book in books[:10]:  # Ограничиваем 10 книгами
        book_id = book.get('id', '')
        title = book.get('title', 'Неизвестное название')
        author = book.get('author', 'Неизвестный автор')
        
        # Сокращаем текст кнопки
        button_text = f"{title[:20]}{'...' if len(title) > 20 else ''} - {author[:15]}{'...' if len(author) > 15 else ''}"
        
        if event_id:
            callback_data = f"select_book_{book_id}_for_event_{event_id}"
        else:
            callback_data = f"select_book_{book_id}"
        
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    
    # Добавляем кнопку "Добавить новую книгу"
    if event_id:
        keyboard.append([InlineKeyboardButton(text="📚 Добавить новую книгу", callback_data=f"add_new_book_for_event_{event_id}")])
    else:
        keyboard.append([InlineKeyboardButton(text="📚 Добавить новую книгу", callback_data="add_new_book")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_book_management_keyboard(book_id: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для управления книгой
    """
    keyboard = [
        [
            InlineKeyboardButton(text="📝 Редактировать", callback_data=f"edit_book_{book_id}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_book_{book_id}")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data=f"book_stats_{book_id}"),
            InlineKeyboardButton(text="🔗 Ссылки", callback_data=f"book_links_{book_id}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_books")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 
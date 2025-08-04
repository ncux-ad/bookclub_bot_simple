"""
@file: utils/callback_utils.py
@description: Утилиты для работы с callback_data
@dependencies: hashlib, typing
@created: 2025-01-06
"""

import hashlib
from typing import Optional
from services.books import book_service


def safe_encode_title(title: str) -> str:
    """
    Безопасное кодирование названия книги для callback_data
    
    Создает короткий MD5-хэш от названия книги для использования
    в callback_data кнопок. Это необходимо потому что:
    - callback_data ограничен 64 байтами
    - Названия книг могут содержать специальные символы
    - Нужна уникальная идентификация книги
    
    Args:
        title (str): Полное название книги
        
    Returns:
        str: MD5-хэш (первые 16 символов) для callback_data
        
    Example:
        >>> safe_encode_title("Война и мир")
        'a1b2c3d4e5f6g7h8'
    """
    if not title:
        return ""
    
    return hashlib.md5(title.encode('utf-8')).hexdigest()[:16]


def safe_decode_title(encoded_title: str) -> Optional[str]:
    """
    Декодирование хэша обратно в название книги
    
    Ищет среди всех книг ту, чей хэш совпадает с переданным.
    Если книга не найдена, возвращает исходный encoded_title.
    
    Args:
        encoded_title (str): MD5-хэш названия книги
        
    Returns:
        Optional[str]: Полное название книги или encoded_title если не найдено
        
    Note:
        Функция выполняет поиск по всем книгам, что может быть
        медленно при большом количестве книг. Для оптимизации
        рекомендуется добавить кэширование.
    """
    if not encoded_title:
        return None
    
    try:
        books = book_service.get_all_books()
        
        # Поиск книги с совпадающим хэшем
        for title in books.keys():
            if safe_encode_title(title) == encoded_title:
                return title
        
        # Если не найдено, возвращаем исходное значение
        return encoded_title
        
    except Exception as e:
        # В случае ошибки возвращаем исходное значение
        from utils.logger import bot_logger
        bot_logger.log_error(e, f"Ошибка декодирования callback_data: {encoded_title}")
        return encoded_title


def create_callback_data(prefix: str, action: str, data: str) -> str:
    """
    Создание стандартизированного callback_data
    
    Формирует callback_data в едином формате: "prefix:action:data"
    Автоматически обрезает данные если они превышают лимит.
    
    Args:
        prefix (str): Префикс модуля (book, user, admin и т.д.)
        action (str): Действие (show, edit, delete и т.д.)
        data (str): Данные (ID, название и т.д.)
        
    Returns:
        str: Сформированный callback_data, не превышающий 64 байта
        
    Example:
        >>> create_callback_data("book", "show", "Война и мир")
        'book:show:a1b2c3d4e5f6g7h8'
    """
    # Кодируем данные если это название книги
    if prefix == "book" and len(data) > 10:
        data = safe_encode_title(data)
    
    callback = f"{prefix}:{action}:{data}"
    
    # Обрезаем если превышает лимит Telegram (64 байта)
    if len(callback.encode('utf-8')) > 64:
        # Обрезаем данные, сохраняя структуру
        max_data_length = 64 - len(f"{prefix}:{action}:".encode('utf-8'))
        data = data[:max_data_length].rstrip(":")
        callback = f"{prefix}:{action}:{data}"
    
    return callback


def parse_callback_data(callback_data: str) -> tuple[str, str, str]:
    """
    Парсинг callback_data в компоненты
    
    Разбирает callback_data обратно на составляющие:
    prefix, action, data
    
    Args:
        callback_data (str): Callback data в формате "prefix:action:data"
        
    Returns:
        tuple[str, str, str]: (prefix, action, data)
        
    Example:
        >>> parse_callback_data("book:show:a1b2c3d4e5f6g7h8")
        ('book', 'show', 'a1b2c3d4e5f6g7h8')
    """
    parts = callback_data.split(":", 2)
    
    if len(parts) != 3:
        return "", "", callback_data
    
    return parts[0], parts[1], parts[2]


# Константы для префиксов callback_data
class CallbackPrefixes:
    """Стандартные префиксы для callback_data"""
    
    # Префиксы для книг
    BOOK = "book"
    BOOK_DOWNLOAD = "download"
    BOOK_EDIT = "edit_book"
    BOOK_DELETE = "del_book"
    
    # Префиксы для пользователей
    USER = "user"
    USER_BAN = "user_ban"
    USER_UNBAN = "user_unban"
    USER_ROLE = "user_role"
    
    # Префиксы для администрирования
    ADMIN = "admin"
    ADMIN_STATS = "admin_stats"
    ADMIN_BACK = "admin_back"
    
    # Префиксы для навигации
    BACK = "back"
    BACK_TO_BOOKS = "back_to_books"
    NEXT_PAGE = "next"
    PREV_PAGE = "prev"
    
    # Префиксы для фильтров
    FILTER = "filter"
    SORT = "sort"


# Константы для действий
class CallbackActions:
    """Стандартные действия для callback_data"""
    
    SHOW = "show"
    EDIT = "edit" 
    DELETE = "delete"
    DOWNLOAD = "download"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    NEXT = "next"
    PREV = "prev"
    FILTER = "filter"
    SORT = "sort"
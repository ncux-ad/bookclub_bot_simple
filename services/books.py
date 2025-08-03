"""
@file: services/books.py
@description: Сервис для работы с книгами
@dependencies: typing, config, utils
@created: 2024-01-15
"""

from typing import Dict, Any, Optional, List
from pathlib import Path

from config import config
from utils.data_manager import data_manager
from utils.logger import bot_logger
from utils.security import security_manager


class BookService:
    """Сервис для работы с книгами"""
    
    def __init__(self):
        self.logger = bot_logger
    
    def get_book(self, title: str) -> Optional[Dict[str, Any]]:
        """Получить книгу по названию"""
        books = data_manager.load_json(config.database.books_file)
        return books.get(title)
    
    def get_all_books(self) -> Dict[str, Dict[str, Any]]:
        """Получить все книги"""
        return data_manager.load_json(config.database.books_file)
    
    def add_book(self, title: str, author: str, description: str = "", 
                 files: Dict[str, str] = None) -> bool:
        """Добавить новую книгу"""
        books = data_manager.load_json(config.database.books_file)
        
        if title in books:
            self.logger.log_error(Exception("Книга уже существует"), f"title: {title}")
            return False
        
        book_data = {
            "title": title,
            "author": author,
            "description": description
        }
        
        # Добавляем файлы если они есть
        if files:
            for format_type, file_path in files.items():
                if format_type in ['epub', 'fb2', 'mobi']:
                    book_data[f'{format_type}_file'] = file_path
        
        if not data_manager.validate_book_data(book_data):
            self.logger.log_error(Exception("Ошибка валидации данных книги"), f"title: {title}")
            return False
        
        books[title] = book_data
        
        if data_manager.save_json(config.database.books_file, books):
            self.logger.log_admin_action(0, f"добавление книги: {title}")
            return True
        return False
    
    def update_book(self, title: str, **kwargs) -> bool:
        """Обновить данные книги"""
        books = data_manager.load_json(config.database.books_file)
        
        if title not in books:
            return False
        
        books[title].update(kwargs)
        
        if data_manager.save_json(config.database.books_file, books):
            self.logger.log_admin_action(0, f"обновление книги: {title}")
            return True
        return False
    
    def delete_book(self, title: str) -> bool:
        """Удалить книгу"""
        books = data_manager.load_json(config.database.books_file)
        
        if title not in books:
            return False
        
        # Удаляем файлы книги
        book_data = books[title]
        for format_type in ['epub', 'fb2', 'mobi']:
            file_key = f'{format_type}_file'
            if file_key in book_data:
                file_path = book_data[file_key]
                if file_path and Path(file_path).exists():
                    try:
                        Path(file_path).unlink()
                        self.logger.log_file_operation("удаление", file_path, True)
                    except Exception as e:
                        self.logger.log_error(e, f"ошибка удаления файла {file_path}")
        
        del books[title]
        
        if data_manager.save_json(config.database.books_file, books):
            self.logger.log_admin_action(0, f"удаление книги: {title}")
            return True
        return False
    
    def get_book_formats(self, title: str) -> List[str]:
        """Получить доступные форматы книги"""
        book = self.get_book(title)
        if not book:
            return []
        
        formats = []
        for fmt in ['epub', 'fb2', 'mobi']:
            if f'{fmt}_file' in book:
                formats.append(fmt)
        
        return formats
    
    def add_book_file(self, title: str, format_type: str, file_path: str) -> bool:
        """Добавить файл к книге"""
        if format_type not in ['epub', 'fb2', 'mobi']:
            return False
        
        books = data_manager.load_json(config.database.books_file)
        
        if title not in books:
            return False
        
        # Валидация пути файла
        sanitized_path = security_manager.sanitize_filename(file_path)
        
        books[title][f'{format_type}_file'] = sanitized_path
        
        if data_manager.save_json(config.database.books_file, books):
            self.logger.log_admin_action(0, f"добавление файла {format_type} к книге {title}")
            return True
        return False
    
    def remove_book_file(self, title: str, format_type: str) -> bool:
        """Удалить файл книги"""
        if format_type not in ['epub', 'fb2', 'mobi']:
            return False
        
        books = data_manager.load_json(config.database.books_file)
        
        if title not in books:
            return False
        
        file_key = f'{format_type}_file'
        if file_key in books[title]:
            del books[title][file_key]
            
            if data_manager.save_json(config.database.books_file, books):
                self.logger.log_admin_action(0, f"удаление файла {format_type} книги {title}")
                return True
        
        return False
    
    def search_books(self, query: str) -> Dict[str, Dict[str, Any]]:
        """Поиск книг по запросу"""
        books = data_manager.load_json(config.database.books_file)
        query_lower = query.lower()
        
        results = {}
        for title, book_data in books.items():
            if (query_lower in title.lower() or 
                query_lower in book_data.get('author', '').lower() or
                query_lower in book_data.get('description', '').lower()):
                results[title] = book_data
        
        return results
    
    def get_books_by_author(self, author: str) -> Dict[str, Dict[str, Any]]:
        """Получить книги по автору"""
        books = data_manager.load_json(config.database.books_file)
        author_lower = author.lower()
        
        results = {}
        for title, book_data in books.items():
            if author_lower in book_data.get('author', '').lower():
                results[title] = book_data
        
        return results


# Создаем глобальный экземпляр сервиса книг
book_service = BookService() 
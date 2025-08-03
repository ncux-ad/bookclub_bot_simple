"""
@file: services/books.py
@description: Сервис для работы с книгами
@dependencies: utils.data_manager, utils.logger, datetime, zipfile, xml.etree.ElementTree
@created: 2025-01-03
"""

import json
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import tempfile
import shutil

from utils.data_manager import data_manager
from utils.logger import bot_logger


class BookService:
    """
    Сервис для работы с книгами
    
    Обеспечивает добавление книг из ZIP архивов, парсинг FB2 файлов,
    конвертацию в различные форматы и управление библиотекой.
    """
    
    def __init__(self):
        self.logger = bot_logger.logger
        self.books_file = "data/books.json"
        self.books_dir = Path("books")
        self.books_dir.mkdir(exist_ok=True)
    
    def get_all_books(self) -> Dict[str, Any]:
        """Получить все книги"""
        return data_manager.load_data(self.books_file)
    
    def get_book(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Получить книгу по ID"""
        books = self.get_all_books()
        return books.get(book_id)
    
    def add_book(self, book_data: Dict[str, Any]) -> str:
        """
        Добавить новую книгу
        
        Args:
            book_data: Данные книги
            
        Returns:
            str: ID добавленной книги
        """
        books = self.get_all_books()
        
        # Генерируем уникальный ID
        book_id = f"book_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Добавляем метаданные
        book_data.update({
            'id': book_id,
            'added_at': datetime.now().isoformat(),
            'added_by': book_data.get('added_by', 'unknown')
        })
        
        books[book_id] = book_data
        data_manager.save_data(self.books_file, books)
        
        self.logger.info(f"Добавлена книга: {book_data.get('title', 'Unknown')} (ID: {book_id})")
        return book_id
    
    def update_book(self, book_id: str, updates: Dict[str, Any]) -> bool:
        """Обновить данные книги"""
        books = self.get_all_books()
        if book_id not in books:
            return False
        
        books[book_id].update(updates)
        books[book_id]['updated_at'] = datetime.now().isoformat()
        
        data_manager.save_data(self.books_file, books)
        self.logger.info(f"Обновлена книга: {book_id}")
        return True
    
    def delete_book(self, book_id: str) -> bool:
        """Удалить книгу"""
        books = self.get_all_books()
        if book_id not in books:
            return False
        
        # Удаляем файлы книги
        book = books[book_id]
        book_dir = self.books_dir / book_id
        if book_dir.exists():
            shutil.rmtree(book_dir)
        
        del books[book_id]
        data_manager.save_data(self.books_file, books)
        
        self.logger.info(f"Удалена книга: {book_id}")
        return True
    
    def process_zip_archive(self, zip_path: str, added_by: str) -> Dict[str, Any]:
        """
        Обработать ZIP архив с книгой
        
        Args:
            zip_path: Путь к ZIP файлу
            added_by: ID пользователя, добавившего книгу
            
        Returns:
            Dict[str, Any]: Данные книги
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # Ищем FB2 файл в архиве
                fb2_files = [f for f in zip_file.namelist() if f.endswith('.fb2')]
                
                if not fb2_files:
                    raise ValueError("FB2 файл не найден в архиве")
                
                fb2_filename = fb2_files[0]
                
                # Извлекаем и парсим FB2
                with zip_file.open(fb2_filename) as fb2_file:
                    book_data = self._parse_fb2_file(fb2_file)
                
                # Добавляем информацию о пользователе
                book_data['added_by'] = added_by
                
                return book_data
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки ZIP архива: {e}")
            raise
    
    def _parse_fb2_file(self, fb2_file) -> Dict[str, Any]:
        """
        Парсить FB2 файл и извлекать метаданные
        
        Args:
            fb2_file: Файловый объект FB2
            
        Returns:
            Dict[str, Any]: Метаданные книги
        """
        try:
            tree = ET.parse(fb2_file)
            root = tree.getroot()
            
            # Определяем namespace
            ns = {'fb2': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
            
            # Извлекаем метаданные
            title_info = root.find('.//fb2:title-info', ns)
            if title_info is None:
                raise ValueError("Не удалось найти title-info в FB2 файле")
            
            # Название книги
            book_title = title_info.find('.//fb2:book-title', ns)
            title = book_title.text if book_title is not None else "Неизвестное название"
            
            # Автор
            author_info = title_info.find('.//fb2:author', ns)
            author = "Неизвестный автор"
            if author_info is not None:
                first_name = author_info.find('.//fb2:first-name', ns)
                last_name = author_info.find('.//fb2:last-name', ns)
                middle_name = author_info.find('.//fb2:middle-name', ns)
                
                author_parts = []
                if first_name is not None and first_name.text:
                    author_parts.append(first_name.text)
                if middle_name is not None and middle_name.text:
                    author_parts.append(middle_name.text)
                if last_name is not None and last_name.text:
                    author_parts.append(last_name.text)
                
                if author_parts:
                    author = " ".join(author_parts)
            
            # Аннотация
            annotation = title_info.find('.//fb2:annotation', ns)
            description = ""
            if annotation is not None:
                # Извлекаем текст из всех параграфов
                paragraphs = annotation.findall('.//fb2:p', ns)
                if paragraphs:
                    description = "\n".join([p.text for p in paragraphs if p.text])
            
            # Жанры
            genres = []
            for genre in title_info.findall('.//fb2:genre', ns):
                if genre.text:
                    genres.append(genre.text)
            
            # Язык
            lang = title_info.find('.//fb2:lang', ns)
            language = lang.text if lang is not None else "ru"
            
            # Дата публикации
            date_info = title_info.find('.//fb2:date', ns)
            publication_date = ""
            if date_info is not None:
                date_value = date_info.find('.//fb2:value', ns)
                if date_value is not None and date_value.text:
                    publication_date = date_value.text
            
            return {
                'title': title,
                'author': author,
                'description': description,
                'genres': genres,
                'language': language,
                'publication_date': publication_date,
                'original_format': 'fb2',
                'formats': ['fb2'],  # Пока только FB2, конвертация будет позже
                'file_paths': {},  # Пути к файлам будут добавлены позже
                'links': {
                    'yandex': '',
                    'litres': '',
                    'audio': ''
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка парсинга FB2 файла: {e}")
            raise
    
    def search_books(self, query: str) -> List[Dict[str, Any]]:
        """
        Поиск книг по запросу
        
        Args:
            query: Поисковый запрос
            
        Returns:
            List[Dict[str, Any]]: Список найденных книг
        """
        books = self.get_all_books()
        query_lower = query.lower()
        
        results = []
        for book_id, book_data in books.items():
            # Поиск по названию, автору и описанию
            title = book_data.get('title', '').lower()
            author = book_data.get('author', '').lower()
            description = book_data.get('description', '').lower()
            
            if (query_lower in title or 
                query_lower in author or 
                query_lower in description):
                results.append({**book_data, 'id': book_id})
        
        return results
    
    def get_books_for_event(self) -> List[Dict[str, Any]]:
        """Получить список книг для выбора в событиях"""
        books = self.get_all_books()
        return [
            {
                'id': book_id,
                'title': book_data.get('title', 'Неизвестное название'),
                'author': book_data.get('author', 'Неизвестный автор')
            }
            for book_id, book_data in books.items()
        ]


# Создаем экземпляр сервиса
book_service = BookService() 
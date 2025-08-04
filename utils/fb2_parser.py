"""
@file: utils/fb2_parser.py
@description: Парсер FB2 файлов для извлечения метаданных
@dependencies: xml.etree.ElementTree, zipfile, pathlib
@created: 2025-01-04
"""

import xml.etree.ElementTree as ET
import zipfile
import platform
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import re
from datetime import datetime

from utils.logger import bot_logger


class FB2Parser:
    """Парсер FB2 файлов для извлечения метаданных"""
    
    def __init__(self):
        self.logger = bot_logger
        self.is_windows = platform.system() == "Windows"
    
    def extract_fb2_from_zip(self, zip_path: str) -> Optional[str]:
        """
        Извлечь FB2 файл из ZIP архива
        
        Args:
            zip_path: Путь к ZIP архиву
            
        Returns:
            str: Путь к извлеченному FB2 файлу или None
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # Ищем FB2 файлы в архиве
                fb2_files = [f for f in zip_file.namelist() if f.lower().endswith('.fb2')]
                
                if not fb2_files:
                    self.logger.log_error(Exception("FB2 файлы не найдены в архиве"), f"zip_path: {zip_path}")
                    return None
                
                # Извлекаем первый FB2 файл
                fb2_filename = fb2_files[0]
                extract_path = Path("temp") / Path(fb2_filename).name
                extract_path.parent.mkdir(exist_ok=True)
                
                zip_file.extract(fb2_filename, "temp")
                extracted_path = Path("temp") / fb2_filename
                
                # Переименовываем для удобства
                final_path = Path("temp") / Path(fb2_filename).name
                if extracted_path != final_path:
                    extracted_path.rename(final_path)
                
                self.logger.log_file_operation("извлечение", str(final_path), True)
                return str(final_path)
                
        except zipfile.BadZipFile:
            self.logger.log_error(Exception("Некорректный ZIP архив"), f"zip_path: {zip_path}")
            return None
        except Exception as e:
            self.logger.log_error(e, f"ошибка извлечения FB2 из ZIP: {zip_path}")
            return None
    
    def parse_fb2_metadata(self, fb2_path: str) -> Optional[Dict[str, Any]]:
        """
        Парсить метаданные из FB2 файла
        
        Args:
            fb2_path: Путь к FB2 файлу
            
        Returns:
            Dict[str, Any]: Метаданные книги или None
        """
        try:
            # Обработка кодировок для Windows
            if self.is_windows:
                # Пробуем разные кодировки для Windows
                encodings = ['utf-8', 'cp1251', 'windows-1251', 'iso-8859-1']
                tree = None
                
                for encoding in encodings:
                    try:
                        with open(fb2_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        tree = ET.fromstring(content)
                        break
                    except UnicodeDecodeError:
                        continue
                    except ET.ParseError:
                        continue
                
                if tree is None:
                    # Если не удалось с кодировками, пробуем бинарный режим
                    with open(fb2_path, 'rb') as f:
                        content = f.read()
                    tree = ET.fromstring(content)
            else:
                # Для Linux используем стандартный парсер
                tree = ET.parse(fb2_path)
                tree = tree.getroot()
            
            root = tree
            
            # Определяем namespace для FB2
            namespace = {'fb2': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
            
            # Извлекаем метаданные
            metadata = {}
            
            # Название
            title_info = root.find('.//fb2:title-info', namespace)
            if title_info is not None:
                # Основное название
                book_title = title_info.find('.//fb2:book-title', namespace)
                if book_title is not None:
                    metadata['title'] = book_title.text.strip()
                
                # Автор
                author = title_info.find('.//fb2:author', namespace)
                if author is not None:
                    first_name = author.find('.//fb2:first-name', namespace)
                    last_name = author.find('.//fb2:last-name', namespace)
                    middle_name = author.find('.//fb2:middle-name', namespace)
                    
                    author_parts = []
                    if first_name is not None and first_name.text:
                        author_parts.append(first_name.text.strip())
                    if middle_name is not None and middle_name.text:
                        author_parts.append(middle_name.text.strip())
                    if last_name is not None and last_name.text:
                        author_parts.append(last_name.text.strip())
                    
                    if author_parts:
                        metadata['author'] = ' '.join(author_parts)
                
                # Жанры
                genres = title_info.findall('.//fb2:genre', namespace)
                if genres:
                    metadata['genres'] = [genre.text.strip() for genre in genres if genre.text]
                
                # Аннотация
                annotation = title_info.find('.//fb2:annotation', namespace)
                if annotation is not None:
                    # Извлекаем текст из всех параграфов аннотации
                    paragraphs = annotation.findall('.//fb2:p', namespace)
                    if paragraphs:
                        annotation_text = '\n'.join([p.text.strip() for p in paragraphs if p.text])
                        metadata['description'] = annotation_text
            
            # Дата публикации
            publish_info = root.find('.//fb2:publish-info', namespace)
            if publish_info is not None:
                year = publish_info.find('.//fb2:year', namespace)
                if year is not None and year.text:
                    try:
                        metadata['year'] = int(year.text.strip())
                    except ValueError:
                        pass
            
            # Дополнительная информация
            document_info = root.find('.//fb2:document-info', namespace)
            if document_info is not None:
                # Дата создания
                date = document_info.find('.//fb2:date', namespace)
                if date is not None:
                    value = date.get('value')
                    if value:
                        try:
                            # Парсим дату в формате YYYY-MM-DD
                            metadata['created_date'] = value
                        except:
                            pass
            
            # Проверяем обязательные поля
            if 'title' not in metadata or 'author' not in metadata:
                self.logger.log_error(Exception("Отсутствуют обязательные метаданные"), f"fb2_path: {fb2_path}")
                return None
            
            self.logger.log_file_operation("парсинг", fb2_path, True)
            return metadata
            
        except ET.ParseError as e:
            self.logger.log_error(e, f"ошибка парсинга XML в FB2: {fb2_path}")
            return None
        except Exception as e:
            self.logger.log_error(e, f"ошибка парсинга FB2: {fb2_path}")
            return None
    
    def clean_temp_files(self, file_path: str) -> None:
        """
        Очистить временные файлы
        
        Args:
            file_path: Путь к файлу для удаления
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                self.logger.log_file_operation("удаление временного файла", file_path, True)
        except Exception as e:
            self.logger.log_error(e, f"ошибка удаления временного файла: {file_path}")


# Создаем глобальный экземпляр парсера
fb2_parser = FB2Parser() 
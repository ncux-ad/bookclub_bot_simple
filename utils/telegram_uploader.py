"""
@file: utils/telegram_uploader.py
@description: Загрузчик файлов в Telegram для удобного шаринга
@dependencies: aiogram, pathlib
@created: 2025-01-04
"""

from pathlib import Path
from typing import Dict, Optional, List
import asyncio
import platform
from aiogram.types import FSInputFile

from utils.logger import bot_logger


class TelegramUploader:
    """Загрузчик файлов в Telegram"""
    
    def __init__(self):
        self.logger = bot_logger
        self.uploaded_files = {}  # Кэш загруженных файлов
        self.is_windows = platform.system() == "Windows"
    
    async def upload_book_file(self, bot, file_path: str, chat_id: int) -> Optional[str]:
        """
        Загрузить файл книги в Telegram
        
        Args:
            bot: Экземпляр бота
            file_path: Путь к файлу
            chat_id: ID чата для загрузки
            
        Returns:
            str: file_id загруженного файла или None
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.log_error(Exception("Файл не найден"), f"file_path: {file_path}")
                return None
            
            # Нормализуем путь для Windows
            if self.is_windows:
                path = path.resolve()
            
            # Определяем тип файла по расширению
            file_extension = path.suffix.lower()
            
            # Загружаем файл в зависимости от типа
            if file_extension == '.epub':
                message = await bot.send_document(
                    chat_id=chat_id,
                    document=FSInputFile(str(path)),
                    caption=f"📚 {path.stem}.epub"
                )
            elif file_extension == '.mobi':
                message = await bot.send_document(
                    chat_id=chat_id,
                    document=FSInputFile(str(path)),
                    caption=f"📚 {path.stem}.mobi"
                )
            elif file_extension == '.fb2':
                message = await bot.send_document(
                    chat_id=chat_id,
                    document=FSInputFile(str(path)),
                    caption=f"📚 {path.stem}.fb2"
                )
            else:
                self.logger.log_error(Exception("Неподдерживаемый формат файла"), f"file_path: {file_path}")
                return None
            
            # Получаем file_id
            if message.document:
                file_id = message.document.file_id
                self.uploaded_files[file_path] = file_id
                self.logger.log_file_operation("загрузка в Telegram", file_path, True)
                return file_id
            else:
                self.logger.log_error(Exception("Не удалось получить file_id"), f"file_path: {file_path}")
                return None
                
        except Exception as e:
            self.logger.log_error(e, f"ошибка загрузки файла в Telegram: {file_path}")
            return None
    
    async def upload_book_formats(self, bot, file_paths: Dict[str, str], chat_id: int) -> Dict[str, str]:
        """
        Загрузить все форматы книги в Telegram
        
        Args:
            bot: Экземпляр бота
            file_paths: Словарь с путями к файлам разных форматов
            chat_id: ID чата для загрузки
            
        Returns:
            Dict[str, str]: Словарь с file_id для каждого формата
        """
        uploaded_file_ids = {}
        
        for format_type, file_path in file_paths.items():
            file_id = await self.upload_book_file(bot, file_path, chat_id)
            if file_id:
                uploaded_file_ids[format_type] = file_id
        
        return uploaded_file_ids
    
    def get_file_id(self, file_path: str) -> Optional[str]:
        """
        Получить file_id для уже загруженного файла
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            str: file_id или None
        """
        return self.uploaded_files.get(file_path)
    
    def clear_cache(self) -> None:
        """Очистить кэш загруженных файлов"""
        self.uploaded_files.clear()
        self.logger.log_file_operation("очистка кэша", "uploaded_files", True)


# Создаем глобальный экземпляр загрузчика
telegram_uploader = TelegramUploader() 
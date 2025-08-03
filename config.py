"""
@file: config.py
@description: Конфигурация приложения с валидацией и типизацией
@dependencies: os, typing
@created: 2024-01-15
"""

import os
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Конфигурация базы данных"""
    users_file: str = "data/users.json"
    books_file: str = "data/books.json"
    events_file: str = "data/events.json"


@dataclass
class SecurityConfig:
    """Конфигурация безопасности"""
    secret_phrase: str
    admin_ids: List[int]
    max_login_attempts: int = 3
    session_timeout: int = 3600  # 1 час


@dataclass
class FileConfig:
    """Конфигурация файлов"""
    upload_dir: str = "books"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: List[str] = None
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = ['.epub', '.fb2', '.mobi', '.pdf']


@dataclass
class LoggingConfig:
    """Конфигурация логирования"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = "logs/bot.log"


class Config:
    """Основная конфигурация приложения"""
    
    def __init__(self):
        self.bot_token = self._get_required_env("BOT_TOKEN")
        self.database = DatabaseConfig()
        self.security = SecurityConfig(
            secret_phrase=self._get_env("SECRET_PHRASE", "bookclub2024"),
            admin_ids=self._parse_admin_ids()
        )
        self.files = FileConfig()
        self.logging = LoggingConfig()
        
        # Создаем необходимые директории
        self._create_directories()
    
    def _get_required_env(self, key: str) -> str:
        """Получить обязательную переменную окружения"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Обязательная переменная окружения {key} не установлена")
        return value
    
    def _get_env(self, key: str, default: str) -> str:
        """Получить переменную окружения с значением по умолчанию"""
        return os.getenv(key, default)
    
    def _parse_admin_ids(self) -> List[int]:
        """Парсинг ID администраторов из переменной окружения"""
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if not admin_ids_str:
            return []
        
        try:
            return [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]
        except ValueError as e:
            raise ValueError(f"Неверный формат ADMIN_IDS: {e}")
    
    def _create_directories(self) -> None:
        """Создание необходимых директорий"""
        Path(self.files.upload_dir).mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        return user_id in self.security.admin_ids


# Создаем глобальный экземпляр конфигурации
config = Config() 
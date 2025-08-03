"""
@file: config.py
@description: Конфигурация приложения с валидацией и типизацией
@dependencies: os, typing, pathlib, utils.env_validator
@created: 2024-01-15
"""

import os
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path
from utils.env_validator import env_validator


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
    """Основная конфигурация приложения с валидацией переменных окружения"""
    
    def __init__(self):
        # Валидируем переменные окружения
        is_valid, validation_result = env_validator.validate_all()
        
        if not is_valid:
            env_validator.print_validation_report(validation_result)
            raise ValueError("Ошибки в конфигурации переменных окружения")
        
        # Инициализируем конфигурацию с валидированными данными
        self.bot_token = validation_result["bot_token"]
        self.database = DatabaseConfig()
        self.security = SecurityConfig(
            secret_phrase=validation_result["secret_phrase"],
            admin_ids=validation_result["admin_ids"]
        )
        self.files = FileConfig()
        self.logging = LoggingConfig()
        
        # Выводим отчет о валидации
        env_validator.print_validation_report(validation_result)
    
    def _get_required_env(self, key: str) -> str:
        """Получить обязательную переменную окружения"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Обязательная переменная окружения {key} не установлена")
        return value
    
    def _get_env(self, key: str, default: str) -> str:
        """Получить переменную окружения с значением по умолчанию"""
        return os.getenv(key, default)
    
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
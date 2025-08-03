"""
@file: utils/logger.py
@description: Система логирования с ротацией и фильтрацией
@dependencies: logging, pathlib, config
@created: 2024-01-15
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from config import config


class SensitiveDataFilter(logging.Filter):
    """Фильтр для скрытия чувствительных данных в логах"""
    
    def __init__(self):
        super().__init__()
        self.sensitive_patterns = [
            r'token[=:]\s*\w+',
            r'password[=:]\s*\w+',
            r'secret[=:]\s*\w+',
            r'api_key[=:]\s*\w+',
            r'admin_id[=:]\s*\d+'
        ]
    
    def filter(self, record):
        """Фильтрация чувствительных данных"""
        if hasattr(record, 'msg'):
            import re
            for pattern in self.sensitive_patterns:
                record.msg = re.sub(pattern, '[HIDDEN]', str(record.msg))
        
        return True


def setup_logging(
    log_file: Optional[str] = None,
    log_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """Настройка системы логирования"""
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Очищаем существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # Файловый обработчик с ротацией
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
    
    # Добавляем фильтр для чувствительных данных
    sensitive_filter = SensitiveDataFilter()
    root_logger.addFilter(sensitive_filter)
    
    # Логируем запуск системы
    logger = logging.getLogger(__name__)
    logger.info("Система логирования инициализирована")


def get_logger(name: str) -> logging.Logger:
    """Получить логгер с указанным именем"""
    return logging.getLogger(name)


class BotLogger:
    """Специализированный логгер для бота"""
    
    def __init__(self, name: str = "bot"):
        self.logger = get_logger(name)
    
    def log_user_action(self, user_id: int, action: str, details: str = "") -> None:
        """Логирование действий пользователя"""
        self.logger.info(f"Пользователь {user_id}: {action} {details}".strip())
    
    def log_admin_action(self, admin_id: int, action: str, details: str = "") -> None:
        """Логирование действий администратора"""
        self.logger.info(f"Администратор {admin_id}: {action} {details}".strip())
    
    def log_error(self, error: Exception, context: str = "") -> None:
        """Логирование ошибок"""
        self.logger.error(f"Ошибка {context}: {error}", exc_info=True)
    
    def log_security_event(self, event_type: str, user_id: int, details: str = "") -> None:
        """Логирование событий безопасности"""
        self.logger.warning(f"Событие безопасности [{event_type}] пользователь {user_id}: {details}")
    
    def log_file_operation(self, operation: str, filepath: str, success: bool) -> None:
        """Логирование операций с файлами"""
        status = "успешно" if success else "ошибка"
        self.logger.info(f"Операция с файлом {operation}: {filepath} - {status}")


# Создаем глобальный экземпляр логгера бота
bot_logger = BotLogger() 
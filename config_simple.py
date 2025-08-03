import os
from typing import List

class SimpleConfig:
    """Упрощенная конфигурация бота"""
    
    # Основные настройки
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    SECRET_PHRASE = os.getenv("SECRET_PHRASE", "bookclub2024")
    
    # Список администраторов (ID через запятую)
    ADMIN_IDS = []
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]
    
    # Настройки файлов
    UPLOAD_DIR = "books"
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Создаем экземпляр конфигурации
settings = SimpleConfig() 
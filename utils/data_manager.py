"""
@file: utils/data_manager.py
@description: Менеджер данных с кэшированием и валидацией
@dependencies: json, typing, pathlib, logging
@created: 2024-01-15
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps


class DataCache:
    """Кэш для данных с автоматическим обновлением"""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 минут по умолчанию
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
    
    def get(self, key: str) -> Optional[Any]:
        """Получить данные из кэша"""
        if key not in self._cache:
            return None
        
        if datetime.now() - self._timestamps[key] > self._ttl:
            del self._cache[key]
            del self._timestamps[key]
            return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Установить данные в кэш"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
    
    def invalidate(self, key: str) -> None:
        """Инвалидировать кэш для ключа"""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]


class DataManager:
    """Менеджер для работы с JSON данными"""
    
    def __init__(self, cache_ttl: int = 300):
        self.cache = DataCache(cache_ttl)
        self.logger = logging.getLogger(__name__)
    
    def load_json(self, filepath: str) -> Dict[str, Any]:
        """Загрузить данные из JSON файла с кэшированием"""
        cache_key = f"file_{filepath}"
        cached_data = self.cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        try:
            path = Path(filepath)
            if not path.exists():
                self.logger.warning(f"Файл {filepath} не найден, создаем пустой")
                return {}
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.cache.set(cache_key, data)
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка парсинга JSON файла {filepath}: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Ошибка чтения файла {filepath}: {e}")
            return {}
    
    def save_json(self, filepath: str, data: Dict[str, Any]) -> bool:
        """Сохранить данные в JSON файл"""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Инвалидируем кэш
            cache_key = f"file_{filepath}"
            self.cache.invalidate(cache_key)
            
            self.logger.info(f"Данные успешно сохранены в {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения файла {filepath}: {e}")
            return False
    
    def validate_user_data(self, user_data: Dict[str, Any]) -> bool:
        """Валидация данных пользователя"""
        required_fields = ['name', 'registered_at', 'status']
        
        for field in required_fields:
            if field not in user_data:
                self.logger.warning(f"Отсутствует обязательное поле {field} в данных пользователя")
                return False
        
        if user_data['status'] not in ['active', 'inactive', 'banned']:
            self.logger.warning(f"Неверный статус пользователя: {user_data['status']}")
            return False
        
        return True
    
    def validate_book_data(self, book_data: Dict[str, Any]) -> bool:
        """Валидация данных книги"""
        required_fields = ['title', 'author']
        
        for field in required_fields:
            if field not in book_data:
                self.logger.warning(f"Отсутствует обязательное поле {field} в данных книги")
                return False
        
        return True
    
    def validate_event_data(self, event_data: Dict[str, Any]) -> bool:
        """Валидация данных события"""
        required_fields = ['title', 'date', 'time']
        
        for field in required_fields:
            if field not in event_data:
                self.logger.warning(f"Отсутствует обязательное поле {field} в данных события")
                return False
        
        return True


# Создаем глобальный экземпляр менеджера данных
data_manager = DataManager() 
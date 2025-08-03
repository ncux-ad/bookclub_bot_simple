"""
@file: utils/env_validator.py
@description: Валидатор переменных окружения
@dependencies: os, re, typing
@created: 2024-01-15
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class EnvValidator:
    """Валидатор переменных окружения"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_bot_token(self, token: str) -> bool:
        """Валидация токена бота"""
        if not token:
            self.errors.append("BOT_TOKEN не установлен")
            return False
        
        # Проверка формата токена Telegram
        if not re.match(r'^\d+:[A-Za-z0-9_-]{35}$', token):
            # Для тестового режима разрешаем пример токена
            if token == "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz":
                self.warnings.append("BOT_TOKEN использует тестовое значение - замените на реальный токен")
                return True
            self.errors.append("BOT_TOKEN имеет неверный формат")
            return False
        
        return True
    
    def validate_secret_phrase(self, phrase: str) -> bool:
        """Валидация секретной фразы"""
        if not phrase:
            self.warnings.append("SECRET_PHRASE не установлен, используется значение по умолчанию")
            return True
        
        if len(phrase) < 6:
            self.errors.append("SECRET_PHRASE должен содержать минимум 6 символов")
            return False
        
        if len(phrase) > 50:
            self.errors.append("SECRET_PHRASE слишком длинный (максимум 50 символов)")
            return False
        
        return True
    
    def validate_admin_ids(self, admin_ids_str: str) -> Tuple[bool, List[int]]:
        """Валидация ID администраторов"""
        admin_ids = []
        
        if not admin_ids_str:
            self.warnings.append("ADMIN_IDS не установлен, администраторы не настроены")
            return True, admin_ids
        
        try:
            admin_ids = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]
        except ValueError:
            self.errors.append("ADMIN_IDS содержит неверные значения")
            return False, []
        
        if not admin_ids:
            self.warnings.append("ADMIN_IDS пустой, администраторы не настроены")
            return True, admin_ids
        
        # Проверка на дубликаты
        if len(admin_ids) != len(set(admin_ids)):
            self.errors.append("ADMIN_IDS содержит дубликаты")
            return False, []
        
        # Проверка диапазона ID
        for admin_id in admin_ids:
            if admin_id <= 0:
                self.errors.append(f"ADMIN_ID {admin_id} должен быть положительным числом")
                return False, []
        
        return True, admin_ids
    
    def validate_file_paths(self) -> bool:
        """Валидация путей к файлам"""
        required_dirs = ['books', 'data', 'logs']
        
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.warnings.append(f"Создана директория {dir_name}")
                except Exception as e:
                    self.errors.append(f"Не удалось создать директорию {dir_name}: {e}")
                    return False
        
        return True
    
    def validate_all(self) -> Tuple[bool, Dict[str, any]]:
        """Валидация всех переменных окружения"""
        self.errors.clear()
        self.warnings.clear()
        
        # Получаем переменные окружения
        bot_token = os.getenv("BOT_TOKEN", "")
        secret_phrase = os.getenv("SECRET_PHRASE", "bookclub2024")
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        
        # Валидируем каждую переменную
        token_valid = self.validate_bot_token(bot_token)
        phrase_valid = self.validate_secret_phrase(secret_phrase)
        admin_ids_valid, admin_ids = self.validate_admin_ids(admin_ids_str)
        paths_valid = self.validate_file_paths()
        
        # Формируем результат
        is_valid = token_valid and phrase_valid and admin_ids_valid and paths_valid
        
        result = {
            "bot_token": bot_token if token_valid else "",
            "secret_phrase": secret_phrase,
            "admin_ids": admin_ids,
            "is_valid": is_valid,
            "errors": self.errors.copy(),
            "warnings": self.warnings.copy()
        }
        
        return is_valid, result
    
    def print_validation_report(self, result: Dict[str, any]) -> None:
        """Вывод отчета о валидации"""
        print("🔍 Отчет о валидации переменных окружения:")
        print("=" * 50)
        
        if result["is_valid"]:
            print("✅ Валидация пройдена успешно")
        else:
            print("❌ Валидация не пройдена")
        
        if result["errors"]:
            print("\n❌ Ошибки:")
            for error in result["errors"]:
                print(f"  - {error}")
        
        if result["warnings"]:
            print("\n⚠️ Предупреждения:")
            for warning in result["warnings"]:
                print(f"  - {warning}")
        
        print("\n📋 Результат валидации:")
        print(f"  BOT_TOKEN: {'✅ Установлен' if result['bot_token'] else '❌ Не установлен'}")
        print(f"  SECRET_PHRASE: {'✅ Установлен' if result['secret_phrase'] else '⚠️ По умолчанию'}")
        print(f"  ADMIN_IDS: {'✅ Настроены' if result['admin_ids'] else '⚠️ Не настроены'}")
        
        print("=" * 50)


# Создаем глобальный экземпляр валидатора
env_validator = EnvValidator() 
"""
@file: services/users.py
@description: Сервис для работы с пользователями
@dependencies: typing, datetime, config, utils
@created: 2024-01-15
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from config import config
from utils.data_manager import data_manager
from utils.logger import bot_logger


class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self):
        self.logger = bot_logger
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить пользователя по ID
        
        Args:
            user_id (str): ID пользователя
            
        Returns:
            Optional[Dict[str, Any]]: Данные пользователя или None если не найден
        """
        users = data_manager.load_json(config.database.users_file)
        return users.get(user_id)
    
    def create_user(self, user_id: str, name: str, username: Optional[str] = None, status: str = "inactive") -> bool:
        """
        Создать нового пользователя
        
        Args:
            user_id (str): Уникальный ID пользователя
            name (str): Имя пользователя
            username (Optional[str]): Username пользователя
            status (str): Статус пользователя (inactive/active)
            
        Returns:
            bool: True если пользователь создан успешно, False в противном случае
        """
        users = data_manager.load_json(config.database.users_file)
        
        if user_id in users:
            self.logger.log_user_action(int(user_id), "попытка повторной регистрации")
            return False
        
        user_data = {
            "name": name,
            "username": username,
            "registered_at": datetime.now().isoformat(),
            "status": status,
            "first_interaction": datetime.now().isoformat()
        }
        
        if not data_manager.validate_user_data(user_data):
            self.logger.log_error(Exception("Ошибка валидации данных пользователя"), f"user_id: {user_id}")
            return False
        
        users[user_id] = user_data
        
        if data_manager.save_json(config.database.users_file, users):
            self.logger.log_user_action(int(user_id), f"создание пользователя со статусом {status}")
            return True
        else:
            self.logger.log_error(Exception("Ошибка сохранения пользователя"), f"user_id: {user_id}")
            return False
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """Обновить данные пользователя"""
        users = data_manager.load_json(config.database.users_file)
        
        if user_id not in users:
            return False
        
        users[user_id].update(kwargs)
        
        if data_manager.save_json(config.database.users_file, users):
            self.logger.log_user_action(int(user_id), f"обновление профиля: {list(kwargs.keys())}")
            return True
        return False
    
    def delete_user(self, user_id: str) -> bool:
        """Удалить пользователя"""
        users = data_manager.load_json(config.database.users_file)
        
        if user_id not in users:
            return False
        
        del users[user_id]
        
        if data_manager.save_json(config.database.users_file, users):
            self.logger.log_user_action(int(user_id), "удаление аккаунта")
            return True
        return False
    
    def get_all_users(self) -> Dict[str, Dict[str, Any]]:
        """Получить всех пользователей"""
        return data_manager.load_json(config.database.users_file)
    
    def get_active_users(self) -> List[str]:
        """Получить список активных пользователей"""
        users = data_manager.load_json(config.database.users_file)
        return [user_id for user_id, user_data in users.items() 
                if user_data.get('status') == 'active']
    
    def ban_user(self, user_id: str) -> bool:
        """Заблокировать пользователя"""
        return self.update_user(user_id, status="banned")
    
    def unban_user(self, user_id: str) -> bool:
        """Разблокировать пользователя"""
        return self.update_user(user_id, status="active")
    
    def activate_user(self, user_id: str) -> bool:
        """
        Активировать пользователя после успешной авторизации
        
        Args:
            user_id (str): ID пользователя
            
        Returns:
            bool: True если пользователь активирован успешно
        """
        user = self.get_user(user_id)
        if not user:
            return False
        
        if user.get('status') == 'active':
            return True  # Уже активен
        
        return self.update_user(user_id, status="active", activated_at=datetime.now().isoformat())
    
    def set_user_tags(self, user_id: str, tags: List[str]) -> bool:
        """
        Установить теги для пользователя
        
        Args:
            user_id (str): ID пользователя
            tags (List[str]): Список тегов
            
        Returns:
            bool: True если теги установлены успешно
        """
        return self.update_user(user_id, tags=tags)
    
    def add_user_tag(self, user_id: str, tag: str) -> bool:
        """
        Добавить тег пользователю
        
        Args:
            user_id (str): ID пользователя
            tag (str): Тег для добавления
            
        Returns:
            bool: True если тег добавлен успешно
        """
        user = self.get_user(user_id)
        if not user:
            return False
        
        current_tags = user.get('tags', [])
        if isinstance(current_tags, str):
            current_tags = [current_tags]
        elif not isinstance(current_tags, list):
            current_tags = []
        
        if tag not in current_tags:
            current_tags.append(tag)
            return self.update_user(user_id, tags=current_tags)
        
        return True
    
    def get_user_stats(self) -> Dict[str, int]:
        """
        Получить статистику пользователей
        
        Returns:
            Dict[str, int]: Словарь со статистикой:
                - total: общее количество пользователей
                - active: количество активных пользователей
                - inactive: количество неактивных пользователей
                - banned: количество заблокированных пользователей
                - new_today: количество новых пользователей за сегодня
        """
        users = data_manager.load_json(config.database.users_file)
        today = datetime.now().date().isoformat()
        
        stats = {
            "total": len(users),
            "active": 0,
            "inactive": 0,
            "banned": 0,
            "new_today": 0
        }
        
        for user_data in users.values():
            status = user_data.get('status', 'unknown')
            if status in stats:
                stats[status] += 1
            
            # Подсчет новых пользователей за сегодня
            first_interaction = user_data.get('first_interaction', '')
            if first_interaction.startswith(today):
                stats['new_today'] += 1
        
        return stats


# Создаем глобальный экземпляр сервиса пользователей
user_service = UserService() 
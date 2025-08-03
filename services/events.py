"""
@file: services/events.py
@description: Сервис для работы с событиями
@dependencies: typing, datetime, config, utils
@created: 2024-01-15
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date

from config import config
from utils.data_manager import data_manager
from utils.logger import bot_logger


class EventService:
    """Сервис для работы с событиями"""
    
    def __init__(self):
        self.logger = bot_logger
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Получить событие по ID"""
        events = data_manager.load_json(config.database.events_file)
        return events.get(event_id)
    
    def get_all_events(self) -> Dict[str, Dict[str, Any]]:
        """Получить все события"""
        return data_manager.load_json(config.database.events_file)
    
    def create_event(self, title: str, date_str: str, time_str: str, 
                    description: str = "", book: str = "", participants: List[str] = None) -> str:
        """Создать новое событие"""
        events = data_manager.load_json(config.database.events_file)
        
        # Генерируем уникальный ID
        event_id = f"event_{len(events) + 1:03d}"
        
        event_data = {
            "title": title,
            "date": date_str,
            "time": time_str,
            "description": description,
            "book": book,
            "participants": participants or []
        }
        
        if not data_manager.validate_event_data(event_data):
            self.logger.log_error(Exception("Ошибка валидации данных события"), f"title: {title}")
            return ""
        
        events[event_id] = event_data
        
        if data_manager.save_json(config.database.events_file, events):
            self.logger.log_admin_action(0, f"создание события: {title}")
            return event_id
        return ""
    
    def update_event(self, event_id: str, **kwargs) -> bool:
        """Обновить данные события"""
        events = data_manager.load_json(config.database.events_file)
        
        if event_id not in events:
            return False
        
        events[event_id].update(kwargs)
        
        if data_manager.save_json(config.database.events_file, events):
            self.logger.log_admin_action(0, f"обновление события: {event_id}")
            return True
        return False
    
    def delete_event(self, event_id: str) -> bool:
        """Удалить событие"""
        events = data_manager.load_json(config.database.events_file)
        
        if event_id not in events:
            return False
        
        event_title = events[event_id].get('title', 'Неизвестное событие')
        del events[event_id]
        
        if data_manager.save_json(config.database.events_file, events):
            self.logger.log_admin_action(0, f"удаление события: {event_title}")
            return True
        return False
    
    def add_participant(self, event_id: str, user_id: str) -> bool:
        """Добавить участника к событию"""
        events = data_manager.load_json(config.database.events_file)
        
        if event_id not in events:
            return False
        
        if user_id not in events[event_id].get('participants', []):
            events[event_id]['participants'].append(user_id)
            
            if data_manager.save_json(config.database.events_file, events):
                self.logger.log_user_action(int(user_id), f"присоединение к событию {event_id}")
                return True
        
        return False
    
    def remove_participant(self, event_id: str, user_id: str) -> bool:
        """Удалить участника из события"""
        events = data_manager.load_json(config.database.events_file)
        
        if event_id not in events:
            return False
        
        participants = events[event_id].get('participants', [])
        if user_id in participants:
            participants.remove(user_id)
            events[event_id]['participants'] = participants
            
            if data_manager.save_json(config.database.events_file, events):
                self.logger.log_user_action(int(user_id), f"выход из события {event_id}")
                return True
        
        return False
    
    def get_upcoming_events(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """Получить предстоящие события"""
        events = data_manager.load_json(config.database.events_file)
        today = date.today()
        
        upcoming = {}
        for event_id, event_data in events.items():
            try:
                event_date = datetime.strptime(event_data.get('date', ''), '%Y-%m-%d').date()
                if event_date >= today:
                    upcoming[event_id] = event_data
            except ValueError:
                continue
        
        return upcoming
    
    def get_events_by_book(self, book_title: str) -> Dict[str, Dict[str, Any]]:
        """Получить события по книге"""
        events = data_manager.load_json(config.database.events_file)
        
        book_events = {}
        for event_id, event_data in events.items():
            if event_data.get('book') == book_title:
                book_events[event_id] = event_data
        
        return book_events
    
    def get_user_events(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Получить события пользователя"""
        events = data_manager.load_json(config.database.events_file)
        
        user_events = {}
        for event_id, event_data in events.items():
            if user_id in event_data.get('participants', []):
                user_events[event_id] = event_data
        
        return user_events
    
    def get_event_stats(self) -> Dict[str, int]:
        """Получить статистику событий"""
        events = data_manager.load_json(config.database.events_file)
        
        stats = {
            "total": len(events),
            "upcoming": 0,
            "past": 0
        }
        
        today = date.today()
        for event_data in events.values():
            try:
                event_date = datetime.strptime(event_data.get('date', ''), '%Y-%m-%d').date()
                if event_date >= today:
                    stats["upcoming"] += 1
                else:
                    stats["past"] += 1
            except ValueError:
                continue
        
        return stats


# Создаем глобальный экземпляр сервиса событий
event_service = EventService() 
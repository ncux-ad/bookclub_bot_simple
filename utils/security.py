"""
@file: utils/security.py
@description: Утилиты безопасности с хэшированием и валидацией
@dependencies: hashlib, re, typing, logging
@created: 2024-01-15
"""

import hashlib
import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class SecurityManager:
    """Менеджер безопасности"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._login_attempts: Dict[int, Dict[str, Any]] = {}
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._spam_protection: Dict[int, Dict[str, Any]] = {}
    
    def hash_password(self, password: str) -> str:
        """Хэширование пароля с солью"""
        salt = "bookclub_salt_2024"
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def verify_secret_phrase(self, phrase: str, correct_phrase: str) -> bool:
        """Проверка секретной фразы"""
        return phrase.strip() == correct_phrase.strip()
    
    def validate_user_input(self, text: str, max_length: int = 1000) -> bool:
        """Валидация пользовательского ввода"""
        if not text or len(text) > max_length:
            return False
        
        # Проверка на потенциально опасные символы
        dangerous_patterns = [
            r'<script.*?>',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
            r'onload=',
            r'onerror='
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                self.logger.warning(f"Обнаружен потенциально опасный ввод: {text[:50]}...")
                return False
        
        return True
    
    def sanitize_filename(self, filename: str) -> str:
        """Очистка имени файла от опасных символов"""
        # Удаляем опасные символы
        dangerous_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(dangerous_chars, '_', filename)
        
        # Ограничиваем длину
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            sanitized = name[:255-len(ext)-1] + ('.' + ext if ext else '')
        
        return sanitized
    
    def check_login_attempts(self, user_id: int, max_attempts: int = 3, 
                           lockout_duration: int = 900) -> bool:
        """Проверка попыток входа с блокировкой"""
        now = datetime.now()
        
        if user_id not in self._login_attempts:
            return True
        
        attempts = self._login_attempts[user_id]
        
        # Проверяем, не истекла ли блокировка
        if 'locked_until' in attempts:
            if now < attempts['locked_until']:
                remaining = (attempts['locked_until'] - now).seconds
                self.logger.warning(f"Пользователь {user_id} заблокирован еще на {remaining} секунд")
                return False
            else:
                # Блокировка истекла, сбрасываем
                del attempts['locked_until']
        
        # Проверяем количество попыток
        if attempts.get('count', 0) >= max_attempts:
            # Блокируем пользователя
            attempts['locked_until'] = now + timedelta(seconds=lockout_duration)
            self.logger.warning(f"Пользователь {user_id} заблокирован на {lockout_duration} секунд")
            return False
        
        return True
    
    def record_login_attempt(self, user_id: int, success: bool) -> None:
        """Запись попытки входа"""
        if user_id not in self._login_attempts:
            self._login_attempts[user_id] = {'count': 0, 'last_attempt': None}
        
        attempts = self._login_attempts[user_id]
        
        if success:
            # Успешный вход, сбрасываем счетчик
            attempts['count'] = 0
            if 'locked_until' in attempts:
                del attempts['locked_until']
        else:
            # Неудачная попытка
            attempts['count'] = attempts.get('count', 0) + 1
        
        attempts['last_attempt'] = datetime.now()
    
    def create_session(self, user_id: int, duration: int = 3600) -> str:
        """Создание сессии пользователя"""
        session_id = hashlib.sha256(f"{user_id}_{datetime.now()}".encode()).hexdigest()
        
        self._sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=duration)
        }
        
        self.logger.info(f"Создана сессия {session_id} для пользователя {user_id}")
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[int]:
        """Проверка валидности сессии"""
        if session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]
        
        if datetime.now() > session['expires_at']:
            # Сессия истекла
            del self._sessions[session_id]
            return None
        
        return session['user_id']
    
    def cleanup_expired_sessions(self) -> None:
        """Очистка истекших сессий"""
        now = datetime.now()
        expired_sessions = [
            session_id for session_id, session in self._sessions.items()
            if now > session['expires_at']
        ]
        
        for session_id in expired_sessions:
            del self._sessions[session_id]
        
        if expired_sessions:
            self.logger.info(f"Очищено {len(expired_sessions)} истекших сессий")
    
    def check_spam_protection(self, user_id: int, user_status: str = "unknown") -> bool:
        """
        Проверка защиты от спама для заблокированных пользователей
        
        Args:
            user_id (int): ID пользователя
            user_status (str): Статус пользователя
            
        Returns:
            bool: True если сообщение разрешено, False если заблокировано
        """
        # Для заблокированных пользователей применяем строгие ограничения
        if user_status == "banned":
            return self._check_banned_user_spam(user_id)
        
        return True
    
    def _check_banned_user_spam(self, user_id: int) -> bool:
        """
        Проверка спама для заблокированных пользователей
        
        Args:
            user_id (int): ID пользователя
            
        Returns:
            bool: True если сообщение разрешено, False если заблокировано
        """
        now = datetime.now()
        
        if user_id not in self._spam_protection:
            self._spam_protection[user_id] = {
                'message_count': 0,
                'first_message': now,
                'last_message': now,
                'blocked_until': None
            }
        
        protection = self._spam_protection[user_id]
        
        # Проверяем, не заблокирован ли пользователь
        if protection.get('blocked_until') and now < protection['blocked_until']:
            remaining = (protection['blocked_until'] - now).seconds
            self.logger.warning(f"Заблокированный пользователь {user_id} пытается отправить сообщение. Блокировка еще на {remaining} секунд")
            return False
        
        # Сбрасываем блокировку если истекла
        if protection.get('blocked_until') and now >= protection['blocked_until']:
            protection['blocked_until'] = None
            protection['message_count'] = 0
            protection['first_message'] = now
        
        # Ограничения для заблокированных пользователей:
        # - Максимум 3 сообщения в минуту
        # - Максимум 10 сообщений в час
        # - Максимум 30 сообщений в день
        
        time_diff = (now - protection['first_message']).total_seconds()
        
        # Проверка лимита в минуту
        if time_diff <= 60:  # В течение минуты
            if protection['message_count'] >= 3:
                protection['blocked_until'] = now + timedelta(minutes=5)
                self.logger.warning(f"Заблокированный пользователь {user_id} превысил лимит сообщений в минуту. Блокировка на 5 минут")
                return False
        
        # Проверка лимита в час
        elif time_diff <= 3600:  # В течение часа
            if protection['message_count'] >= 10:
                protection['blocked_until'] = now + timedelta(hours=1)
                self.logger.warning(f"Заблокированный пользователь {user_id} превысил лимит сообщений в час. Блокировка на 1 час")
                return False
        
        # Проверка лимита в день
        elif time_diff <= 86400:  # В течение дня
            if protection['message_count'] >= 30:
                protection['blocked_until'] = now + timedelta(hours=6)
                self.logger.warning(f"Заблокированный пользователь {user_id} превысил лимит сообщений в день. Блокировка на 6 часов")
                return False
        
        # Если прошло больше дня, сбрасываем счетчик
        else:
            protection['message_count'] = 0
            protection['first_message'] = now
        
        # Увеличиваем счетчик сообщений
        protection['message_count'] += 1
        protection['last_message'] = now
        
        return True
    
    def record_banned_user_message(self, user_id: int) -> None:
        """
        Запись сообщения от заблокированного пользователя
        
        Args:
            user_id (int): ID пользователя
        """
        if user_id not in self._spam_protection:
            self._spam_protection[user_id] = {
                'message_count': 0,
                'first_message': datetime.now(),
                'last_message': datetime.now(),
                'blocked_until': None
            }
        
        protection = self._spam_protection[user_id]
        protection['message_count'] += 1
        protection['last_message'] = datetime.now()
        
        self.logger.info(f"Заблокированный пользователь {user_id} отправил сообщение (всего: {protection['message_count']})")
    
    def get_spam_protection_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Получить статистику защиты от спама для пользователя
        
        Args:
            user_id (int): ID пользователя
            
        Returns:
            Dict[str, Any]: Статистика защиты от спама
        """
        if user_id not in self._spam_protection:
            return {
                'message_count': 0,
                'is_blocked': False,
                'blocked_until': None,
                'remaining_time': 0
            }
        
        protection = self._spam_protection[user_id]
        now = datetime.now()
        
        is_blocked = False
        remaining_time = 0
        
        if protection.get('blocked_until') and now < protection['blocked_until']:
            is_blocked = True
            remaining_time = (protection['blocked_until'] - now).seconds
        
        return {
            'message_count': protection['message_count'],
            'is_blocked': is_blocked,
            'blocked_until': protection.get('blocked_until'),
            'remaining_time': remaining_time
        }


# Создаем глобальный экземпляр менеджера безопасности
security_manager = SecurityManager() 
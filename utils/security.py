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


# Создаем глобальный экземпляр менеджера безопасности
security_manager = SecurityManager() 
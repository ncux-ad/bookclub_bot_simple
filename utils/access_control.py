"""
@file: utils/access_control.py
@description: Система контроля доступа для команд бота
@dependencies: config, services.users, utils.logger
@created: 2025-01-03
"""

from functools import wraps
from typing import Callable, Any
from aiogram.types import Message

from config import config
from services.users import user_service
from utils.logger import bot_logger


def active_user_required(func: Callable) -> Callable:
    """
    Декоратор для проверки активного статуса пользователя
    
    Проверяет, имеет ли пользователь статус 'active'.
    Если нет - отправляет сообщение о необходимости регистрации.
    
    Args:
        func: Функция-обработчик для защиты
        
    Returns:
        wrapper: Обернутая функция с проверкой статуса
    """
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs) -> Any:
        user_id = str(message.from_user.id)
        user_info = user_service.get_user(user_id)
        
        if not user_info:
            await message.answer(
                "❌ Вы не зарегистрированы в системе.\n"
                "Используйте /register для регистрации."
            )
            return
        
        if user_info.get('status') != 'active':
            await message.answer(
                "❌ Ваш аккаунт не активирован.\n"
                "Используйте /register для активации."
            )
            return
        
        return await func(message, *args, **kwargs)
    return wrapper


def admin_required(func: Callable) -> Callable:
    """
    Декоратор для проверки прав администратора
    
    Проверяет, имеет ли пользователь права администратора.
    Если нет - отправляет сообщение об ошибке и логирует попытку доступа.
    
    Args:
        func: Функция-обработчик для защиты
        
    Returns:
        wrapper: Обернутая функция с проверкой прав
    """
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs) -> Any:
        if not config.is_admin(message.from_user.id):
            bot_logger.log_security_event(
                "неавторизованный_доступ", 
                message.from_user.id, 
                f"админская команда: {func.__name__}"
            )
            await message.answer("❌ У вас нет прав администратора!")
            return
        return await func(message, *args, **kwargs)
    return wrapper


def get_user_status(user_id: int) -> str:
    """
    Получить статус пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        str: Статус пользователя ('active', 'inactive', 'banned', 'unknown')
    """
    user_info = user_service.get_user(str(user_id))
    if not user_info:
        return 'unknown'
    return user_info.get('status', 'unknown')


def is_user_active(user_id: int) -> bool:
    """
    Проверить, активен ли пользователь
    
    Args:
        user_id: ID пользователя
        
    Returns:
        bool: True если пользователь активен, False иначе
    """
    return get_user_status(user_id) == 'active'


def is_user_admin(user_id: int) -> bool:
    """
    Проверить, является ли пользователь администратором
    
    Проверяет как статические админы из config, так и динамические админы по роли
    
    Args:
        user_id: ID пользователя
        
    Returns:
        bool: True если пользователь админ, False иначе
    """
    # Проверяем статических админов из config
    if config.is_admin(user_id):
        return True
    
    # Проверяем динамическую роль из базы данных
    user_info = user_service.get_user(str(user_id))
    if user_info and user_info.get('role') == 'admin':
        return True
    
    return False


def is_user_moderator(user_id: int) -> bool:
    """
    Проверить, является ли пользователь модератором
    
    Args:
        user_id: ID пользователя
        
    Returns:
        bool: True если пользователь модератор, False иначе
    """
    user_info = user_service.get_user(str(user_id))
    if not user_info:
        return False
    role = user_info.get('role', 'user')
    return role in ['moderator', 'admin']


def get_user_role(user_id: int) -> str:
    """
    Получить роль пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        str: Роль пользователя ('user', 'moderator', 'admin')
    """
    user_info = user_service.get_user(str(user_id))
    if not user_info:
        return 'user'
    return user_info.get('role', 'user')


def get_available_commands(user_id: int) -> list[str]:
    """
    Получить список доступных команд для пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        list[str]: Список доступных команд
    """
    status = get_user_status(user_id)
    role = get_user_role(user_id)
    is_admin = is_user_admin(user_id)
    
    # Базовые команды для всех
    commands = ['/start', '/help']
    
    # Команды для неактивных пользователей
    if status == 'inactive':
        commands.append('/register')
        return commands
    
    # Команды для заблокированных пользователей
    if status == 'banned':
        return commands  # Только базовые команды
    
    # Команды для активных пользователей
    if status == 'active':
        commands.extend([
            '/profile',
            '/books', 
            '/search',
            '/schedule',
            '/cancel'
        ])
    
    # Команды для модераторов
    if role in ['moderator', 'admin']:
        commands.extend([
            '/ban',
            '/unban',
            '/userinfo',
            '/stats',
            '/users'
        ])
    
    # Админские команды (для статических админов из config и динамических админов по роли)
    if is_admin:
        commands.extend([
            '/admin',
            '/settag',
            '/setrole',
            '/spamstats'
        ])
    
    return commands 
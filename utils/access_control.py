"""
@file: utils/access_control.py
@description: Система контроля доступа
@dependencies: services.users, functools
@created: 2025-01-03
"""

from functools import wraps
from typing import Callable, Any, Awaitable

from services.users import user_service
from utils.logger import bot_logger


def active_user_required(func: Callable) -> Callable:
    """
    Декоратор для проверки активности пользователя
    
    Проверяет, что пользователь имеет статус 'active'
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # Ищем объект Message в аргументах
        message = None
        for arg in args:
            if hasattr(arg, 'from_user') and hasattr(arg.from_user, 'id'):
                message = arg
                break
        
        if not message:
            return await func(*args, **kwargs)
        
        user_id = str(message.from_user.id)
        user_info = user_service.get_user(user_id)
        
        if not user_info or user_info.get('status') != 'active':
            await message.answer(
                "🚫 У вас нет доступа к этой команде.\n"
                "Необходимо пройти регистрацию: /register"
            )
            bot_logger.log_security_event("попытка_доступа_неактивного_пользователя", message.from_user.id)
            return
        
        return await func(*args, **kwargs)
    
    return wrapper


def admin_required(func: Callable) -> Callable:
    """
    Декоратор для проверки прав администратора
    
    Проверяет, что пользователь является администратором
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # Ищем объект Message в аргументах
        message = None
        for arg in args:
            if hasattr(arg, 'from_user') and hasattr(arg.from_user, 'id'):
                message = arg
                break
        
        if not message:
            return await func(*args, **kwargs)
        
        user_id = str(message.from_user.id)
        user_info = user_service.get_user(user_id)
        
        if not user_info or user_info.get('status') != 'active':
            await message.answer(
                "🚫 У вас нет доступа к этой команде.\n"
                "Необходимо пройти регистрацию: /register"
            )
            bot_logger.log_security_event("попытка_доступа_неактивного_пользователя", message.from_user.id)
            return
        
        # Проверяем, является ли пользователь администратором
        if str(message.from_user.id) not in user_service.get_admin_ids():
            await message.answer(
                "🚫 У вас нет прав администратора для выполнения этой команды."
            )
            bot_logger.log_security_event("попытка_доступа_неадмина", message.from_user.id)
            return
        
        return await func(*args, **kwargs)
    
    return wrapper


def get_user_status(user_id: int) -> str:
    """
    Получить статус пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        str: Статус пользователя
    """
    user_info = user_service.get_user(str(user_id))
    return user_info.get('status', 'unknown') if user_info else 'unknown'


def is_user_active(user_id: int) -> bool:
    """
    Проверить, активен ли пользователь
    
    Args:
        user_id: ID пользователя
        
    Returns:
        bool: True если пользователь активен
    """
    return get_user_status(user_id) == 'active'


def is_user_admin(user_id: int) -> bool:
    """
    Проверить, является ли пользователь администратором
    
    Args:
        user_id: ID пользователя
        
    Returns:
        bool: True если пользователь администратор
    """
    return str(user_id) in user_service.get_admin_ids()


def get_available_commands(user_id: int) -> list[str]:
    """
    Получить список доступных команд для пользователя
    
    Args:
        user_id: ID пользователя
        
    Returns:
        list[str]: Список доступных команд
    """
    commands = ['/start', '/help']
    status = get_user_status(user_id)
    
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
            '/search',
            '/schedule'
        ])
        
        # Админские команды
        if is_user_admin(user_id):
            commands.extend([
                '/admin',
                '/ban',
                '/unban',
                '/userinfo',
                '/users',
                '/stats',
                '/spamstats',
                '/addbook'
            ])
    
    return commands 
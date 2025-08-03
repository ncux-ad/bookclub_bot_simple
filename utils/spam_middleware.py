"""
@file: utils/spam_middleware.py
@description: Middleware для защиты от спама заблокированных пользователей
@dependencies: aiogram, services.users, utils.security, utils.logger
@created: 2025-01-03
"""

from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from services.users import user_service
from utils.security import security_manager
from utils.logger import bot_logger


class SpamProtectionMiddleware(BaseMiddleware):
    """
    Middleware для защиты от спама заблокированных пользователей
    
    Автоматически проверяет и ограничивает активность заблокированных пользователей
    для предотвращения DDoS атак и спама.
    """
    
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any]
    ) -> Any:
        """
        Обработка события с проверкой спама
        
        Args:
            handler: Обработчик события
            event: Событие (Message или CallbackQuery)
            data: Данные события
            
        Returns:
            Any: Результат обработки
        """
        # Получаем user_id из события
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            # Для других типов событий пропускаем
            return await handler(event, data)
        
        # Получаем статус пользователя
        user_info = user_service.get_user(str(user_id))
        user_status = user_info.get('status', 'unknown') if user_info else 'unknown'
        
        # Проверяем защиту от спама
        if not security_manager.check_spam_protection(user_id, user_status):
            # Пользователь заблокирован за спам
            bot_logger.log_security_event("спам_блокировка", user_id, f"статус: {user_status}")
            
            # Отправляем сообщение о блокировке (только для Message)
            if isinstance(event, Message):
                await event.answer(
                    "🚫 Ваша активность ограничена из-за превышения лимитов.\n"
                    "Попробуйте позже."
                )
            
            # Не обрабатываем событие дальше
            return
        
        # Если пользователь заблокирован, записываем сообщение для статистики
        if user_status == "banned":
            security_manager.record_banned_user_message(user_id)
        
        # Продолжаем обработку события
        return await handler(event, data) 
"""
@file: handlers/unknown_handlers.py
@description: Обработчики неизвестных команд
@dependencies: aiogram, utils.logger
@created: 2025-01-03
"""

from aiogram import Router
from aiogram.types import Message

from utils.logger import bot_logger

router = Router()


@router.message()
async def unknown_command(message: Message) -> None:
    """
    Обработчик неизвестных команд
    
    Отправляет пользователю сообщение с предложением посмотреть /help
    при получении неизвестной команды.
    
    Args:
        message (Message): Сообщение с неизвестной командой
        
    Returns:
        None
    """
    bot_logger.log_user_action(message.from_user.id, f"неизвестная команда: {message.text}")
    
    await message.answer(
        "❓ Неизвестная команда.\n"
        "Используйте /help для просмотра доступных команд."
    ) 
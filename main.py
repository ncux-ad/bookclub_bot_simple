"""
@file: main.py
@description: Главный файл приложения с модульной архитектурой
@dependencies: aiogram, config, utils, handlers, services
@created: 2024-01-15
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from utils.logger import setup_logging, bot_logger
from handlers import user_router, admin_router


async def main() -> None:
    """
    Главная функция приложения
    
    Инициализирует и запускает бота с полной валидацией конфигурации.
    Включает настройку логирования, обработку ошибок и graceful shutdown.
    
    Returns:
        None
    """
    # Настройка логирования
    setup_logging(
        log_file=config.logging.file,
        log_level=config.logging.level
    )
    
    bot_logger.logger.info("🚀 Запуск BookClub Bot...")
    
    # Инициализация бота и диспетчера
    bot = Bot(token=config.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация роутеров
    dp.include_router(user_router)
    dp.include_router(admin_router)
    
    # Обработка ошибок
    @dp.error()
    async def error_handler(update, exception):
        """
        Обработчик ошибок
        
        Логирует все ошибки, возникающие в процессе работы бота.
        
        Args:
            update: Объект обновления от Telegram
            exception: Исключение, которое произошло
            
        Returns:
            None
        """
        bot_logger.log_error(exception, f"update: {update}")
    
    try:
        bot_logger.logger.info("✅ Бот успешно запущен")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        bot_logger.logger.info("⏹️ Бот остановлен пользователем")
    except Exception as e:
        bot_logger.log_error(e, "критическая ошибка при запуске бота")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main()) 
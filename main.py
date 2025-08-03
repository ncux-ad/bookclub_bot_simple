"""
@file: main.py
@description: Главный файл бота
@dependencies: aiogram, config, utils.logger, handlers
@created: 2025-01-03
"""

# Загружаем переменные окружения ПЕРЕД всеми импортами
from dotenv import load_dotenv
load_dotenv()

import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from utils.logger import bot_logger
from handlers import user_router, admin_router, unknown_router, book_router
from utils.spam_middleware import SpamProtectionMiddleware

# Глобальные переменные для graceful shutdown
bot_instance = None
dp_instance = None


async def error_handler(exception: Exception):
    """Глобальный обработчик ошибок"""
    bot_logger.logger.error(f"Необработанная ошибка: {exception}")
    return True


async def on_shutdown():
    """Обработчик завершения работы"""
    bot_logger.logger.info("🔄 Начинаем graceful shutdown...")
    
    try:
        if bot_instance and not bot_instance.session.closed:
            await bot_instance.session.close()
            bot_logger.logger.info("✅ Сессия бота закрыта")
    except Exception as e:
        bot_logger.logger.error(f"Ошибка закрытия сессии бота: {e}")
    
    try:
        if dp_instance and not dp_instance.storage.is_closed():
            await dp_instance.storage.close()
            bot_logger.logger.info("✅ Storage закрыт")
    except Exception as e:
        bot_logger.logger.error(f"Ошибка закрытия storage: {e}")
    
    bot_logger.logger.info("✅ Graceful shutdown завершен")


async def main() -> None:
    """Основная функция"""
    global bot_instance, dp_instance
    
    bot_logger.logger.info("🚀 Запуск BookClub Bot...")
    
    # Инициализация бота и диспетчера
    bot_instance = Bot(token=config.bot.token)
    storage = MemoryStorage()
    dp_instance = Dispatcher(storage=storage)
    
    # Регистрация middleware для защиты от спама
    dp_instance.message.middleware(SpamProtectionMiddleware())
    dp_instance.callback_query.middleware(SpamProtectionMiddleware())
    
    # Регистрация роутеров
    # Сначала админские команды (более специфичные)
    dp_instance.include_router(admin_router)
    # Затем пользовательские команды
    dp_instance.include_router(user_router)
    # Затем обработчики книг
    dp_instance.include_router(book_router)
    # В последнюю очередь обработчик неизвестных команд
    dp_instance.include_router(unknown_router)
    
    # Регистрация обработчиков
    dp_instance.error.register(error_handler)
    dp_instance.shutdown.register(on_shutdown)
    
    bot_logger.logger.info("✅ Бот успешно запущен")
    
    try:
        await dp_instance.start_polling(bot_instance)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        bot_logger.logger.error(f"Ошибка в main: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        bot_logger.logger.info("⏹️ Бот остановлен пользователем")
    except asyncio.CancelledError:
        pass
    except Exception as e:
        bot_logger.logger.error(f"Критическая ошибка: {e}")
        sys.exit(1) 
"""
@file: main.py
@description: Главный файл приложения с модульной архитектурой
@dependencies: aiogram, config, utils, handlers, services
@created: 2024-01-15
"""

import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Загружаем переменные окружения
load_dotenv()

from config import config
from utils.logger import setup_logging, bot_logger
from handlers import user_router, admin_router

# Глобальные переменные для управления состоянием
bot_instance = None
dp_instance = None


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
    global bot_instance, dp_instance
    bot_instance = Bot(token=config.bot_token)
    storage = MemoryStorage()
    dp_instance = Dispatcher(storage=storage)
    
    # Регистрация роутеров
    dp_instance.include_router(user_router)
    dp_instance.include_router(admin_router)
    
    # Обработка ошибок
    @dp_instance.error()
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
        return True
    
    # Обработка graceful shutdown
    async def on_shutdown():
        """
        Обработчик graceful shutdown
        
        Корректно завершает работу бота, закрывая все соединения
        и сохраняя состояние.
        """
        bot_logger.logger.info("🔄 Начинаем graceful shutdown...")
        
        try:
            # Закрываем сессию бота
            if bot_instance:
                try:
                    if hasattr(bot_instance.session, 'closed') and not bot_instance.session.closed:
                        await bot_instance.session.close()
                        bot_logger.logger.info("✅ Сессия бота закрыта")
                    elif not hasattr(bot_instance.session, 'closed'):
                        await bot_instance.session.close()
                        bot_logger.logger.info("✅ Сессия бота закрыта")
                except Exception as e:
                    bot_logger.log_error(e, "ошибка при закрытии сессии бота")
            
            # Сохраняем состояние storage
            try:
                if hasattr(storage, 'is_closed') and not storage.is_closed():
                    await storage.close()
                    bot_logger.logger.info("✅ Storage закрыт")
                elif not hasattr(storage, 'is_closed'):
                    await storage.close()
                    bot_logger.logger.info("✅ Storage закрыт")
            except Exception as e:
                bot_logger.log_error(e, "ошибка при закрытии storage")
            
        except Exception as e:
            bot_logger.log_error(e, "ошибка при graceful shutdown")
        finally:
            bot_logger.logger.info("✅ Graceful shutdown завершен")
    
    # Устанавливаем обработчик shutdown
    dp_instance.shutdown.register(on_shutdown)
    
    try:
        bot_logger.logger.info("✅ Бот успешно запущен")
        
        # Запускаем polling
        await dp_instance.start_polling(bot_instance, skip_updates=True)
        
    except KeyboardInterrupt:
        bot_logger.logger.info("⏹️ Получен сигнал прерывания (Ctrl+C)")
        # Graceful shutdown будет вызван автоматически aiogram
    except asyncio.CancelledError:
        # Игнорируем CancelledError после graceful shutdown
        pass
    except Exception as e:
        bot_logger.log_error(e, "критическая ошибка при запуске бота")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Игнорируем KeyboardInterrupt на верхнем уровне
        pass
    except asyncio.CancelledError:
        # Игнорируем CancelledError на верхнем уровне
        pass 
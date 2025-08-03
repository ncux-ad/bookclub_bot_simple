"""
@file: main.py
@description: Главный файл приложения с модульной архитектурой
@dependencies: aiogram, config, utils, handlers, services
@created: 2024-01-15
"""

import asyncio
import logging
import signal
import sys
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
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    """
    Обработчик сигналов для graceful shutdown
    
    Args:
        signum: Номер сигнала
        frame: Текущий кадр стека
    """
    bot_logger.logger.info(f"📡 Получен сигнал {signum}")
    shutdown_event.set()

# Регистрируем обработчики сигналов
if sys.platform != "win32":  # На Windows сигналы работают по-другому
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # SIGTERM


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
            # Останавливаем polling
            if dp_instance:
                await dp_instance.stop_polling()
                bot_logger.logger.info("✅ Polling остановлен")
            
            # Закрываем сессию бота
            if bot_instance:
                await bot_instance.session.close()
                bot_logger.logger.info("✅ Сессия бота закрыта")
            
            # Сохраняем состояние storage
            await storage.close()
            bot_logger.logger.info("✅ Storage закрыт")
            
        except Exception as e:
            bot_logger.log_error(e, "ошибка при graceful shutdown")
        finally:
            bot_logger.logger.info("✅ Graceful shutdown завершен")
    
    # Устанавливаем обработчик shutdown
    dp_instance.shutdown.register(on_shutdown)
    
    try:
        bot_logger.logger.info("✅ Бот успешно запущен")
        
        # Запускаем polling с мониторингом сигналов
        polling_task = asyncio.create_task(
            dp_instance.start_polling(bot_instance, skip_updates=True)
        )
        
        # На Windows используем простой await, на Unix - мониторинг сигналов
        if sys.platform == "win32":
            await polling_task
        else:
            # Ждем либо завершения polling, либо сигнала shutdown
            await asyncio.wait(
                [polling_task, shutdown_event.wait()],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Если получен сигнал shutdown, останавливаем polling
            if shutdown_event.is_set():
                bot_logger.logger.info("⏹️ Получен сигнал завершения работы")
                polling_task.cancel()
                try:
                    await polling_task
                except asyncio.CancelledError:
                    pass
        
    except KeyboardInterrupt:
        bot_logger.logger.info("⏹️ Получен сигнал прерывания (Ctrl+C)")
    except Exception as e:
        bot_logger.log_error(e, "критическая ошибка при запуске бота")
    finally:
        await on_shutdown()


if __name__ == "__main__":
    asyncio.run(main()) 
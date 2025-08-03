"""
@file: test_shutdown.py
@description: Тестовый скрипт для проверки graceful shutdown
@dependencies: asyncio, signal, sys
@created: 2024-01-15
"""

import asyncio
import signal
import sys
import time


async def test_shutdown():
    """Тестирование graceful shutdown"""
    print("🚀 Запуск тестового процесса...")
    
    # Создаем событие для shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler(signum, frame):
        """Обработчик сигналов"""
        print(f"📡 Получен сигнал {signum}")
        shutdown_event.set()
    
    # Регистрируем обработчики сигналов
    if sys.platform != "win32":
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def long_running_task():
        """Долго выполняющаяся задача"""
        i = 0
        while not shutdown_event.is_set():
            print(f"⏱️ Выполняется задача {i}")
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                print("⏹️ Задача отменена")
                break
            i += 1
            if i > 10:  # Ограничиваем для теста
                break
    
    async def graceful_shutdown():
        """Graceful shutdown"""
        print("🔄 Начинаем graceful shutdown...")
        
        # Имитируем закрытие ресурсов
        await asyncio.sleep(0.5)
        print("✅ Ресурсы закрыты")
        
        # Имитируем сохранение состояния
        await asyncio.sleep(0.5)
        print("✅ Состояние сохранено")
        
        print("✅ Graceful shutdown завершен")
    
    try:
        # Запускаем основную задачу
        task = asyncio.create_task(long_running_task())
        
        # На Windows используем простой await
        if sys.platform == "win32":
            await task
        else:
            # Ждем либо завершения задачи, либо сигнала
            await asyncio.wait(
                [task, shutdown_event.wait()],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            if shutdown_event.is_set():
                print("⏹️ Получен сигнал завершения")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
    except KeyboardInterrupt:
        print("⏹️ Получен KeyboardInterrupt")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await graceful_shutdown()


if __name__ == "__main__":
    print("🧪 Тестирование graceful shutdown")
    print("Нажмите Ctrl+C для тестирования graceful shutdown")
    asyncio.run(test_shutdown()) 
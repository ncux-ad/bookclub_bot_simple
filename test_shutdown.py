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
    
    async def long_running_task():
        """Долго выполняющаяся задача"""
        i = 0
        while i < 10:  # Ограничиваем для теста
            print(f"⏱️ Выполняется задача {i}")
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                print("⏹️ Задача отменена")
                break
            i += 1
    
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
        await long_running_task()
        
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
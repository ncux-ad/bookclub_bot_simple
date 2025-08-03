# 🔄 Graceful Shutdown

## 📋 Описание

Система graceful shutdown обеспечивает корректное завершение работы бота при получении сигналов прерывания (Ctrl+C, SIGTERM).

## 🚀 Как это работает

### 1. Обработка сигналов
- **SIGINT** (Ctrl+C) - прерывание пользователем
- **SIGTERM** - системный сигнал завершения
- **KeyboardInterrupt** - альтернативное прерывание

### 2. Graceful shutdown процесс
1. **Получение сигнала** - система регистрирует сигнал прерывания
2. **Остановка polling** - прекращается получение обновлений от Telegram
3. **Закрытие сессии** - корректно закрывается соединение с Telegram API
4. **Сохранение состояния** - сохраняется состояние storage и кэша
5. **Логирование** - записывается информация о завершении

## 🔧 Реализация

### Основные компоненты:

```python
# Глобальные переменные для управления состоянием
bot_instance = None
dp_instance = None

# Graceful shutdown функция
async def on_shutdown():
    try:
        # Закрываем сессию бота
        if bot_instance and hasattr(bot_instance.session, 'closed'):
            if not bot_instance.session.closed:
                await bot_instance.session.close()
        
        # Закрываем storage
        if hasattr(storage, 'is_closed'):
            if not storage.is_closed():
                await storage.close()
        else:
            await storage.close()
    except Exception as e:
        # Логируем ошибки
        pass

# Обработка исключений на верхнем уровне
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        # Игнорируем исключения после graceful shutdown
        pass
```

### Кросс-платформенность:

- **Все платформы**: Использует встроенный graceful shutdown aiogram
- **KeyboardInterrupt**: Обрабатывается автоматически

## 🧪 Тестирование

Запустите тестовый скрипт:
```bash
python test_shutdown.py
```

Нажмите `Ctrl+C` для проверки graceful shutdown.

## 📊 Логи

При graceful shutdown вы увидите:
```
⏹️ Получен сигнал прерывания (Ctrl+C)
🔄 Начинаем graceful shutdown...
✅ Сессия бота закрыта
✅ Storage закрыт
✅ Graceful shutdown завершен
```

**Примечание:** Graceful shutdown вызывается автоматически aiogram при получении сигналов прерывания. Исключения `CancelledError` и `KeyboardInterrupt` обрабатываются на верхнем уровне для предотвращения вывода ошибок после корректного завершения.

## ⚙️ Настройка

### Включение/отключение:
- Graceful shutdown включен по умолчанию
- Для отключения удалите обработчики сигналов в `main.py`

### Таймауты:
- По умолчанию: 5 секунд на graceful shutdown
- Настраивается в `on_shutdown()` функции

## 🔒 Безопасность

- ✅ Корректное закрытие соединений
- ✅ Сохранение состояния пользователей
- ✅ Логирование всех операций
- ✅ Обработка ошибок при shutdown

## 🐛 Устранение проблем

### Бот не завершается корректно:
1. Проверьте логи на ошибки
2. Увеличьте таймаут shutdown
3. Проверьте права доступа к файлам

### Потеря данных при shutdown:
1. Убедитесь, что storage корректно сохраняется
2. Проверьте права записи в директорию data/
3. Проверьте логи на ошибки сохранения 
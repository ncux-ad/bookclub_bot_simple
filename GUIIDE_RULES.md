# 📚 Комплексный гайд по созданию Telegram ботов с библиотекой книг

## 🎯 Основные принципы архитектуры

### 1. Модульная структура проекта
```
project/
├── handlers/          # Обработчики команд
├── services/          # Бизнес-логика
├── utils/            # Утилиты и хелперы
├── keyboards/        # Клавиатуры
├── data/            # JSON файлы данных
├── temp/            # Временные файлы
├── logs/            # Логи
└── config.py        # Конфигурация
```

### 2. SOLID принципы
- **Single Responsibility**: Каждый модуль отвечает за одну задачу
- **Open/Closed**: Расширяемость без изменения существующего кода
- **Liskov Substitution**: Заменяемость компонентов
- **Interface Segregation**: Разделение интерфейсов
- **Dependency Inversion**: Зависимость от абстракций

## 🔧 Критические моменты и их решения

### 1. Проблема: BUTTON_DATA_INVALID
**Причина**: Telegram ограничивает callback_data 64 байтами
**Решение**: Использовать MD5 хеш названий
```python
def safe_encode_title(title: str) -> str:
    return hashlib.md5(title.encode('utf-8')).hexdigest()[:16]

def safe_decode_title(encoded_title: str) -> str:
    books = book_service.get_all_books()
    for title in books.keys():
        if safe_encode_title(title) == encoded_title:
            return title
    return encoded_title
```

### 2. Проблема: Отправка файлов
**Причина**: `Path(file_path)` не работает с aiogram
**Решение**: Использовать `FSInputFile`
```python
from aiogram.types import FSInputFile

await bot.send_document(
    chat_id=user_id,
    document=FSInputFile(file_path),
    caption=f"📚 {title} ({format_type.upper()})"
)
```

### 3. Проблема: Мультиплатформенность
**Причина**: Разные пути в Windows/Linux
**Решение**: Автоопределение ОС и путей
```python
import platform
is_windows = platform.system() == "Windows"

# Пути для Calibre
if is_windows:
    portable_paths = ["./calibre-portable/ebook-convert.exe"]
    system_paths = ["C:\\Program Files\\Calibre2\\ebook-convert.exe"]
else:
    portable_paths = ["./calibre-portable/ebook-convert"]
    system_paths = ["/usr/bin/ebook-convert"]
```

## ��️ Безопасность и валидация

### 1. Переменные окружения
```python
# utils/env_validator.py
class EnvValidator:
    @staticmethod
    def validate_required_vars():
        required = ['BOT_TOKEN', 'SECRET_PHRASE', 'ADMIN_IDS']
        missing = []
        for var in required:
            if not os.getenv(var):
                missing.append(var)
        return missing
```

### 2. Контроль доступа
```python
# utils/access_control.py
def admin_required(func):
    async def wrapper(message: Message, *args, **kwargs):
        user_id = message.from_user.id
        if not user_service.is_admin(user_id):
            await message.answer("❌ Доступ запрещен!")
            return
        return await func(message, *args, **kwargs)
    return wrapper
```

### 3. Защита от спама
```python
# utils/spam_middleware.py
class SpamProtectionMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: int = 5, window: int = 60):
        self.rate_limit = rate_limit
        self.window = window
        self.user_requests = {}
```

## �� Управление данными

### 1. Кэширование и валидация
```python
# utils/data_manager.py
class DataManager:
    def __init__(self):
        self._cache = {}
        self._cache_timestamps = {}
    
    def get_json(self, file_path: str) -> Dict:
        # Проверяем кэш
        if file_path in self._cache:
            if time.time() - self._cache_timestamps[file_path] < 30:
                return self._cache[file_path]
        
        # Загружаем из файла
        data = self._load_json(file_path)
        self._cache[file_path] = data
        self._cache_timestamps[file_path] = time.time()
        return data
```

### 2. Миграции данных
```python
# services/users.py
def migrate_user_roles():
    """Миграция ролей пользователей"""
    users = user_service.get_all_users()
    updated = False
    
    for user_id, user_data in users.items():
        if 'role' not in user_data:
            user_data['role'] = 'user'
            updated = True
    
    if updated:
        data_manager.save_json(config.database.users_file, users)
```

## 🔄 FSM (Finite State Machine)

### 1. Состояния для многошаговых операций
```python
# utils/states.py
class BookUploadStates(StatesGroup):
    waiting_for_zip_file = State()

class BookLinkStates(StatesGroup):
    waiting_for_yandex_url = State()
    waiting_for_litres_url = State()
    waiting_for_audio_format = State()
```

### 2. Обработка состояний
```python
@router.message(StateFilter(BookLinkStates.waiting_for_yandex_url))
async def process_yandex_url(message: Message, state: FSMContext):
    data = await state.get_data()
    book_title = data.get('book_title')
    
    url = message.text.strip()
    if url.lower() == 'нет':
        url = ""
    
    # Обновляем данные
    books = book_service.get_all_books()
    if book_title in books:
        books[book_title]['yandex_books_url'] = url
        data_manager.save_json(config.database.books_file, books)
    
    await state.clear()
```

## �� Работа с файлами

### 1. Портативный Calibre
```python
# utils/book_converter.py
def _find_calibre_path(self) -> Optional[str]:
    """Поиск Calibre с приоритетом портативной версии"""
    if self.is_windows:
        portable_paths = [
            "./calibre-portable/ebook-convert.exe",
            "./calibre-portable/calibre/ebook-convert.exe"
        ]
        system_paths = [
            r"C:\Program Files\Calibre2\ebook-convert.exe"
        ]
    else:
        portable_paths = ["./calibre-portable/ebook-convert"]
        system_paths = ["/usr/bin/ebook-convert"]
    
    # Сначала проверяем портативную версию
    for path in portable_paths + system_paths:
        if os.path.exists(path):
            return path
    return None
```

### 2. Обработка ZIP архивов
```python
def extract_fb2_from_zip(zip_path: str) -> Optional[str]:
    """Извлечение FB2 из ZIP архива"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                if file_info.filename.lower().endswith('.fb2'):
                    # Извлекаем FB2 файл
                    zip_ref.extract(file_info, temp_dir)
                    return os.path.join(temp_dir, file_info.filename)
    except Exception as e:
        logger.log_error(e, f"Ошибка извлечения из ZIP: {zip_path}")
        return None
```

## 🎨 UX/UI принципы

### 1. Интерактивные клавиатуры
```python
def create_book_keyboard(book_title: str) -> InlineKeyboardMarkup:
    safe_title = safe_encode_title(book_title)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать FB2", callback_data=f"download_{safe_title}_fb2")],
        [InlineKeyboardButton(text="📥 Скачать EPUB", callback_data=f"download_{safe_title}_epub")],
        [InlineKeyboardButton(text="📥 Скачать MOBI", callback_data=f"download_{safe_title}_mobi")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_library")]
    ])
```

### 2. Информативные сообщения
```python
async def show_book_card(callback: CallbackQuery, book_info: Dict):
    card_text = f"�� <b>{book_title}</b>\n\n"
    
    if 'author' in book_info:
        card_text += f"👤 <b>Автор:</b> {book_info['author']}\n"
    
    if 'description' in book_info:
        desc = book_info['description']
        if len(desc) > 300:
            desc = desc[:300] + "..."
        card_text += f"�� <b>Описание:</b> {desc}\n"
    
    # Добавляем ссылки на онлайн каталоги
    if book_info.get('yandex_books_url'):
        card_text += f"�� <b>Яндекс.Книги:</b> {book_info['yandex_books_url']}\n"
```

## 📝 Логирование и отладка

### 1. Структурированное логирование
```python
# utils/logger.py
class BotLogger:
    def __init__(self):
        self.logger = logging.getLogger('bot')
        self.setup_logging()
    
    def log_user_action(self, user_id: int, action: str):
        self.logger.info(f"Пользователь {user_id}: {action}")
    
    def log_admin_action(self, user_id: int, action: str):
        self.logger.info(f"Админ {user_id}: {action}")
    
    def log_error(self, error: Exception, context: str = ""):
        self.logger.error(f"Ошибка: {error} | Контекст: {context}")
```

### 2. Фильтрация чувствительных данных
```python
def filter_sensitive_data(message: str) -> str:
    """Фильтрация токенов и паролей из логов"""
    sensitive_patterns = [
        r'BOT_TOKEN=\w+',
        r'SECRET_PHRASE=\w+',
        r'password["\']?\s*[:=]\s*["\']?\w+["\']?'
    ]
    
    for pattern in sensitive_patterns:
        message = re.sub(pattern, '[FILTERED]', message)
    
    return message
```

## 🚀 Graceful Shutdown

### 1. Корректное завершение
```python
# main.py
async def on_shutdown(dp: Dispatcher):
    """Корректное завершение работы бота"""
    bot_logger.info("🛑 Завершение работы бота...")
    
    # Очистка временных файлов
    cleanup_temp_files()
    
    # Сохранение состояния
    await dp.storage.close()
    
    bot_logger.info("✅ Бот успешно завершен")

# Регистрация обработчиков
dp.shutdown.register(on_shutdown)
```

## 🔄 Жизненный цикл пользователя

### 1. Статусы пользователей
```python
USER_STATUSES = {
    'inactive': 'Неактивный',
    'active': 'Активный', 
    'banned': 'Заблокированный'
}

USER_ROLES = {
    'user': 'Пользователь',
    'moderator': 'Модератор',
    'admin': 'Администратор'
}
```

### 2. Контроль доступа
```python
def active_user_required(func):
    async def wrapper(message: Message, *args, **kwargs):
        user_id = message.from_user.id
        user_data = user_service.get_user(user_id)
        
        if not user_data or user_data.get('status') != 'active':
            await message.answer("❌ Ваш аккаунт неактивен!")
            return
        
        return await func(message, *args, **kwargs)
    return wrapper
```

## 📋 Чек-лист для нового проекта

### ✅ Обязательные компоненты:
1. **Валидация переменных окружения** - проверка всех необходимых токенов
2. **Структурированное логирование** - с фильтрацией чувствительных данных
3. **Контроль доступа** - декораторы для разных уровней доступа
4. **Graceful shutdown** - корректное завершение работы
5. **Кэширование данных** - для оптимизации производительности
6. **Миграции данных** - для обновления структуры БД
7. **FSM для сложных операций** - многошаговые процессы
8. **Мультиплатформенность** - поддержка Windows/Linux
9. **Безопасная работа с файлами** - FSInputFile для отправки
10. **Валидация callback_data** - MD5 хеши для длинных названий

### 🎯 Рекомендуемые практики:
1. **Модульная архитектура** - разделение на handlers/services/utils
2. **SOLID принципы** - для масштабируемости
3. **Комплексное логирование** - для отладки
4. **Интерактивные клавиатуры** - для лучшего UX
5. **Портативные зависимости** - Calibre в папке проекта
6. **Автоматическая очистка** - временных файлов
7. **Структурированная документация** - TODO.md, README.md
8. **Версионирование** - Git с осмысленными коммитами

## 🚨 Типичные ошибки и их профилактика

### ❌ НЕ ДЕЛАЙТЕ:
- Хранить токены в коде
- Использовать глобальные переменные
- Игнорировать обработку ошибок
- Отправлять файлы через `Path()` напрямую
- Использовать длинные названия в callback_data
- Забывать про graceful shutdown
- Не валидировать пользовательский ввод

### ✅ ОБЯЗАТЕЛЬНО ДЕЛАЙТЕ:
- Использовать переменные окружения
- Применять декораторы для контроля доступа
- Логировать все действия пользователей
- Использовать FSInputFile для отправки файлов
- Кодировать callback_data через MD5
- Реализовывать graceful shutdown
- Валидировать все входные данные

Этот гайд поможет избежать большинства проблем при создании Telegram ботов с библиотекой книг и других подобных проектов! 🚀
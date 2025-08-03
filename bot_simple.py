import asyncio
import json
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config_simple import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Инициализация бота
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Простые функции для работы с данными
def load_json(filename):
    """Загружает данные из JSON файла"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json(filename, data):
    """Сохраняет данные в JSON файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_users():
    """Загружает пользователей"""
    return load_json('users_simple.json')

def load_books():
    """Загружает книги"""
    return load_json('books_simple.json')

def load_events():
    """Загружает события"""
    return load_json('events_simple.json')

def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    return str(user_id) in [str(admin_id) for admin_id in settings.ADMIN_IDS]

# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Начальная команда"""
    user_id = str(message.from_user.id)
    users = load_users()
    
    if user_id not in users:
        await message.answer(
            "👋 Добро пожаловать в книжный клуб!\n"
            "Для регистрации используйте /register <секретная_фраза>"
        )
    else:
        await message.answer(
            f"Привет, {message.from_user.first_name}! 👋\n"
            "Используйте /help для списка команд"
        )

@dp.message(Command("register"))
async def cmd_register(message: Message):
    """Регистрация пользователя"""
    user_id = str(message.from_user.id)
    users = load_users()
    
    if user_id in users:
        await message.answer("Вы уже зарегистрированы!")
        return
    
    # Простая проверка секретной фразы
    args = message.text.split()
    if len(args) < 2 or args[1] != settings.SECRET_PHRASE:
        await message.answer("❌ Неверная секретная фраза!")
        return
    
    # Регистрация пользователя
    users[user_id] = {
        "name": message.from_user.first_name,
        "username": message.from_user.username,
        "registered_at": datetime.now().isoformat(),
        "status": "active"
    }
    save_json('users_simple.json', users)
    
    await message.answer("✅ Регистрация успешна! Используйте /help для списка команд")

@dp.message(Command("books"))
async def cmd_books(message: Message):
    """Показать список книг"""
    books = load_books()
    
    if not books:
        await message.answer("📚 В библиотеке пока нет книг.")
        return
    
    # Создаем простую клавиатуру
    keyboard = []
    for book_title in books.keys():
        keyboard.append([InlineKeyboardButton(text=book_title, callback_data=f"book:{book_title}")])
    
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("📖 Выберите книгу:", reply_markup=markup)

@dp.callback_query(lambda c: c.data.startswith('book:'))
async def process_book_selection(callback: CallbackQuery):
    """Обработка выбора книги"""
    book_title = callback.data.split(':', 1)[1]
    books = load_books()
    
    if book_title not in books:
        await callback.answer("Книга не найдена!")
        return
    
    book_info = books[book_title]
    
    # Формируем информацию о книге
    text = f"📖 <b>{book_title}</b>\n\n"
    if 'author' in book_info:
        text += f"👤 Автор: {book_info['author']}\n"
    
    # Проверяем доступные форматы
    formats = []
    for fmt in ['epub', 'fb2', 'mobi']:
        if f'{fmt}_file' in book_info:
            formats.append(fmt.upper())
    
    if formats:
        text += f"📁 Доступные форматы: {', '.join(formats)}\n\n"
        text += "Выберите формат для скачивания:"
        
        # Создаем кнопки для форматов
        keyboard = []
        for fmt in formats:
            keyboard.append([InlineKeyboardButton(
                text=fmt, 
                callback_data=f"download:{book_title}:{fmt.lower()}"
            )])
        keyboard.append([InlineKeyboardButton(text="« Назад", callback_data="back_to_books")])
        
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    else:
        await callback.answer("Файлы для этой книги недоступны!")

@dp.callback_query(lambda c: c.data.startswith('download:'))
async def process_download(callback: CallbackQuery):
    """Обработка скачивания книги"""
    _, book_title, format_type = callback.data.split(':', 2)
    books = load_books()
    
    if book_title not in books:
        await callback.answer("Книга не найдена!")
        return
    
    book_info = books[book_title]
    file_key = f'{format_type}_file'
    
    if file_key in book_info:
        try:
            file_path = book_info[file_key]
            if os.path.exists(file_path):
                await bot.send_document(
                    chat_id=callback.from_user.id,
                    document=types.FSInputFile(file_path),
                    caption=f"📚 {book_title} ({format_type.upper()})"
                )
                await callback.answer("Файл отправлен!")
            else:
                await callback.answer("Файл не найден на сервере!")
        except Exception as e:
            logging.error(f"Ошибка отправки файла: {e}")
            await callback.answer("Ошибка отправки файла!")
    else:
        await callback.answer("Этот формат недоступен!")

@dp.callback_query(lambda c: c.data == "back_to_books")
async def back_to_books(callback: CallbackQuery):
    """Возврат к списку книг"""
    books = load_books()
    
    keyboard = []
    for book_title in books.keys():
        keyboard.append([InlineKeyboardButton(text=book_title, callback_data=f"book:{book_title}")])
    
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await callback.message.edit_text("📖 Выберите книгу:", reply_markup=markup)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Показать справку"""
    help_text = """
📚 <b>Команды книжного клуба:</b>

/start - Начать работу с ботом
/register <фраза> - Регистрация в клубе
/books - Просмотр библиотеки
/schedule - Расписание встреч
/profile - Ваш профиль
/help - Эта справка

Для администраторов:
/admin - Панель администратора
    """
    await message.answer(help_text, parse_mode="HTML")

@dp.message(Command("schedule"))
async def cmd_schedule(message: Message):
    """Показать расписание встреч"""
    events = load_events()
    
    if not events:
        await message.answer("📅 Встречи пока не запланированы.")
        return
    
    text = "📅 <b>Ближайшие встречи:</b>\n\n"
    
    for event_id, event in events.items():
        text += f"📖 <b>{event.get('title', 'Без названия')}</b>\n"
        text += f"📅 Дата: {event.get('date', 'Не указана')}\n"
        text += f"⏰ Время: {event.get('time', 'Не указано')}\n"
        if event.get('description'):
            text += f"📝 {event['description']}\n"
        text += "\n"
    
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("profile"))
async def cmd_profile(message: Message):
    """Показать профиль пользователя"""
    user_id = str(message.from_user.id)
    users = load_users()
    
    if user_id not in users:
        await message.answer("Вы не зарегистрированы! Используйте /register")
        return
    
    user_info = users[user_id]
    text = f"""
👤 <b>Ваш профиль:</b>

📝 Имя: {user_info.get('name', 'Не указано')}
🆔 ID: {user_id}
📅 Регистрация: {user_info.get('registered_at', 'Не указано')}
✅ Статус: {user_info.get('status', 'Не указан')}
    """
    
    await message.answer(text, parse_mode="HTML")

# Административные функции
@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Панель администратора"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора!")
        return
    
    keyboard = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="📚 Управление книгами", callback_data="admin_books")],
        [InlineKeyboardButton(text="📅 Управление событиями", callback_data="admin_events")]
    ]
    
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("🔧 <b>Панель администратора</b>\nВыберите действие:", reply_markup=markup, parse_mode="HTML")

@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Показать статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    users = load_users()
    books = load_books()
    events = load_events()
    
    active_users = sum(1 for user in users.values() if user.get('status') == 'active')
    
    text = f"""
📊 <b>Статистика клуба:</b>

👥 Пользователи: {len(users)} (активных: {active_users})
📚 Книг в библиотеке: {len(books)}
📅 Запланированных встреч: {len(events)}
    """
    
    await callback.message.edit_text(text, parse_mode="HTML")

@dp.callback_query(lambda c: c.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    """Показать список пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    users = load_users()
    
    if not users:
        text = "👥 Пользователей пока нет"
    else:
        text = "👥 <b>Список пользователей:</b>\n\n"
        for user_id, user_info in users.items():
            text += f"🆔 {user_id}\n"
            text += f"📝 {user_info.get('name', 'Не указано')}\n"
            text += f"✅ Статус: {user_info.get('status', 'Не указан')}\n"
            text += f"📅 Регистрация: {user_info.get('registered_at', 'Не указано')}\n\n"
    
    await callback.message.edit_text(text, parse_mode="HTML")

@dp.callback_query(lambda c: c.data == "admin_books")
async def admin_books(callback: CallbackQuery):
    """Управление книгами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    books = load_books()
    
    if not books:
        text = "📚 Книг в библиотеке пока нет"
    else:
        text = "📚 <b>Книги в библиотеке:</b>\n\n"
        for title, info in books.items():
            text += f"📖 {title}\n"
            if 'author' in info:
                text += f"👤 {info['author']}\n"
            text += "\n"
    
    await callback.message.edit_text(text, parse_mode="HTML")

@dp.callback_query(lambda c: c.data == "admin_events")
async def admin_events(callback: CallbackQuery):
    """Управление событиями"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    events = load_events()
    
    if not events:
        text = "📅 Событий пока нет"
    else:
        text = "📅 <b>Запланированные события:</b>\n\n"
        for event_id, event in events.items():
            text += f"📖 {event.get('title', 'Без названия')}\n"
            text += f"📅 {event.get('date', 'Не указана')}\n"
            text += f"⏰ {event.get('time', 'Не указано')}\n\n"
    
    await callback.message.edit_text(text, parse_mode="HTML")

async def main():
    """Главная функция"""
    logging.info("🚀 Запуск упрощенного бота...")
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logging.info("⏹️ Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main()) 
"""
@file: handlers/user_handlers.py
@description: Обработчики команд пользователей
@dependencies: aiogram, config, utils
@created: 2024-01-15
"""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

from config import config
from utils.data_manager import data_manager
from utils.security import security_manager
from utils.logger import bot_logger
from keyboards.inline import create_books_keyboard, create_book_keyboard, create_back_keyboard
from services.users import user_service
from services.books import book_service
from services.events import event_service

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """
    Начальная команда бота
    
    Приветствует пользователя и проверяет его регистрацию.
    Если пользователь не зарегистрирован, предлагает пройти регистрацию.
    
    Args:
        message (Message): Сообщение от пользователя
        
    Returns:
        None
    """
    user_id = str(message.from_user.id)
    users = data_manager.load_json(config.database.users_file)
    
    bot_logger.log_user_action(message.from_user.id, "команда /start")
    
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


@router.message(Command("register"))
async def cmd_register(message: Message) -> None:
    """
    Регистрация пользователя в клубе
    
    Обрабатывает команду регистрации с проверкой секретной фразы.
    Включает валидацию входных данных и защиту от брутфорса.
    
    Args:
        message (Message): Сообщение с командой регистрации
        
    Returns:
        None
    """
    user_id = str(message.from_user.id)
    
    bot_logger.log_user_action(message.from_user.id, "попытка регистрации")
    
    # Проверка существования пользователя
    if user_service.get_user(user_id):
        await message.answer("Вы уже зарегистрированы!")
        return
    
    # Проверка попыток входа
    if not security_manager.check_login_attempts(message.from_user.id):
        await message.answer("❌ Слишком много попыток. Попробуйте позже.")
        return
    
    # Валидация входных данных
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажите секретную фразу: /register <фраза>")
        security_manager.record_login_attempt(message.from_user.id, False)
        return
    
    secret_phrase = args[1]
    
    # Проверка секретной фразы
    if not security_manager.verify_secret_phrase(secret_phrase, config.security.secret_phrase):
        await message.answer("❌ Неверная секретная фраза!")
        security_manager.record_login_attempt(message.from_user.id, False)
        bot_logger.log_security_event("неверная_фраза", message.from_user.id)
        return
    
    # Создание пользователя через сервис
    if user_service.create_user(
        user_id=user_id,
        name=message.from_user.first_name,
        username=message.from_user.username
    ):
        security_manager.record_login_attempt(message.from_user.id, True)
        await message.answer("✅ Регистрация успешна! Используйте /help для списка команд")
    else:
        await message.answer("❌ Ошибка регистрации")


@router.message(Command("books"))
async def cmd_books(message: Message) -> None:
    """
    Показать список доступных книг
    
    Отображает интерактивную клавиатуру со всеми книгами в библиотеке.
    Если книг нет, показывает соответствующее сообщение.
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    books = book_service.get_all_books()
    
    bot_logger.log_user_action(message.from_user.id, "просмотр библиотеки")
    
    if not books:
        await message.answer("📚 В библиотеке пока нет книг.")
        return
    
    keyboard = create_books_keyboard(books)
    await message.answer("📖 Выберите книгу:", reply_markup=keyboard)


@router.callback_query(lambda c: c.data.startswith('book:'))
async def process_book_selection(callback: CallbackQuery) -> None:
    """
    Обработка выбора книги
    
    Показывает детальную информацию о выбранной книге,
    включая автора, описание и доступные форматы для скачивания.
    
    Args:
        callback (CallbackQuery): Callback от inline клавиатуры
        
    Returns:
        None
    """
    book_title = callback.data.split(':', 1)[1]
    book_info = book_service.get_book(book_title)
    
    bot_logger.log_user_action(callback.from_user.id, f"выбор книги: {book_title}")
    
    if not book_info:
        await callback.answer("Книга не найдена!")
        return
    
    # Формируем информацию о книге
    text = f"📖 <b>{book_title}</b>\n\n"
    if 'author' in book_info:
        text += f"👤 Автор: {book_info['author']}\n"
    if 'description' in book_info:
        text += f"📝 {book_info['description']}\n\n"
    
    # Проверяем доступные форматы
    formats = []
    for fmt in ['epub', 'fb2', 'mobi']:
        if f'{fmt}_file' in book_info:
            formats.append(fmt.upper())
    
    if formats:
        text += f"📁 Доступные форматы: {', '.join(formats)}\n\n"
        text += "Выберите формат для скачивания:"
        
        keyboard = create_book_keyboard(book_title, formats)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback.answer("Файлы для этой книги недоступны!")


@router.callback_query(lambda c: c.data.startswith('download:'))
async def process_download(callback: CallbackQuery) -> None:
    """
    Обработка скачивания книги
    
    Отправляет файл книги в выбранном формате пользователю.
    Включает валидацию пути файла и логирование операций.
    
    Args:
        callback (CallbackQuery): Callback с данными о книге и формате
        
    Returns:
        None
    """
    _, book_title, format_type = callback.data.split(':', 2)
    book_info = book_service.get_book(book_title)
    
    bot_logger.log_user_action(callback.from_user.id, f"скачивание {book_title} ({format_type})")
    
    if not book_info:
        await callback.answer("Книга не найдена!")
        return
    file_key = f'{format_type}_file'
    
    if file_key in book_info:
        try:
            file_path = book_info[file_key]
            if file_path and file_path.startswith('books/'):
                # Валидация пути файла
                sanitized_path = security_manager.sanitize_filename(file_path)
                
                await callback.bot.send_document(
                    chat_id=callback.from_user.id,
                    document=types.FSInputFile(sanitized_path),
                    caption=f"📚 {book_title} ({format_type.upper()})"
                )
                await callback.answer("Файл отправлен!")
                bot_logger.log_file_operation("скачивание", sanitized_path, True)
            else:
                await callback.answer("Файл не найден на сервере!")
                bot_logger.log_file_operation("скачивание", file_path, False)
        except Exception as e:
            bot_logger.log_error(e, f"ошибка отправки файла {file_path}")
            await callback.answer("Ошибка отправки файла!")
    else:
        await callback.answer("Этот формат недоступен!")


@router.callback_query(lambda c: c.data == "back_to_books")
async def back_to_books(callback: CallbackQuery) -> None:
    """
    Возврат к списку книг
    
    Обновляет сообщение, возвращая пользователя к списку всех книг.
    
    Args:
        callback (CallbackQuery): Callback с кнопки "Назад"
        
    Returns:
        None
    """
    books = book_service.get_all_books()
    
    bot_logger.log_user_action(callback.from_user.id, "возврат к списку книг")
    
    keyboard = create_books_keyboard(books)
    await callback.message.edit_text("📖 Выберите книгу:", reply_markup=keyboard)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """
    Показать справку по командам
    
    Отображает полный список доступных команд с описанием.
    Включает команды для пользователей и администраторов.
    
    Args:
        message (Message): Сообщение с командой помощи
        
    Returns:
        None
    """
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
    
    bot_logger.log_user_action(message.from_user.id, "запрос справки")
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("schedule"))
async def cmd_schedule(message: Message) -> None:
    """
    Показать расписание встреч
    
    Отображает список предстоящих встреч книжного клуба.
    Показывает дату, время и описание каждого события.
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    events = event_service.get_upcoming_events()
    
    bot_logger.log_user_action(message.from_user.id, "просмотр расписания")
    
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


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    """
    Показать профиль пользователя
    
    Отображает информацию о профиле пользователя,
    включая имя, ID, дату регистрации и статус.
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    user_id = str(message.from_user.id)
    user_info = user_service.get_user(user_id)
    
    bot_logger.log_user_action(message.from_user.id, "просмотр профиля")
    
    if not user_info:
        await message.answer("Вы не зарегистрированы! Используйте /register")
        return
    
    text = f"""
👤 <b>Ваш профиль:</b>

📝 Имя: {user_info.get('name', 'Не указано')}
🆔 ID: {user_id}
📅 Регистрация: {user_info.get('registered_at', 'Не указано')}
✅ Статус: {user_info.get('status', 'Не указан')}
    """
    
    await message.answer(text, parse_mode="HTML") 
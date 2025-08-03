"""
@file: handlers/user_handlers.py
@description: Обработчики команд пользователей
@dependencies: aiogram, config, utils
@created: 2024-01-15
"""

from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime

from config import config
from utils.data_manager import data_manager
from utils.security import security_manager
from utils.logger import bot_logger
from keyboards.inline import create_books_keyboard, create_book_keyboard, create_back_keyboard
from services.users import user_service
from services.books import book_service
from services.events import event_service
from utils.states import RegistrationStates, BookSearchStates

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """
    Начальная команда бота
    
    Приветствует пользователя и автоматически создает запись в базе.
    Если пользователь не авторизован, предлагает пройти регистрацию.
    
    Args:
        message (Message): Сообщение от пользователя
        
    Returns:
        None
    """
    user_id = str(message.from_user.id)
    user_info = user_service.get_user(user_id)
    
    bot_logger.log_user_action(message.from_user.id, "команда /start")
    
    if not user_info:
        # Создаем пользователя автоматически со статусом inactive
        if user_service.create_user(
            user_id=user_id,
            name=message.from_user.first_name,
            username=message.from_user.username,
            status="inactive"
        ):
            await message.answer(
                "👋 Добро пожаловать в книжный клуб!\n"
                "Для доступа к функциям используйте /register"
            )
        else:
            await message.answer("❌ Ошибка создания профиля. Попробуйте позже.")
    else:
        status = user_info.get('status', 'unknown')
        if status == 'active':
            await message.answer(
                f"Привет, {message.from_user.first_name}! 👋\n"
                "Используйте /help для списка команд"
            )
        else:
            await message.answer(
                "👋 С возвращением!\n"
                "Для доступа к функциям используйте /register"
            )


@router.message(Command("register"))
async def cmd_register(message: Message, state: FSMContext) -> None:
    """
    Начало процесса регистрации пользователя
    
    Запускает FSM для пошаговой регистрации с проверкой секретной фразы.
    
    Args:
        message (Message): Сообщение с командой регистрации
        
    Returns:
        None
    """
    user_id = str(message.from_user.id)
    
    bot_logger.log_user_action(message.from_user.id, "начало регистрации")
    
    # Проверка существования пользователя
    user_info = user_service.get_user(user_id)
    if user_info and user_info.get('status') == 'active':
        await message.answer("Вы уже авторизованы!")
        return
    
    # Проверка попыток входа
    if not security_manager.check_login_attempts(message.from_user.id):
        await message.answer("❌ Слишком много попыток. Попробуйте позже.")
        return
    
    await message.answer("🔐 Введите секретную фразу для регистрации:")
    await message.answer("💡 Подсказка: фраза указана в документации клуба")
    
    # Устанавливаем состояние ожидания фразы
    await state.set_state(RegistrationStates.waiting_for_phrase)


@router.message(StateFilter(RegistrationStates.waiting_for_phrase))
async def process_registration_phrase(message: Message, state: FSMContext) -> None:
    """
    Обработка секретной фразы при регистрации
    
    Args:
        message (Message): Сообщение с секретной фразой
        
    Returns:
        None
    """
    user_id = str(message.from_user.id)
    secret_phrase = message.text.strip()
    
    bot_logger.log_user_action(message.from_user.id, "ввод секретной фразы")
    
    # Проверка секретной фразы
    if not security_manager.verify_secret_phrase(secret_phrase, config.security.secret_phrase):
        await message.answer("❌ Неверная секретная фраза! Попробуйте еще раз или используйте /cancel для отмены")
        security_manager.record_login_attempt(message.from_user.id, False)
        bot_logger.log_security_event("неверная_фраза", message.from_user.id)
        return
    
    # Активация пользователя через сервис
    if user_service.activate_user(user_id):
        security_manager.record_login_attempt(message.from_user.id, True)
        await message.answer("✅ Авторизация успешна! Используйте /help для списка команд")
        
        # Сбрасываем состояние
        await state.clear()
    else:
        await message.answer("❌ Ошибка авторизации. Попробуйте позже.")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """
    Отмена текущего процесса
    
    Args:
        message (Message): Сообщение с командой отмены
        
    Returns:
        None
    """
    current_state = await state.get_state()
    
    if current_state:
        await state.clear()
        await message.answer("❌ Операция отменена. Используйте /help для списка команд")
    else:
        await message.answer("Нет активных операций для отмены.")


@router.message(Command("books"))
async def cmd_books(message: Message) -> None:
    """
    Показать список доступных книг
    
    Отображает интерактивную клавиатуру со всеми книгами в библиотеке.
    Требует авторизации пользователя.
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    user_id = str(message.from_user.id)
    user_info = user_service.get_user(user_id)
    
    if not user_info or user_info.get('status') != 'active':
        await message.answer("❌ Для доступа к библиотеке необходимо авторизоваться!\nИспользуйте /register")
        return
    
    books = book_service.get_all_books()
    
    bot_logger.log_user_action(message.from_user.id, "просмотр библиотеки")
    
    if not books:
        await message.answer("📚 В библиотеке пока нет книг.")
        return
    
    keyboard = create_books_keyboard(books)
    await message.answer("📖 Выберите книгу:", reply_markup=keyboard)


@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext) -> None:
    """
    Начать поиск книг
    
    Запускает FSM для поиска книг по названию или автору.
    Требует авторизации пользователя.
    
    Args:
        message (Message): Сообщение с командой поиска
        
    Returns:
        None
    """
    user_id = str(message.from_user.id)
    user_info = user_service.get_user(user_id)
    
    if not user_info or user_info.get('status') != 'active':
        await message.answer("❌ Для поиска книг необходимо авторизоваться!\nИспользуйте /register")
        return
    
    bot_logger.log_user_action(message.from_user.id, "начало поиска книг")
    
    await message.answer("🔍 Введите название книги или автора для поиска:")
    await message.answer("💡 Примеры: 'Гарри Поттер', 'Толстой', 'фантастика'")
    
    # Устанавливаем состояние ожидания запроса
    await state.set_state(BookSearchStates.waiting_for_query)


@router.message(StateFilter(BookSearchStates.waiting_for_query))
async def process_search_query(message: Message, state: FSMContext) -> None:
    """
    Обработка поискового запроса
    
    Args:
        message (Message): Сообщение с поисковым запросом
        
    Returns:
        None
    """
    query = message.text.strip().lower()
    
    bot_logger.log_user_action(message.from_user.id, f"поиск книг: {query}")
    
    books = book_service.get_all_books()
    found_books = {}
    
    # Поиск книг по запросу
    for title, book_info in books.items():
        title_lower = title.lower()
        author_lower = book_info.get('author', '').lower()
        description_lower = book_info.get('description', '').lower()
        
        if (query in title_lower or 
            query in author_lower or 
            query in description_lower):
            found_books[title] = book_info
    
    if found_books:
        keyboard = create_books_keyboard(found_books)
        await message.answer(f"🔍 Найдено {len(found_books)} книг:", reply_markup=keyboard)
    else:
        await message.answer("❌ Книги не найдены. Попробуйте другой запрос.")
    
    # Сбрасываем состояние
    await state.clear()


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
/register - Авторизация в клубе (пошагово)
/search - Поиск книг по названию или автору
/books - Просмотр всей библиотеки
/schedule - Расписание встреч
/profile - Ваш профиль
/cancel - Отменить текущую операцию
/help - Эта справка

Для администраторов:
/admin - Панель администратора
/settag &lt;user_id&gt; &lt;tag&gt; - Установить тег пользователю
/ban &lt;user_id&gt; - Заблокировать пользователя
/unban &lt;user_id&gt; - Разблокировать пользователя
/userinfo &lt;user_id&gt; - Информация о пользователе
/stats - Расширенная статистика
    """
    
    bot_logger.log_user_action(message.from_user.id, "запрос справки")
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("schedule"))
async def cmd_schedule(message: Message) -> None:
    """
    Показать расписание встреч
    
    Отображает список предстоящих встреч книжного клуба.
    Требует авторизации пользователя.
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    user_id = str(message.from_user.id)
    user_info = user_service.get_user(user_id)
    
    if not user_info or user_info.get('status') != 'active':
        await message.answer("❌ Для доступа к расписанию необходимо авторизоваться!\nИспользуйте /register")
        return
    
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
    
    Отображает информацию о пользователе:
    - ID пользователя (копируемый)
    - Имя пользователя
    - Username (кликабельный)
    - Дата регистрации
    - Статус в клубе
    - Теги/роли
    
    Args:
        message (Message): Сообщение с командой профиля
        
    Returns:
        None
    """
    user_id = str(message.from_user.id)
    user_info = user_service.get_user(user_id)
    
    bot_logger.log_user_action(message.from_user.id, "просмотр профиля")
    
    if not user_info:
        await message.answer("❌ Профиль не найден!\nИспользуйте /start для создания профиля.")
        return
    
    status = user_info.get('status', 'unknown')
    if status != 'active':
        await message.answer("❌ Вы не авторизованы в клубе!\nИспользуйте /register для авторизации.")
        return
    
    # Получаем username пользователя
    username = user_info.get('username', '')
    if username and not username.startswith('@'):
        username = f"@{username}"
    
    # Формируем кликабельный username
    username_display = username if username else "Не указан"
    if username and username != "Не указан":
        username_display = f"<a href='https://t.me/{username[1:]}'>{username}</a>"
    
    # Формируем копируемый ID
    user_id_display = f"<code>{user_id}</code>"
    
    # Формируем отображение тегов
    tags = user_info.get('tags', [])
    if isinstance(tags, str):
        tags = [tags]
    elif not isinstance(tags, list):
        tags = []
    
    tags_display = ", ".join(tags) if tags else "Не указаны"
    
    # Формируем текст профиля
    profile_text = f"""
👤 <b>Ваш профиль:</b>

🆔 ID: {user_id_display}
🔹 Имя: {user_info.get('name', 'Не указано')}
📌 Username: {username_display}
📅 Дата регистрации: {user_info.get('registered_at', 'Не указана')}
📍 Статус: {user_info.get('status', 'Не указан')}
🏷️ Теги: {tags_display}
    """
    
    await message.answer(profile_text, parse_mode="HTML", disable_web_page_preview=True) 
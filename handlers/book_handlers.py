"""
@file: handlers/book_handlers.py
@description: Обработчики для управления книгами через FSM
@dependencies: aiogram, config, utils, services
@created: 2025-01-04
"""

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime
from pathlib import Path

from config import config
from utils.logger import bot_logger
from utils.access_control import admin_required
from services.books import book_service
from utils.states import BookManagementStates
from utils.fb2_parser import fb2_parser
from utils.book_converter import book_converter
from utils.telegram_uploader import telegram_uploader

router = Router()


@router.message(Command("addbook"))
@admin_required
async def cmd_addbook(message: Message, state: FSMContext) -> None:
    """
    Начало процесса добавления книги
    
    Запускает FSM для пошагового добавления книги:
    1. Название книги
    2. Автор
    3. Описание (опционально)
    4. Путь к файлу (опционально)
    
    Args:
        message (Message): Сообщение с командой добавления книги
        state (FSMContext): Контекст FSM
        
    Returns:
        None
    """
    bot_logger.log_admin_action(message.from_user.id, "начало добавления книги")
    
    await state.set_state(BookManagementStates.waiting_for_book_title)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_addbook")]
    ])
    
    await message.answer(
        "📚 <b>Добавление новой книги</b>\n\n"
        "💡 <b>Шаг 1/4:</b> Введите название книги\n\n"
        "📝 <b>Примеры:</b>\n"
        "• Война и мир\n"
        "• Преступление и наказание\n"
        "• Мастер и Маргарита",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(Command("uploadbook"))
@admin_required
async def cmd_uploadbook(message: Message, state: FSMContext) -> None:
    """
    Начало процесса загрузки книги из ZIP-архива
    
    Обрабатывает ZIP-архив с FB2 файлом:
    1. Извлекает FB2 файл
    2. Парсит метаданные
    3. Конвертирует в EPUB и MOBI
    4. Загружает в Telegram
    5. Сохраняет в базу данных
    
    Args:
        message (Message): Сообщение с командой загрузки книги
        state (FSMContext): Контекст FSM
        
    Returns:
        None
    """
    bot_logger.log_admin_action(message.from_user.id, "начало загрузки книги из ZIP")
    
    await state.set_state(BookManagementStates.waiting_for_zip_file)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_addbook")]
    ])
    
    await message.answer(
        "📚 <b>Загрузка книги из ZIP-архива</b>\n\n"
        "💡 <b>Шаг 1:</b> Отправьте ZIP-архив с FB2 файлом\n\n"
        "📝 <b>Требования:</b>\n"
        "• ZIP-архив должен содержать FB2 файл\n"
        "• FB2 файл должен иметь корректные метаданные\n"
        "• Размер архива не более 50MB\n\n"
        "🔄 <b>Что произойдет:</b>\n"
        "• Извлечение FB2 файла\n"
        "• Парсинг метаданных (автор, название, год, жанр)\n"
        "• Конвертация в EPUB и MOBI\n"
        "• Загрузка в Telegram для шаринга\n"
        "• Сохранение в базу данных",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(StateFilter(BookManagementStates.waiting_for_book_title))
async def process_book_title(message: Message, state: FSMContext) -> None:
    """
    Обработка названия книги
    
    Args:
        message (Message): Сообщение с названием книги
        state (FSMContext): Контекст FSM
        
    Returns:
        None
    """
    title = message.text.strip()
    
    if len(title) < 2:
        await message.answer(
            "❌ Название книги слишком короткое!\n"
            "Минимум 2 символа. Попробуйте еще раз:"
        )
        return
    
    if len(title) > 200:
        await message.answer(
            "❌ Название книги слишком длинное!\n"
            "Максимум 200 символов. Попробуйте еще раз:"
        )
        return
    
    # Проверяем, не существует ли уже такая книга
    existing_book = book_service.get_book(title)
    if existing_book:
        await message.answer(
            f"❌ Книга <b>«{title}»</b> уже существует в библиотеке!\n\n"
            "Введите другое название:",
            parse_mode="HTML"
        )
        return
    
    # Сохраняем название и переходим к следующему шагу
    await state.update_data(book_title=title)
    await state.set_state(BookManagementStates.waiting_for_author)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_addbook")]
    ])
    
    await message.answer(
        f"✅ <b>Название:</b> {title}\n\n"
        "💡 <b>Шаг 2/4:</b> Введите автора книги\n\n"
        "📝 <b>Примеры:</b>\n"
        "• Лев Толстой\n"
        "• Фёдор Достоевский\n"
        "• Михаил Булгаков",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(StateFilter(BookManagementStates.waiting_for_author))
async def process_book_author(message: Message, state: FSMContext) -> None:
    """
    Обработка автора книги
    
    Args:
        message (Message): Сообщение с автором книги
        state (FSMContext): Контекст FSM
        
    Returns:
        None
    """
    author = message.text.strip()
    
    if len(author) < 2:
        await message.answer(
            "❌ Имя автора слишком короткое!\n"
            "Минимум 2 символа. Попробуйте еще раз:"
        )
        return
    
    if len(author) > 100:
        await message.answer(
            "❌ Имя автора слишком длинное!\n"
            "Максимум 100 символов. Попробуйте еще раз:"
        )
        return
    
    # Сохраняем автора и переходим к следующему шагу
    await state.update_data(book_author=author)
    await state.set_state(BookManagementStates.waiting_for_description)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_description")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_addbook")]
    ])
    
    data = await state.get_data()
    title = data.get('book_title', 'Неизвестно')
    
    await message.answer(
        f"✅ <b>Название:</b> {title}\n"
        f"✅ <b>Автор:</b> {author}\n\n"
        "💡 <b>Шаг 3/4:</b> Введите описание книги (или пропустите)\n\n"
        "📝 <b>Примеры:</b>\n"
        "• Классический роман о русском обществе\n"
        "• Философский роман о преступлении и наказании\n"
        "• Магический реализм в советской Москве",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(StateFilter(BookManagementStates.waiting_for_description))
async def process_book_description(message: Message, state: FSMContext) -> None:
    """
    Обработка описания книги
    
    Args:
        message (Message): Сообщение с описанием книги
        state (FSMContext): Контекст FSM
        
    Returns:
        None
    """
    description = message.text.strip()
    
    if len(description) > 1000:
        await message.answer(
            "❌ Описание слишком длинное!\n"
            "Максимум 1000 символов. Попробуйте еще раз:"
        )
        return
    
    # Сохраняем описание и переходим к финальному шагу
    await state.update_data(book_description=description)
    await state.set_state(BookManagementStates.waiting_for_file_path)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_file")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_addbook")]
    ])
    
    data = await state.get_data()
    title = data.get('book_title', 'Неизвестно')
    author = data.get('book_author', 'Неизвестно')
    
    await message.answer(
        f"✅ <b>Название:</b> {title}\n"
        f"✅ <b>Автор:</b> {author}\n"
        f"✅ <b>Описание:</b> {description[:100]}{'...' if len(description) > 100 else ''}\n\n"
        "💡 <b>Шаг 4/4:</b> Введите путь к файлу книги (или пропустите)\n\n"
        "📁 <b>Поддерживаемые форматы:</b> EPUB, FB2, MOBI\n"
        "📝 <b>Примеры:</b>\n"
        "• books/war_and_peace.epub\n"
        "• books/crime_and_punishment.fb2\n"
        "• books/master_and_margarita.mobi",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(StateFilter(BookManagementStates.waiting_for_file_path))
async def process_book_file(message: Message, state: FSMContext) -> None:
    """
    Обработка пути к файлу книги и завершение добавления
    
    Args:
        message (Message): Сообщение с путем к файлу
        state (FSMContext): Контекст FSM
        
    Returns:
        None
    """
    file_path = message.text.strip()
    
    # Получаем все данные книги
    data = await state.get_data()
    title = data.get('book_title')
    author = data.get('book_author')
    description = data.get('book_description', '')
    
    # Проверяем путь к файлу если он указан
    files = {}
    if file_path and file_path.lower() != 'пропустить':
        # Определяем формат файла по расширению
        if file_path.lower().endswith('.epub'):
            files['epub'] = file_path
        elif file_path.lower().endswith('.fb2'):
            files['fb2'] = file_path
        elif file_path.lower().endswith('.mobi'):
            files['mobi'] = file_path
        else:
            await message.answer(
                "❌ Неподдерживаемый формат файла!\n"
                "Поддерживаются только: EPUB, FB2, MOBI\n"
                "Введите правильный путь или 'пропустить':"
            )
            return
    
    # Добавляем книгу в базу данных
    if book_service.add_book(title, author, description, files):
        bot_logger.log_admin_action(message.from_user.id, f"добавление книги: {title}")
        
        # Формируем сообщение об успехе
        success_text = f"""
✅ <b>Книга успешно добавлена!</b>

📚 <b>Название:</b> {title}
👤 <b>Автор:</b> {author}
📝 <b>Описание:</b> {description[:200]}{'...' if len(description) > 200 else ''}
        """
        
        if files:
            formats = ', '.join(files.keys()).upper()
            success_text += f"\n📁 <b>Форматы:</b> {formats}"
        else:
            success_text += "\n📁 <b>Форматы:</b> Не указаны"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 Добавить еще книгу", callback_data="add_another_book")],
            [InlineKeyboardButton(text="🔙 К панели администратора", callback_data="admin_back")]
        ])
        
        await message.answer(success_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(
            "❌ Ошибка при добавлении книги!\n"
            "Попробуйте еще раз или обратитесь к администратору."
        )
    
    # Очищаем состояние FSM
    await state.clear()


@router.callback_query(lambda c: c.data == "cancel_addbook")
async def cancel_addbook(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Отмена процесса добавления книги
    
    Args:
        callback (CallbackQuery): Callback от кнопки отмены
        state (FSMContext): Контекст FSM
        
    Returns:
        None
    """
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К панели администратора", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(
        "❌ <b>Добавление книги отменено</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data == "skip_description")
async def skip_description(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Пропуск описания книги
    
    Args:
        callback (CallbackQuery): Callback от кнопки пропуска
        state (FSMContext): Контекст FSM
        
    Returns:
        None
    """
    await state.update_data(book_description="")
    await state.set_state(BookManagementStates.waiting_for_file_path)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_file")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_addbook")]
    ])
    
    data = await state.get_data()
    title = data.get('book_title', 'Неизвестно')
    author = data.get('book_author', 'Неизвестно')
    
    await callback.message.edit_text(
        f"✅ <b>Название:</b> {title}\n"
        f"✅ <b>Автор:</b> {author}\n"
        f"✅ <b>Описание:</b> Не указано\n\n"
        "💡 <b>Шаг 4/4:</b> Введите путь к файлу книги (или пропустите)\n\n"
        "📁 <b>Поддерживаемые форматы:</b> EPUB, FB2, MOBI\n"
        "📝 <b>Примеры:</b>\n"
        "• books/war_and_peace.epub\n"
        "• books/crime_and_punishment.fb2\n"
        "• books/master_and_margarita.mobi",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data == "skip_file")
async def skip_file(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Пропуск файла книги и завершение добавления
    
    Args:
        callback (CallbackQuery): Callback от кнопки пропуска
        state (FSMContext): Контекст FSM
        
    Returns:
        None
    """
    # Получаем все данные книги
    data = await state.get_data()
    title = data.get('book_title')
    author = data.get('book_author')
    description = data.get('book_description', '')
    
    # Добавляем книгу без файлов
    if book_service.add_book(title, author, description):
        bot_logger.log_admin_action(callback.from_user.id, f"добавление книги: {title}")
        
        success_text = f"""
✅ <b>Книга успешно добавлена!</b>

📚 <b>Название:</b> {title}
👤 <b>Автор:</b> {author}
📝 <b>Описание:</b> {description[:200]}{'...' if len(description) > 200 else ''}
📁 <b>Форматы:</b> Не указаны
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 Добавить еще книгу", callback_data="add_another_book")],
            [InlineKeyboardButton(text="🔙 К панели администратора", callback_data="admin_back")]
        ])
        
        await callback.message.edit_text(success_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback.message.edit_text(
            "❌ Ошибка при добавлении книги!\n"
            "Попробуйте еще раз или обратитесь к администратору."
        )
    
    # Очищаем состояние FSM
    await state.clear()


@router.callback_query(lambda c: c.data == "add_another_book")
async def add_another_book(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Начать добавление еще одной книги
    
    Args:
        callback (CallbackQuery): Callback от кнопки добавления еще одной книги
        state (FSMContext): Контекст FSM
        
    Returns:
        None
    """
    await cmd_addbook(callback.message, state)


@router.message(Command("checkcalibre"))
@admin_required
async def cmd_checkcalibre(message: Message) -> None:
    """
    Проверить установку Calibre и дать инструкции
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    bot_logger.log_admin_action(message.from_user.id, "проверка Calibre")
    
    if book_converter.check_calibre_installed():
        await message.answer(
            "✅ <b>Calibre установлен и работает!</b>\n\n"
            f"📁 <b>Путь:</b> {book_converter.calibre_path}\n"
            f"🖥️ <b>ОС:</b> {'Windows' if book_converter.is_windows else 'Linux/Ubuntu'}\n\n"
            "Теперь можно использовать команду /uploadbook для загрузки книг!",
            parse_mode="HTML"
        )
    else:
        instructions = book_converter.get_installation_instructions()
        await message.answer(
            "❌ <b>Calibre не найден!</b>\n\n"
            f"Для работы с книгами необходимо установить Calibre:\n\n"
            f"{instructions}\n\n"
            "После установки используйте /checkcalibre для проверки.",
            parse_mode="HTML"
        )


@router.message(StateFilter(BookManagementStates.waiting_for_zip_file))
async def process_zip_file(message: Message, state: FSMContext) -> None:
    """
    Обработка ZIP-архива с FB2 файлом
    
    Args:
        message (Message): Сообщение с ZIP-файлом
        state (FSMContext): Контекст FSM
        
    Returns:
        None
    """
    # Проверяем, что это документ
    if not message.document:
        await message.answer(
            "❌ Пожалуйста, отправьте ZIP-архив с FB2 файлом!\n"
            "Файл должен быть в формате ZIP и содержать FB2 файл."
        )
        return
    
    # Проверяем размер файла (максимум 50MB)
    if message.document.file_size > 50 * 1024 * 1024:
        await message.answer(
            "❌ Файл слишком большой!\n"
            "Максимальный размер: 50MB"
        )
        return
    
    # Проверяем расширение файла
    file_name = message.document.file_name.lower()
    if not file_name.endswith('.zip'):
        await message.answer(
            "❌ Файл должен быть в формате ZIP!\n"
            "Пожалуйста, отправьте ZIP-архив."
        )
        return
    
    try:
        # Скачиваем файл
        await message.answer("📥 Скачиваю ZIP-архив...")
        
        file_info = await message.bot.get_file(message.document.file_id)
        zip_path = f"temp/{message.document.file_name}"
        
        # Создаем временную папку
        Path("temp").mkdir(exist_ok=True)
        
        # Скачиваем файл
        await message.bot.download_file(file_info.file_path, zip_path)
        
        await message.answer("🔍 Извлекаю FB2 файл из архива...")
        
        # Извлекаем FB2 файл
        fb2_path = fb2_parser.extract_fb2_from_zip(zip_path)
        if not fb2_path:
            await message.answer(
                "❌ Не удалось извлечь FB2 файл из архива!\n"
                "Убедитесь, что ZIP-архив содержит FB2 файл."
            )
            return
        
        await message.answer("📖 Парсинг метаданных FB2 файла...")
        
        # Парсим метаданные
        metadata = fb2_parser.parse_fb2_metadata(fb2_path)
        if not metadata:
            await message.answer(
                "❌ Не удалось извлечь метаданные из FB2 файла!\n"
                "Убедитесь, что FB2 файл содержит корректные метаданные."
            )
            return
        
        # Проверяем обязательные поля
        title = metadata.get('title')
        author = metadata.get('author')
        
        if not title or not author:
            await message.answer(
                "❌ В FB2 файле отсутствуют обязательные метаданные!\n"
                "Требуются: название и автор книги."
            )
            return
        
        # Проверяем, не существует ли уже такая книга
        existing_book = book_service.get_book(title)
        if existing_book:
            await message.answer(
                f"❌ Книга <b>«{title}»</b> уже существует в библиотеке!",
                parse_mode="HTML"
            )
            return
        
        # Проверяем наличие Calibre
        if not book_converter.check_calibre_installed():
            instructions = book_converter.get_installation_instructions()
            await message.answer(
                f"❌ <b>Calibre не найден!</b>\n\n"
                f"Для конвертации книг необходимо установить Calibre:\n\n"
                f"{instructions}\n\n"
                f"После установки перезапустите бота.",
                parse_mode="HTML"
            )
            return
        
        await message.answer("🔄 Конвертирую в EPUB и MOBI...")
        
        # Конвертируем форматы
        converted_files = book_converter.convert_book_formats(fb2_path)
        
        await message.answer("📤 Загружаю файлы в Telegram...")
        
        # Загружаем файлы в Telegram
        telegram_file_ids = await telegram_uploader.upload_book_formats(
            message.bot, converted_files, message.chat.id
        )
        
        await message.answer("💾 Сохраняю в базу данных...")
        
        # Подготавливаем данные для сохранения
        description = metadata.get('description', '')
        year = metadata.get('year')
        genres = metadata.get('genres', [])
        
        # Создаем расширенные метаданные
        extended_metadata = {
            'year': year,
            'genres': genres,
            'created_date': metadata.get('created_date'),
            'telegram_file_ids': telegram_file_ids
        }
        
        # Сохраняем книгу в базу данных
        if book_service.add_book(title, author, description, converted_files, extended_metadata):
            # Формируем сообщение об успехе
            success_text = f"""
✅ <b>Книга успешно добавлена!</b>

📚 <b>Название:</b> {title}
👤 <b>Автор:</b> {author}
📝 <b>Описание:</b> {description[:200]}{'...' if len(description) > 200 else ''}
            """
            
            if year:
                success_text += f"\n📅 <b>Год:</b> {year}"
            
            if genres:
                success_text += f"\n🎭 <b>Жанры:</b> {', '.join(genres)}"
            
            # Добавляем информацию о форматах
            formats = list(converted_files.keys())
            success_text += f"\n📁 <b>Форматы:</b> {', '.join(formats).upper()}"
            
            success_text += f"\n\n📤 <b>Файлы загружены в Telegram для шаринга!</b>"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 Добавить еще книгу", callback_data="add_another_book")],
                [InlineKeyboardButton(text="🔙 К панели администратора", callback_data="admin_back")]
            ])
            
            await message.answer(success_text, reply_markup=keyboard, parse_mode="HTML")
            
            bot_logger.log_admin_action(message.from_user.id, f"добавление книги из ZIP: {title}")
        else:
            await message.answer(
                "❌ Ошибка при сохранении книги в базу данных!\n"
                "Попробуйте еще раз или обратитесь к администратору."
            )
        
        # Очищаем временные файлы
        temp_files = [zip_path, fb2_path] + list(converted_files.values())
        for file_path in temp_files:
            fb2_parser.clean_temp_files(file_path)
        
        # Очищаем состояние FSM
        await state.clear()
        
    except Exception as e:
        bot_logger.log_error(e, f"ошибка обработки ZIP файла: {message.document.file_name}")
        await message.answer(
            "❌ Произошла ошибка при обработке файла!\n"
            "Попробуйте еще раз или обратитесь к администратору."
        )
        await state.clear() 
"""
@file: handlers/library_handlers.py
@description: Обработчики для работы с библиотекой книг
@dependencies: aiogram, config, utils, services
@created: 2025-01-04
"""

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from datetime import datetime
from pathlib import Path
import json

from config import config
from utils.logger import bot_logger
from utils.access_control import active_user_required, admin_required
from utils.callback_utils import safe_encode_title, safe_decode_title, CallbackPrefixes
from services.books import book_service
from services.users import user_service
from utils.data_manager import data_manager
import base64

router = Router()


@router.message(Command("library"))
@active_user_required
async def cmd_library(message: Message) -> None:
    """
    Показать библиотеку книг
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    bot_logger.log_user_action(message.from_user.id, "просмотр библиотеки")
    
    books = book_service.get_all_books()
    
    if not books:
        await message.answer(
            "📚 <b>Библиотека пуста</b>\n\n"
            "Книги пока не добавлены в библиотеку.",
            parse_mode="HTML"
        )
        return
    
    # Создаем клавиатуру с книгами
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for title, info in books.items():
        author = info.get('author', 'Неизвестный автор')
        safe_title = safe_encode_title(title)
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"📖 {title[:30]}{'...' if len(title) > 30 else ''}",
                callback_data=f"book_{safe_title}"
            )
        ])
    
    await message.answer(
        f"📚 <b>Библиотека книг</b>\n\n"
        f"Всего книг: {len(books)}\n\n"
        f"Выберите книгу для просмотра:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data.startswith("book_"))
async def show_book_card(callback: CallbackQuery) -> None:
    """
    Показать карточку книги
    
    Args:
        callback (CallbackQuery): Callback с данными книги
        
    Returns:
        None
    """
    encoded_title = callback.data.replace("book_", "")
    book_title = safe_decode_title(encoded_title)
    books = book_service.get_all_books()
    
    if book_title not in books:
        await callback.answer("❌ Книга не найдена!")
        return
    
    book_info = books[book_title]
    
    # Формируем карточку книги
    card_text = f"📖 <b>{book_title}</b>\n\n"
    
    if 'author' in book_info:
        card_text += f"👤 <b>Автор:</b> {book_info['author']}\n"
    
    if 'description' in book_info:
        # Обрезаем описание если слишком длинное
        desc = book_info['description']
        if len(desc) > 300:
            desc = desc[:300] + "..."
        card_text += f"📝 <b>Описание:</b> {desc}\n"
    
    if 'year' in book_info:
        card_text += f"📅 <b>Год:</b> {book_info['year']}\n"
    
    if 'genres' in book_info and book_info['genres']:
        genres = ", ".join(book_info['genres'])
        card_text += f"🏷️ <b>Жанры:</b> {genres}\n"
    
    if 'added_at' in book_info:
        added_date = book_info['added_at'][:10]  # Берем только дату
        card_text += f"📅 <b>Добавлена:</b> {added_date}\n"
    
    # Добавляем ссылки на онлайн каталоги
    if 'yandex_books_url' in book_info and book_info['yandex_books_url']:
        card_text += f"📚 <b>Яндекс.Книги:</b> {book_info['yandex_books_url']}\n"
    
    if 'litres_url' in book_info and book_info['litres_url']:
        card_text += f"📖 <b>ЛитРес:</b> {book_info['litres_url']}\n"
    
    if 'audio_format' in book_info and book_info['audio_format']:
        card_text += f"🎧 <b>Аудио:</b> {book_info['audio_format']}\n"
    
    # Создаем клавиатуру для скачивания
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Проверяем доступные форматы
    available_formats = []
    
    if 'fb2_file' in book_info and book_info['fb2_file']:
        available_formats.append(('FB2', 'fb2'))
    if 'epub_file' in book_info and book_info['epub_file']:
        available_formats.append(('EPUB', 'epub'))
    if 'mobi_file' in book_info and book_info['mobi_file']:
        available_formats.append(('MOBI', 'mobi'))
    
    # Добавляем кнопки для скачивания
    if available_formats:
        safe_title = safe_encode_title(book_title)
        for format_name, format_type in available_formats:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"📥 Скачать {format_name}",
                    callback_data=f"download_{safe_title}_{format_type}"
                )
            ])
    
    # Кнопка "Назад к библиотеке"
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад к библиотеке", callback_data="back_to_library")
    ])
    
    await callback.message.edit_text(
        card_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data.startswith("download_"))
async def download_book(callback: CallbackQuery) -> None:
    """
    Скачать книгу в выбранном формате
    
    Args:
        callback (CallbackQuery): Callback с данными скачивания
        
    Returns:
        None
    """
    parts = callback.data.split("_")
    if len(parts) != 3:
        await callback.answer("❌ Ошибка!")
        return
    
    encoded_title = parts[1]
    book_title = safe_decode_title(encoded_title)
    format_type = parts[2]
    
    books = book_service.get_all_books()
    
    if book_title not in books:
        await callback.answer("❌ Книга не найдена!")
        return
    
    book_info = books[book_title]
    file_key = f"{format_type}_file"
    
    if file_key not in book_info or not book_info[file_key]:
        await callback.answer(f"❌ Файл {format_type.upper()} недоступен!")
        return
    
    file_path = book_info[file_key]
    
    try:
        # Проверяем существование файла
        if not Path(file_path).exists():
            await callback.answer("❌ Файл не найден на сервере!")
            return
        
        # Отправляем файл
        await callback.message.bot.send_document(
            chat_id=callback.from_user.id,
            document=FSInputFile(file_path),
            caption=f"📚 {book_title} ({format_type.upper()})"
        )
        
        await callback.answer("✅ Файл отправлен!")
        
    except Exception as e:
        bot_logger.log_error(e, f"ошибка отправки файла: {file_path}")
        await callback.answer("❌ Ошибка отправки файла!")


@router.callback_query(lambda c: c.data == "back_to_library")
async def back_to_library(callback: CallbackQuery) -> None:
    """
    Вернуться к списку книг
    
    Args:
        callback (CallbackQuery): Callback
        
    Returns:
        None
    """
    books = book_service.get_all_books()
    
    if not books:
        await callback.message.edit_text(
            "📚 <b>Библиотека пуста</b>\n\n"
            "Книги пока не добавлены в библиотеку.",
            parse_mode="HTML"
        )
        return
    
    # Создаем клавиатуру с книгами
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for title, info in books.items():
        author = info.get('author', 'Неизвестный автор')
        safe_title = safe_encode_title(title)
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"📖 {title[:30]}{'...' if len(title) > 30 else ''}",
                callback_data=f"book_{safe_title}"
            )
        ])
    
    await callback.message.edit_text(
        f"📚 <b>Библиотека книг</b>\n\n"
        f"Всего книг: {len(books)}\n\n"
        f"Выберите книгу для просмотра:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(Command("search"))
@active_user_required
async def cmd_search(message: Message) -> None:
    """
    Поиск книг в библиотеке
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    bot_logger.log_user_action(message.from_user.id, "поиск книг")
    
    await message.answer(
        "🔍 <b>Поиск книг</b>\n\n"
        "Отправьте название книги или автора для поиска.\n"
        "Или используйте /library для просмотра всех книг.",
        parse_mode="HTML"
    )


@router.message(lambda message: message.text and not message.text.startswith('/'))
@active_user_required
async def search_books(message: Message) -> None:
    """
    Обработка поискового запроса
    
    Args:
        message (Message): Сообщение с поисковым запросом
        
    Returns:
        None
    """
    query = message.text.lower().strip()
    
    if len(query) < 2:
        await message.answer("🔍 Введите минимум 2 символа для поиска.")
        return
    
    books = book_service.get_all_books()
    found_books = []
    
    for title, info in books.items():
        # Поиск по названию
        if query in title.lower():
            found_books.append((title, info))
            continue
        
        # Поиск по автору
        if 'author' in info and query in info['author'].lower():
            found_books.append((title, info))
            continue
        
        # Поиск по описанию
        if 'description' in info and query in info['description'].lower():
            found_books.append((title, info))
            continue
    
    if not found_books:
        await message.answer(
            f"🔍 <b>Поиск: {message.text}</b>\n\n"
            f"Книги не найдены. Попробуйте другой запрос.",
            parse_mode="HTML"
        )
        return
    
    # Создаем клавиатуру с найденными книгами
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for title, info in found_books:
        safe_title = safe_encode_title(title)
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"📖 {title[:30]}{'...' if len(title) > 30 else ''}",
                callback_data=f"book_{safe_title}"
            )
        ])
    
    await message.answer(
        f"🔍 <b>Поиск: {message.text}</b>\n\n"
        f"Найдено книг: {len(found_books)}\n\n"
        f"Выберите книгу:",
        reply_markup=keyboard,
        parse_mode="HTML"
    ) 
"""
@file: handlers/admin_book_handlers.py
@description: Обработчики для админов по управлению ссылками на книги
@dependencies: aiogram, config, utils, services
@created: 2025-01-04
"""

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime
from pathlib import Path
import json

from config import config
from utils.logger import bot_logger
from utils.access_control import admin_required
from services.books import book_service
from utils.states import BookLinkStates
from utils.data_manager import data_manager
import base64

router = Router()


import hashlib

def safe_encode_title(title: str) -> str:
    """
    Безопасно кодирует название книги для использования в callback_data
    
    Args:
        title (str): Название книги
        
    Returns:
        str: Закодированное название
    """
    # Используем хеш названия для безопасного callback_data
    return hashlib.md5(title.encode('utf-8')).hexdigest()[:16]


def safe_decode_title(encoded_title: str) -> str:
    """
    Декодирует название книги из callback_data
    
    Args:
        encoded_title (str): Закодированное название
        
    Returns:
        str: Декодированное название
    """
    # Для хеша нам нужно найти оригинальное название по хешу
    books = book_service.get_all_books()
    for title in books.keys():
        if safe_encode_title(title) == encoded_title:
            return title
    return encoded_title


@router.message(Command("editlinks"))
@admin_required
async def cmd_editlinks(message: Message) -> None:
    """
    Редактирование ссылок на книги
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    bot_logger.log_admin_action(message.from_user.id, "редактирование ссылок на книги")
    
    books = book_service.get_all_books()
    
    if not books:
        await message.answer(
            "📚 <b>Нет книг для редактирования</b>\n\n"
            "Сначала добавьте книги в библиотеку.",
            parse_mode="HTML"
        )
        return
    
    # Создаем клавиатуру с книгами
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for title, info in books.items():
        safe_title = safe_encode_title(title)
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"📖 {title[:30]}{'...' if len(title) > 30 else ''}",
                callback_data=f"editlinks_{safe_title}"
            )
        ])
    
    await message.answer(
        "🔗 <b>Редактирование ссылок на книги</b>\n\n"
        f"Всего книг: {len(books)}\n\n"
        "Выберите книгу для редактирования ссылок:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data.startswith("editlinks_"))
async def show_book_links(callback: CallbackQuery) -> None:
    """
    Показать ссылки книги для редактирования
    
    Args:
        callback (CallbackQuery): Callback с данными книги
        
    Returns:
        None
    """
    encoded_title = callback.data.replace("editlinks_", "")
    book_title = safe_decode_title(encoded_title)
    books = book_service.get_all_books()
    
    if book_title not in books:
        await callback.answer("❌ Книга не найдена!")
        return
    
    book_info = books[book_title]
    
    # Формируем информацию о ссылках
    links_text = f"🔗 <b>Ссылки для книги: {book_title}</b>\n\n"
    
    yandex_url = book_info.get('yandex_books_url', '')
    litres_url = book_info.get('litres_url', '')
    audio_format = book_info.get('audio_format', '')
    
    links_text += f"📚 <b>Яндекс.Книги:</b> {yandex_url if yandex_url else 'Не указана'}\n"
    links_text += f"📖 <b>ЛитРес:</b> {litres_url if litres_url else 'Не указана'}\n"
    links_text += f"🎧 <b>Аудиоформат:</b> {audio_format if audio_format else 'Не указан'}\n"
    
    # Создаем клавиатуру для редактирования
    safe_title = safe_encode_title(book_title)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Яндекс.Книги", callback_data=f"link_yandex_{safe_title}")],
        [InlineKeyboardButton(text="📖 ЛитРес", callback_data=f"link_litres_{safe_title}")],
        [InlineKeyboardButton(text="🎧 Аудиоформат", callback_data=f"link_audio_{safe_title}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_editlinks")]
    ])
    
    await callback.message.edit_text(
        links_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data.startswith("link_yandex_"))
async def edit_yandex_link(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Редактировать ссылку на Яндекс.Книги
    
    Args:
        callback (CallbackQuery): Callback
        state (FSMContext): Состояние FSM
        
    Returns:
        None
    """
    encoded_title = callback.data.replace("link_yandex_", "")
    book_title = safe_decode_title(encoded_title)
    
    await state.set_state(BookLinkStates.waiting_for_yandex_url)
    await state.update_data(book_title=book_title)
    
    await callback.message.edit_text(
        f"📚 <b>Редактирование ссылки Яндекс.Книги</b>\n\n"
        f"Книга: {book_title}\n\n"
        "Отправьте ссылку на Яндекс.Книги или 'нет' для удаления:",
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data.startswith("link_litres_"))
async def edit_litres_link(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Редактировать ссылку на ЛитРес
    
    Args:
        callback (CallbackQuery): Callback
        state (FSMContext): Состояние FSM
        
    Returns:
        None
    """
    encoded_title = callback.data.replace("link_litres_", "")
    book_title = safe_decode_title(encoded_title)
    
    await state.set_state(BookLinkStates.waiting_for_litres_url)
    await state.update_data(book_title=book_title)
    
    await callback.message.edit_text(
        f"📖 <b>Редактирование ссылки ЛитРес</b>\n\n"
        f"Книга: {book_title}\n\n"
        "Отправьте ссылку на ЛитРес или 'нет' для удаления:",
        parse_mode="HTML"
    )


@router.callback_query(lambda c: c.data.startswith("link_audio_"))
async def edit_audio_format(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Редактировать аудиоформат
    
    Args:
        callback (CallbackQuery): Callback
        state (FSMContext): Состояние FSM
        
    Returns:
        None
    """
    encoded_title = callback.data.replace("link_audio_", "")
    book_title = safe_decode_title(encoded_title)
    
    await state.set_state(BookLinkStates.waiting_for_audio_format)
    await state.update_data(book_title=book_title)
    
    await callback.message.edit_text(
        f"🎧 <b>Редактирование аудиоформата</b>\n\n"
        f"Книга: {book_title}\n\n"
        "Отправьте информацию об аудиоформате или 'нет' для удаления:",
        parse_mode="HTML"
    )


@router.message(StateFilter(BookLinkStates.waiting_for_yandex_url))
async def process_yandex_url(message: Message, state: FSMContext) -> None:
    """
    Обработать ссылку на Яндекс.Книги
    
    Args:
        message (Message): Сообщение с ссылкой
        state (FSMContext): Состояние FSM
        
    Returns:
        None
    """
    data = await state.get_data()
    book_title = data.get('book_title')
    
    url = message.text.strip()
    if url.lower() == 'нет':
        url = ""
    
    # Обновляем ссылку в базе данных
    books = book_service.get_all_books()
    if book_title in books:
        books[book_title]['yandex_books_url'] = url
        data_manager.save_json(config.database.books_file, books)
        
        await message.answer(
            f"✅ <b>Ссылка обновлена!</b>\n\n"
            f"Книга: {book_title}\n"
            f"Яндекс.Книги: {url if url else 'Удалена'}",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Книга не найдена!")
    
    await state.clear()


@router.message(StateFilter(BookLinkStates.waiting_for_litres_url))
async def process_litres_url(message: Message, state: FSMContext) -> None:
    """
    Обработать ссылку на ЛитРес
    
    Args:
        message (Message): Сообщение с ссылкой
        state (FSMContext): Состояние FSM
        
    Returns:
        None
    """
    data = await state.get_data()
    book_title = data.get('book_title')
    
    url = message.text.strip()
    if url.lower() == 'нет':
        url = ""
    
    # Обновляем ссылку в базе данных
    books = book_service.get_all_books()
    if book_title in books:
        books[book_title]['litres_url'] = url
        data_manager.save_json(config.database.books_file, books)
        
        await message.answer(
            f"✅ <b>Ссылка обновлена!</b>\n\n"
            f"Книга: {book_title}\n"
            f"ЛитРес: {url if url else 'Удалена'}",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Книга не найдена!")
    
    await state.clear()


@router.message(StateFilter(BookLinkStates.waiting_for_audio_format))
async def process_audio_format(message: Message, state: FSMContext) -> None:
    """
    Обработать аудиоформат
    
    Args:
        message (Message): Сообщение с аудиоформатом
        state (FSMContext): Состояние FSM
        
    Returns:
        None
    """
    data = await state.get_data()
    book_title = data.get('book_title')
    
    audio_info = message.text.strip()
    if audio_info.lower() == 'нет':
        audio_info = ""
    
    # Обновляем аудиоформат в базе данных
    books = book_service.get_all_books()
    if book_title in books:
        books[book_title]['audio_format'] = audio_info
        data_manager.save_json(config.database.books_file, books)
        
        await message.answer(
            f"✅ <b>Аудиоформат обновлен!</b>\n\n"
            f"Книга: {book_title}\n"
            f"Аудио: {audio_info if audio_info else 'Удален'}",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Книга не найдена!")
    
    await state.clear()


@router.callback_query(lambda c: c.data == "back_to_editlinks")
async def back_to_editlinks(callback: CallbackQuery) -> None:
    """
    Вернуться к списку книг для редактирования ссылок
    
    Args:
        callback (CallbackQuery): Callback
        
    Returns:
        None
    """
    books = book_service.get_all_books()
    
    if not books:
        await callback.message.edit_text(
            "📚 <b>Нет книг для редактирования</b>\n\n"
            "Сначала добавьте книги в библиотеку.",
            parse_mode="HTML"
        )
        return
    
    # Создаем клавиатуру с книгами
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for title, info in books.items():
        safe_title = safe_encode_title(title)
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"📖 {title[:30]}{'...' if len(title) > 30 else ''}",
                callback_data=f"editlinks_{safe_title}"
            )
        ])
    
    await callback.message.edit_text(
        "🔗 <b>Редактирование ссылок на книги</b>\n\n"
        f"Всего книг: {len(books)}\n\n"
        "Выберите книгу для редактирования ссылок:",
        reply_markup=keyboard,
        parse_mode="HTML"
    ) 
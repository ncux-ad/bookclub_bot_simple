"""
@file: handlers/book_handlers.py
@description: Обработчики для работы с книгами
@dependencies: aiogram, services.books, utils.states, utils.access_control, utils.logger
@created: 2025-01-03
"""

import os
import tempfile
from pathlib import Path
from typing import Any

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.books import book_service
from utils.states import BookAddStates
from utils.access_control import admin_required
from utils.logger import bot_logger
from keyboards.inline import create_book_confirmation_keyboard, create_skip_keyboard

router = Router()


@router.message(Command("addbook"))
@admin_required
async def cmd_addbook(message: Message, state: FSMContext) -> None:
    """
    Начать процесс добавления книги
    
    Запрашивает ZIP архив с FB2 файлом
    """
    bot_logger.log_user_action(message.from_user.id, "начало добавления книги")
    
    await state.set_state(BookAddStates.waiting_for_book_file)
    
    await message.answer(
        "📚 <b>Добавление новой книги</b>\n\n"
        "Отправьте ZIP архив с FB2 файлом книги.\n\n"
        "📋 <b>Требования:</b>\n"
        "• ZIP архив должен содержать FB2 файл\n"
        "• Файл должен быть корректным FB2 форматом\n"
        "• Размер архива не более 50 МБ\n\n"
        "💡 <b>Совет:</b> Если у вас нет ZIP архива, "
        "можете отправить FB2 файл напрямую.",
        parse_mode="HTML"
    )


@router.message(BookAddStates.waiting_for_book_file, F.document)
async def process_book_file(message: Message, state: FSMContext) -> None:
    """
    Обработка загруженного файла книги
    """
    try:
        # Проверяем тип файла
        file_name = message.document.file_name.lower()
        
        if not (file_name.endswith('.zip') or file_name.endswith('.fb2')):
            await message.answer(
                "❌ Неподдерживаемый формат файла.\n"
                "Отправьте ZIP архив или FB2 файл."
            )
            return
        
        # Скачиваем файл
        file_info = await message.bot.get_file(message.document.file_id)
        downloaded_file = await message.bot.download_file(file_info.file_path)
        
        # Сохраняем во временную директорию
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file_name).suffix) as tmp_file:
            tmp_file.write(downloaded_file.read())
            temp_path = tmp_file.name
        
        try:
            # Обрабатываем файл
            if file_name.endswith('.zip'):
                book_data = book_service.process_zip_archive(temp_path, str(message.from_user.id))
            else:  # .fb2
                # TODO: Добавить прямую обработку FB2 файлов
                await message.answer("❌ Прямая обработка FB2 файлов пока не поддерживается. Используйте ZIP архив.")
                return
            
            # Сохраняем данные в FSM
            await state.update_data(book_data=book_data, temp_file_path=temp_path)
            
            # Показываем извлеченные данные
            title = book_data.get('title', 'Неизвестное название')
            author = book_data.get('author', 'Неизвестный автор')
            description = book_data.get('description', 'Описание отсутствует')
            
            await message.answer(
                f"📖 <b>Найдена книга:</b>\n\n"
                f"📚 <b>Название:</b> {title}\n"
                f"✍️ <b>Автор:</b> {author}\n"
                f"📝 <b>Описание:</b>\n{description[:200]}{'...' if len(description) > 200 else ''}\n\n"
                f"Хотите ли вы изменить какие-либо данные?",
                parse_mode="HTML",
                reply_markup=create_book_confirmation_keyboard()
            )
            
            await state.set_state(BookAddStates.waiting_for_confirmation)
            
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        bot_logger.logger.error(f"Ошибка обработки файла книги: {e}")
        await message.answer(
            "❌ Ошибка обработки файла.\n"
            "Убедитесь, что файл корректный и попробуйте снова."
        )
        await state.clear()


@router.message(BookAddStates.waiting_for_book_file)
async def process_invalid_file(message: Message) -> None:
    """Обработка некорректного файла"""
    await message.answer(
        "❌ Пожалуйста, отправьте ZIP архив или FB2 файл."
    )


@router.callback_query(BookAddStates.waiting_for_confirmation, F.data == "edit_title")
async def edit_book_title(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование названия книги"""
    await state.set_state(BookAddStates.waiting_for_book_title)
    
    await callback.message.edit_text(
        "📚 <b>Введите новое название книги:</b>",
        parse_mode="HTML",
        reply_markup=create_skip_keyboard()
    )
    await callback.answer()


@router.callback_query(BookAddStates.waiting_for_confirmation, F.data == "edit_author")
async def edit_book_author(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование автора книги"""
    await state.set_state(BookAddStates.waiting_for_book_author)
    
    await callback.message.edit_text(
        "✍️ <b>Введите нового автора книги:</b>",
        parse_mode="HTML",
        reply_markup=create_skip_keyboard()
    )
    await callback.answer()


@router.callback_query(BookAddStates.waiting_for_confirmation, F.data == "edit_description")
async def edit_book_description(callback: CallbackQuery, state: FSMContext) -> None:
    """Редактирование описания книги"""
    await state.set_state(BookAddStates.waiting_for_book_description)
    
    await callback.message.edit_text(
        "📝 <b>Введите новое описание книги:</b>\n\n"
        "💡 <b>Совет:</b> Можете использовать HTML разметку",
        parse_mode="HTML",
        reply_markup=create_skip_keyboard()
    )
    await callback.answer()


@router.callback_query(BookAddStates.waiting_for_confirmation, F.data == "add_yandex")
async def add_yandex_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Добавление ссылки на Яндекс.Книги"""
    await state.set_state(BookAddStates.waiting_for_yandex_link)
    
    await callback.message.edit_text(
        "🔗 <b>Введите ссылку на Яндекс.Книги:</b>\n\n"
        "Пример: https://market.yandex.ru/product/...",
        parse_mode="HTML",
        reply_markup=create_skip_keyboard()
    )
    await callback.answer()


@router.callback_query(BookAddStates.waiting_for_confirmation, F.data == "add_litres")
async def add_litres_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Добавление ссылки на ЛитРес"""
    await state.set_state(BookAddStates.waiting_for_litres_link)
    
    await callback.message.edit_text(
        "🔗 <b>Введите ссылку на ЛитРес:</b>\n\n"
        "Пример: https://www.litres.ru/...",
        parse_mode="HTML",
        reply_markup=create_skip_keyboard()
    )
    await callback.answer()


@router.callback_query(BookAddStates.waiting_for_confirmation, F.data == "add_audio")
async def add_audio_link(callback: CallbackQuery, state: FSMContext) -> None:
    """Добавление ссылки на аудиокнигу"""
    await state.set_state(BookAddStates.waiting_for_audio_link)
    
    await callback.message.edit_text(
        "🎧 <b>Введите ссылку на аудиокнигу:</b>\n\n"
        "Пример: https://www.litres.ru/audio/...",
        parse_mode="HTML",
        reply_markup=create_skip_keyboard()
    )
    await callback.answer()


@router.callback_query(BookAddStates.waiting_for_confirmation, F.data == "confirm_add")
async def confirm_add_book(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждение добавления книги"""
    data = await state.get_data()
    book_data = data.get('book_data', {})
    
    try:
        # Добавляем книгу в базу
        book_id = book_service.add_book(book_data)
        
        await callback.message.edit_text(
            f"✅ <b>Книга успешно добавлена!</b>\n\n"
            f"📚 <b>Название:</b> {book_data.get('title')}\n"
            f"✍️ <b>Автор:</b> {book_data.get('author')}\n"
            f"🆔 <b>ID:</b> <code>{book_id}</code>\n\n"
            f"Книга доступна в библиотеке.",
            parse_mode="HTML"
        )
        
        bot_logger.log_user_action(callback.from_user.id, f"добавлена книга: {book_data.get('title')}")
        
    except Exception as e:
        bot_logger.logger.error(f"Ошибка добавления книги: {e}")
        await callback.message.edit_text(
            "❌ Ошибка добавления книги в базу данных.\n"
            "Попробуйте позже."
        )
    
    await state.clear()
    await callback.answer()


# Обработчики для редактирования данных
@router.message(BookAddStates.waiting_for_book_title)
async def process_book_title(message: Message, state: FSMContext) -> None:
    """Обработка нового названия книги"""
    if message.text.lower() == "пропустить":
        await message.answer("Название оставлено без изменений.")
    else:
        data = await state.get_data()
        book_data = data.get('book_data', {})
        book_data['title'] = message.text
        await state.update_data(book_data=book_data)
        await message.answer(f"✅ Название изменено на: {message.text}")
    
    await show_book_preview(message, state)


@router.message(BookAddStates.waiting_for_book_author)
async def process_book_author(message: Message, state: FSMContext) -> None:
    """Обработка нового автора книги"""
    if message.text.lower() == "пропустить":
        await message.answer("Автор оставлен без изменений.")
    else:
        data = await state.get_data()
        book_data = data.get('book_data', {})
        book_data['author'] = message.text
        await state.update_data(book_data=book_data)
        await message.answer(f"✅ Автор изменен на: {message.text}")
    
    await show_book_preview(message, state)


@router.message(BookAddStates.waiting_for_book_description)
async def process_book_description(message: Message, state: FSMContext) -> None:
    """Обработка нового описания книги"""
    if message.text.lower() == "пропустить":
        await message.answer("Описание оставлено без изменений.")
    else:
        data = await state.get_data()
        book_data = data.get('book_data', {})
        book_data['description'] = message.text
        await state.update_data(book_data=book_data)
        await message.answer("✅ Описание изменено.")
    
    await show_book_preview(message, state)


@router.message(BookAddStates.waiting_for_yandex_link)
async def process_yandex_link(message: Message, state: FSMContext) -> None:
    """Обработка ссылки на Яндекс.Книги"""
    if message.text.lower() == "пропустить":
        await message.answer("Ссылка на Яндекс.Книги не добавлена.")
    else:
        data = await state.get_data()
        book_data = data.get('book_data', {})
        if 'links' not in book_data:
            book_data['links'] = {}
        book_data['links']['yandex'] = message.text
        await state.update_data(book_data=book_data)
        await message.answer("✅ Ссылка на Яндекс.Книги добавлена.")
    
    await show_book_preview(message, state)


@router.message(BookAddStates.waiting_for_litres_link)
async def process_litres_link(message: Message, state: FSMContext) -> None:
    """Обработка ссылки на ЛитРес"""
    if message.text.lower() == "пропустить":
        await message.answer("Ссылка на ЛитРес не добавлена.")
    else:
        data = await state.get_data()
        book_data = data.get('book_data', {})
        if 'links' not in book_data:
            book_data['links'] = {}
        book_data['links']['litres'] = message.text
        await state.update_data(book_data=book_data)
        await message.answer("✅ Ссылка на ЛитРес добавлена.")
    
    await show_book_preview(message, state)


@router.message(BookAddStates.waiting_for_audio_link)
async def process_audio_link(message: Message, state: FSMContext) -> None:
    """Обработка ссылки на аудиокнигу"""
    if message.text.lower() == "пропустить":
        await message.answer("Ссылка на аудиокнигу не добавлена.")
    else:
        data = await state.get_data()
        book_data = data.get('book_data', {})
        if 'links' not in book_data:
            book_data['links'] = {}
        book_data['links']['audio'] = message.text
        await state.update_data(book_data=book_data)
        await message.answer("✅ Ссылка на аудиокнигу добавлена.")
    
    await show_book_preview(message, state)


async def show_book_preview(message: Message, state: FSMContext) -> None:
    """Показать предварительный просмотр книги"""
    data = await state.get_data()
    book_data = data.get('book_data', {})
    
    title = book_data.get('title', 'Неизвестное название')
    author = book_data.get('author', 'Неизвестный автор')
    description = book_data.get('description', 'Описание отсутствует')
    links = book_data.get('links', {})
    
    preview_text = (
        f"📖 <b>Предварительный просмотр:</b>\n\n"
        f"📚 <b>Название:</b> {title}\n"
        f"✍️ <b>Автор:</b> {author}\n"
        f"📝 <b>Описание:</b>\n{description[:200]}{'...' if len(description) > 200 else ''}\n\n"
    )
    
    if links.get('yandex'):
        preview_text += f"🔗 <b>Яндекс.Книги:</b> {links['yandex']}\n"
    if links.get('litres'):
        preview_text += f"🔗 <b>ЛитРес:</b> {links['litres']}\n"
    if links.get('audio'):
        preview_text += f"🎧 <b>Аудиокнига:</b> {links['audio']}\n"
    
    preview_text += "\nХотите ли вы изменить какие-либо данные?"
    
    await message.answer(
        preview_text,
        parse_mode="HTML",
        reply_markup=create_book_confirmation_keyboard()
    )
    
    await state.set_state(BookAddStates.waiting_for_confirmation)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Отмена текущей операции"""
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer("❌ Операция отменена.")
    else:
        await message.answer("Нет активной операции для отмены.") 
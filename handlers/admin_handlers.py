"""
@file: handlers/admin_handlers.py
@description: Обработчики команд администраторов
@dependencies: aiogram, config, utils
@created: 2024-01-15
"""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import config
from utils.data_manager import data_manager
from utils.logger import bot_logger
from keyboards.inline import create_admin_keyboard
from services.users import user_service
from services.books import book_service
from services.events import event_service

router = Router()


def admin_required(func):
    """
    Декоратор для проверки прав администратора
    
    Проверяет, имеет ли пользователь права администратора.
    Если нет - отправляет сообщение об ошибке и логирует попытку доступа.
    
    Args:
        func: Функция-обработчик для защиты
        
    Returns:
        wrapper: Обернутая функция с проверкой прав
    """
    async def wrapper(message: Message, *args, **kwargs):
        if not config.is_admin(message.from_user.id):
            bot_logger.log_security_event("неавторизованный_доступ", message.from_user.id, "админская команда")
            await message.answer("❌ У вас нет прав администратора!")
            return
        return await func(message, *args, **kwargs)
    return wrapper


@router.message(Command("admin"))
@admin_required
async def cmd_admin(message: Message, **kwargs) -> None:
    """
    Панель администратора
    
    Отображает главное меню администратора с доступными функциями:
    - Просмотр статистики
    - Управление пользователями
    - Управление книгами
    - Управление событиями
    
    Args:
        message (Message): Сообщение с командой администратора
        
    Returns:
        None
    """
    bot_logger.log_admin_action(message.from_user.id, "открытие панели администратора")
    
    keyboard = create_admin_keyboard()
    await message.answer("🔧 <b>Панель администратора</b>\nВыберите действие:", 
                        reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: CallbackQuery) -> None:
    """
    Показать статистику клуба
    
    Отображает общую статистику книжного клуба:
    - Количество пользователей (всего/активных)
    - Количество книг в библиотеке
    - Количество событий (всего/предстоящих)
    
    Args:
        callback (CallbackQuery): Callback от кнопки статистики
        
    Returns:
        None
    """
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    bot_logger.log_admin_action(callback.from_user.id, "просмотр статистики")
    
    user_stats = user_service.get_user_stats()
    books = book_service.get_all_books()
    event_stats = event_service.get_event_stats()
    
    text = f"""
📊 <b>Статистика клуба:</b>

👥 Пользователи: {user_stats['total']} (активных: {user_stats['active']})
📈 Новых сегодня: {user_stats['new_today']}
📚 Книг в библиотеке: {len(books)}
📅 Событий: {event_stats['total']} (предстоящих: {event_stats['upcoming']})
    """
    
    await callback.message.edit_text(text, parse_mode="HTML")


@router.callback_query(lambda c: c.data == "admin_users")
async def admin_users(callback: CallbackQuery) -> None:
    """Показать список пользователей"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    bot_logger.log_admin_action(callback.from_user.id, "просмотр пользователей")
    
    users = user_service.get_all_users()
    
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


@router.callback_query(lambda c: c.data == "admin_books")
async def admin_books(callback: CallbackQuery) -> None:
    """Управление книгами"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    bot_logger.log_admin_action(callback.from_user.id, "просмотр книг")
    
    books = book_service.get_all_books()
    
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


@router.callback_query(lambda c: c.data == "admin_events")
async def admin_events(callback: CallbackQuery) -> None:
    """Управление событиями"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    bot_logger.log_admin_action(callback.from_user.id, "просмотр событий")
    
    events = event_service.get_all_events()
    
    if not events:
        text = "📅 Событий пока нет"
    else:
        text = "📅 <b>Запланированные события:</b>\n\n"
        for event_id, event in events.items():
            text += f"📖 {event.get('title', 'Без названия')}\n"
            text += f"📅 {event.get('date', 'Не указана')}\n"
            text += f"⏰ {event.get('time', 'Не указано')}\n\n"
    
    await callback.message.edit_text(text, parse_mode="HTML")


@router.callback_query(lambda c: c.data == "admin_back")
async def admin_back(callback: CallbackQuery) -> None:
    """Возврат в главное меню администратора"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    keyboard = create_admin_keyboard()
    await callback.message.edit_text("🔧 <b>Панель администратора</b>\nВыберите действие:", 
                                    reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("settag"))
async def cmd_settag(message: Message) -> None:
    """
    Установить тег пользователю (только для администраторов)
    
    Формат: /settag <user_id> <tag>
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    if not config.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора!")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Укажите ID пользователя и тег: /settag <user_id> <tag>")
        return
    
    user_id = args[1]
    tag = args[2]
    
    if user_service.add_user_tag(user_id, tag):
        bot_logger.log_admin_action(message.from_user.id, f"установка тега '{tag}' пользователю {user_id}")
        await message.answer(f"✅ Тег '{tag}' установлен пользователю {user_id}")
    else:
        await message.answer(f"❌ Ошибка установки тега для пользователя {user_id}") 
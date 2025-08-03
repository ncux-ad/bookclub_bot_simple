"""
@file: handlers/admin_handlers.py
@description: Обработчики команд администраторов
@dependencies: aiogram, config, utils
@created: 2024-01-15
"""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

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


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """
    Показать расширенную статистику (только для администраторов)
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    if not config.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора!")
        return
    
    user_stats = user_service.get_user_stats()
    books = book_service.get_all_books()
    event_stats = event_service.get_event_stats()
    
    # Получаем дополнительную статистику
    users = user_service.get_all_users()
    active_users = len([u for u in users.values() if u.get('status') == 'active'])
    inactive_users = len([u for u in users.values() if u.get('status') == 'inactive'])
    banned_users = len([u for u in users.values() if u.get('status') == 'banned'])
    
    # Статистика по дням
    today = datetime.now().date().isoformat()
    week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
    
    new_this_week = 0
    for user_data in users.values():
        first_interaction = user_data.get('first_interaction', '')
        if first_interaction.startswith(today) or (first_interaction >= week_ago and first_interaction <= today):
            new_this_week += 1
    
    stats_text = f"""
📊 <b>Расширенная статистика клуба:</b>

👥 <b>Пользователи:</b>
   • Всего: {user_stats['total']}
   • Активных: {active_users}
   • Неактивных: {inactive_users}
   • Заблокированных: {banned_users}
   • Новых сегодня: {user_stats['new_today']}
   • Новых за неделю: {new_this_week}

📚 <b>Библиотека:</b>
   • Книг в библиотеке: {len(books)}

📅 <b>События:</b>
   • Всего событий: {event_stats['total']}
   • Предстоящих: {event_stats['upcoming']}

📈 <b>Активность:</b>
   • Процент активных: {(active_users/user_stats['total']*100):.1f}% (от общего числа)
    """
    
    bot_logger.log_admin_action(message.from_user.id, "просмотр расширенной статистики")
    await message.answer(stats_text, parse_mode="HTML")


@router.message(Command("ban"))
async def cmd_ban(message: Message) -> None:
    """
    Заблокировать пользователя (только для администраторов)
    
    Формат: /ban <user_id>
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    if not config.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажите ID пользователя: /ban <user_id>")
        return
    
    user_id = args[1]
    
    if user_service.ban_user(user_id):
        bot_logger.log_admin_action(message.from_user.id, f"блокировка пользователя {user_id}")
        await message.answer(f"✅ Пользователь {user_id} заблокирован")
    else:
        await message.answer(f"❌ Ошибка блокировки пользователя {user_id}")


@router.message(Command("unban"))
async def cmd_unban(message: Message) -> None:
    """
    Разблокировать пользователя (только для администраторов)
    
    Формат: /unban <user_id>
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    if not config.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажите ID пользователя: /unban <user_id>")
        return
    
    user_id = args[1]
    
    if user_service.unban_user(user_id):
        bot_logger.log_admin_action(message.from_user.id, f"разблокировка пользователя {user_id}")
        await message.answer(f"✅ Пользователь {user_id} разблокирован")
    else:
        await message.answer(f"❌ Ошибка разблокировки пользователя {user_id}")


@router.message(Command("userinfo"))
async def cmd_userinfo(message: Message) -> None:
    """
    Показать информацию о пользователе (только для администраторов)
    
    Формат: /userinfo <user_id>
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    if not config.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора!")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажите ID пользователя: /userinfo <user_id>")
        return
    
    user_id = args[1]
    user_info = user_service.get_user(user_id)
    
    if not user_info:
        await message.answer(f"❌ Пользователь {user_id} не найден")
        return
    
    # Формируем детальную информацию о пользователе
    username = user_info.get('username', '')
    if username and not username.startswith('@'):
        username = f"@{username}"
    
    tags = user_info.get('tags', [])
    if isinstance(tags, str):
        tags = [tags]
    elif not isinstance(tags, list):
        tags = []
    
    tags_display = ", ".join(tags) if tags else "Не указаны"
    
    info_text = f"""
👤 <b>Информация о пользователе:</b>

🆔 ID: <code>{user_id}</code>
🔹 Имя: {user_info.get('name', 'Не указано')}
📌 Username: {username if username else 'Не указан'}
📅 Дата регистрации: {user_info.get('registered_at', 'Не указана')}
📍 Статус: {user_info.get('status', 'Не указан')}
🏷️ Теги: {tags_display}
    """
    
    if user_info.get('activated_at'):
        info_text += f"\n✅ Активирован: {user_info.get('activated_at')}"
    
    bot_logger.log_admin_action(message.from_user.id, f"просмотр информации о пользователе {user_id}")
    await message.answer(info_text, parse_mode="HTML", disable_web_page_preview=True) 
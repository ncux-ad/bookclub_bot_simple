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
from utils.access_control import admin_required
from utils.security import security_manager
from keyboards.inline import create_admin_keyboard
from services.users import user_service
from services.books import book_service
from services.events import event_service

router = Router()





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
    Установить тег пользователю
    
    Формат: /settag <user_id> <tag>
    Пример: /settag 123456789 Модератор
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    if not config.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора!")
        return
    
    try:
        # Парсим аргументы команды
        args = message.text.split()[1:]
        if len(args) < 2:
            await message.answer(
                "❌ Неверный формат команды!\n"
                "Используйте: /settag <user_id> <tag>\n"
                "Пример: /settag 123456789 Модератор"
            )
            return
        
        user_id = args[0]
        tag = ' '.join(args[1:])
        
        # Добавляем тег пользователю
        if user_service.add_user_tag(user_id, tag):
            await message.answer(f"✅ Тег '{tag}' успешно добавлен пользователю {user_id}")
            bot_logger.log_admin_action(message.from_user.id, f"установка тега '{tag}' пользователю {user_id}")
        else:
            await message.answer(f"❌ Ошибка при добавлении тега пользователю {user_id}")
            
    except Exception as e:
        await message.answer("❌ Произошла ошибка при выполнении команды")
        bot_logger.log_error(e, f"settag command error, user: {message.from_user.id}")


@router.message(Command("setrole"))
@admin_required
async def cmd_setrole(message: Message, **kwargs) -> None:
    """
    Установить роль пользователю
    
    Формат: /setrole <user_id> <role>
    Доступные роли: user, moderator, admin
    Пример: /setrole 123456789 moderator
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    try:
        # Парсим аргументы команды
        args = message.text.split()[1:]
        if len(args) != 2:
            await message.answer(
                "❌ Неверный формат команды!\n"
                "Используйте: /setrole <user_id> <role>\n"
                "Доступные роли: user, moderator, admin\n"
                "Пример: /setrole 123456789 moderator"
            )
            return
        
        user_id = args[0]
        role = args[1].lower()
        
        # Проверяем валидность роли
        valid_roles = ['user', 'moderator', 'admin']
        if role not in valid_roles:
            await message.answer(
                f"❌ Неверная роль '{role}'!\n"
                f"Доступные роли: {', '.join(valid_roles)}"
            )
            return
        
        # Получаем информацию о пользователе
        user_info = user_service.get_user(user_id)
        if not user_info:
            await message.answer(f"❌ Пользователь с ID {user_id} не найден!")
            return
        
        # Устанавливаем роль
        if user_service.set_user_role(user_id, role):
            old_role = user_info.get('role', 'user')
            await message.answer(
                f"✅ Роль пользователя {user_id} изменена:\n"
                f"📝 Имя: {user_info.get('name', 'Неизвестно')}\n"
                f"🔄 {old_role} → {role}"
            )
            bot_logger.log_admin_action(message.from_user.id, f"изменение роли пользователя {user_id} с {old_role} на {role}")
        else:
            await message.answer(f"❌ Ошибка при изменении роли пользователя {user_id}")
            
    except Exception as e:
        await message.answer("❌ Произошла ошибка при выполнении команды")
        bot_logger.log_error(e, f"setrole command error, user: {message.from_user.id}")


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


@router.message(Command("users"))
@admin_required
async def cmd_users(message: Message, **kwargs) -> None:
    """
    Показать список пользователей с фильтрацией (только для администраторов)
    
    Отображает список пользователей с возможностью фильтрации по:
    - Статусу (все, активные, неактивные, заблокированные)
    - Тегам
    - Дате регистрации
    - Поиску по имени/username
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    bot_logger.log_admin_action(message.from_user.id, "просмотр списка пользователей")
    
    # Получаем всех пользователей
    users = user_service.get_all_users()
    
    if not users:
        await message.answer("📝 Пользователи не найдены")
        return
    
    # Создаем интерактивную клавиатуру с фильтрами
    keyboard = create_users_filter_keyboard()
    
    # Формируем краткую статистику
    total = len(users)
    active = len([u for u in users.values() if u.get('status') == 'active'])
    inactive = len([u for u in users.values() if u.get('status') == 'inactive'])
    banned = len([u for u in users.values() if u.get('status') == 'banned'])
    
    stats_text = f"""
👥 <b>Список пользователей</b>

📊 <b>Статистика:</b>
• Всего: {total}
• Активных: {active}
• Неактивных: {inactive}
• Заблокированных: {banned}

🔍 <b>Выберите фильтр:</b>
    """
    
    await message.answer(stats_text, reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("spamstats"))
@admin_required
async def cmd_spamstats(message: Message) -> None:
    """
    Показать статистику защиты от спама
    
    Отображает информацию о заблокированных пользователях и их активности.
    
    Args:
        message (Message): Сообщение с командой
        
    Returns:
        None
    """
    bot_logger.log_user_action(message.from_user.id, "просмотр статистики спам-защиты")
    
    # Получаем всех заблокированных пользователей
    users = user_service.get_all_users()
    banned_users = {user_id: user_data for user_id, user_data in users.items() 
                   if user_data.get('status') == 'banned'}
    
    if not banned_users:
        await message.answer("📊 Нет заблокированных пользователей для отслеживания.")
        return
    
    text = "📊 <b>Статистика защиты от спама:</b>\n\n"
    
    total_messages = 0
    blocked_users = 0
    
    for user_id, user_data in banned_users.items():
        spam_stats = security_manager.get_spam_protection_stats(int(user_id))
        
        text += f"👤 <b>Пользователь {user_id}</b>\n"
        text += f"📝 Имя: {user_data.get('name', 'Не указано')}\n"
        text += f"📊 Сообщений: {spam_stats['message_count']}\n"
        
        if spam_stats['is_blocked']:
            blocked_users += 1
            remaining_minutes = spam_stats['remaining_time'] // 60
            remaining_seconds = spam_stats['remaining_time'] % 60
            text += f"🚫 Заблокирован еще на {remaining_minutes}м {remaining_seconds}с\n"
        else:
            text += "✅ Активен\n"
        
        text += "\n"
        total_messages += spam_stats['message_count']
    
    text += f"📈 <b>Общая статистика:</b>\n"
    text += f"• Заблокированных пользователей: {len(banned_users)}\n"
    text += f"• Сейчас заблокировано за спам: {blocked_users}\n"
    text += f"• Всего сообщений от заблокированных: {total_messages}\n"
    
    await message.answer(text, parse_mode="HTML")


def create_users_filter_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с фильтрами для списка пользователей
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с фильтрами
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Все", callback_data="users_filter_all"),
            InlineKeyboardButton(text="✅ Активные", callback_data="users_filter_active")
        ],
        [
            InlineKeyboardButton(text="⏸️ Неактивные", callback_data="users_filter_inactive"),
            InlineKeyboardButton(text="🚫 Заблокированные", callback_data="users_filter_banned")
        ],
        [
            InlineKeyboardButton(text="🆕 Новые (неделя)", callback_data="users_filter_new"),
            InlineKeyboardButton(text="🏷️ С тегами", callback_data="users_filter_tagged")
        ],
        [
            InlineKeyboardButton(text="🔍 Поиск", callback_data="users_search"),
            InlineKeyboardButton(text="📊 Экспорт", callback_data="users_export")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
        ]
    ])
    return keyboard


@router.callback_query(lambda c: c.data.startswith("users_filter_"))
async def users_filter_handler(callback: CallbackQuery) -> None:
    """
    Обработчик фильтров списка пользователей
    
    Args:
        callback (CallbackQuery): Callback с выбранным фильтром
        
    Returns:
        None
    """
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    filter_type = callback.data.split("_")[-1]
    users = user_service.get_all_users()
    
    # Применяем фильтр
    if filter_type == "all":
        filtered_users = users
        filter_name = "Все пользователи"
    elif filter_type == "active":
        filtered_users = {k: v for k, v in users.items() if v.get('status') == 'active'}
        filter_name = "Активные пользователи"
    elif filter_type == "inactive":
        filtered_users = {k: v for k, v in users.items() if v.get('status') == 'inactive'}
        filter_name = "Неактивные пользователи"
    elif filter_type == "banned":
        filtered_users = {k: v for k, v in users.items() if v.get('status') == 'banned'}
        filter_name = "Заблокированные пользователи"
    elif filter_type == "new":
        week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
        filtered_users = {
            k: v for k, v in users.items() 
            if v.get('first_interaction', '').startswith(week_ago)
        }
        filter_name = "Новые пользователи (неделя)"
    elif filter_type == "tagged":
        filtered_users = {
            k: v for k, v in users.items() 
            if v.get('tags') and len(v.get('tags', [])) > 0
        }
        filter_name = "Пользователи с тегами"
    else:
        await callback.answer("❌ Неизвестный фильтр")
        return
    
    if not filtered_users:
        await callback.answer(f"📝 {filter_name} не найдены")
        return
    
    # Создаем клавиатуру с пользователями (первая страница)
    keyboard = create_users_list_keyboard(filtered_users, 0, filter_type)
    
    # Формируем текст с результатами
    result_text = f"""
👥 <b>{filter_name}</b>

📊 <b>Найдено:</b> {len(filtered_users)} пользователей

📋 <b>Список:</b>
    """
    
    await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")
    bot_logger.log_admin_action(callback.from_user.id, f"фильтр пользователей: {filter_type}")


def create_users_list_keyboard(users: dict, page: int = 0, filter_type: str = "all") -> InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком пользователей с пагинацией
    
    Args:
        users (dict): Отфильтрованные пользователи
        page (int): Номер страницы
        filter_type (str): Тип фильтра
        
    Returns:
        InlineKeyboardMarkup: Клавиатура со списком пользователей
    """
    users_list = list(users.items())
    users_per_page = 5
    total_pages = (len(users_list) + users_per_page - 1) // users_per_page
    
    start_idx = page * users_per_page
    end_idx = start_idx + users_per_page
    page_users = users_list[start_idx:end_idx]
    
    keyboard = []
    
    # Добавляем пользователей на страницу
    for user_id, user_data in page_users:
        name = user_data.get('name', 'Не указано')
        username = user_data.get('username', '')
        status = user_data.get('status', 'unknown')
        
        # Формируем текст кнопки
        status_emoji = {
            'active': '✅',
            'inactive': '⏸️',
            'banned': '🚫'
        }.get(status, '❓')
        
        display_name = name[:20] + "..." if len(name) > 20 else name
        button_text = f"{status_emoji} {display_name}"
        
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"user_detail_{user_id}"
            )
        ])
    
    # Добавляем навигацию
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"users_page_{filter_type}_{page-1}")
        )
    
    nav_buttons.append(
        InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="users_page_info")
    )
    
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"users_page_{filter_type}_{page+1}")
        )
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Кнопки управления
    keyboard.append([
        InlineKeyboardButton(text="🔍 Фильтры", callback_data="users_filters"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(lambda c: c.data.startswith("users_page_"))
async def users_page_handler(callback: CallbackQuery) -> None:
    """
    Обработчик пагинации списка пользователей
    
    Args:
        callback (CallbackQuery): Callback с номером страницы
        
    Returns:
        None
    """
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    if callback.data == "users_page_info":
        await callback.answer("📄 Информация о страницах")
        return
    
    parts = callback.data.split("_")
    filter_type = parts[2]
    page = int(parts[3])
    
    users = user_service.get_all_users()
    
    # Применяем тот же фильтр
    if filter_type == "all":
        filtered_users = users
        filter_name = "Все пользователи"
    elif filter_type == "active":
        filtered_users = {k: v for k, v in users.items() if v.get('status') == 'active'}
        filter_name = "Активные пользователи"
    elif filter_type == "inactive":
        filtered_users = {k: v for k, v in users.items() if v.get('status') == 'inactive'}
        filter_name = "Неактивные пользователи"
    elif filter_type == "banned":
        filtered_users = {k: v for k, v in users.items() if v.get('status') == 'banned'}
        filter_name = "Заблокированные пользователи"
    elif filter_type == "new":
        week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
        filtered_users = {
            k: v for k, v in users.items() 
            if v.get('first_interaction', '').startswith(week_ago)
        }
        filter_name = "Новые пользователи (неделя)"
    elif filter_type == "tagged":
        filtered_users = {
            k: v for k, v in users.items() 
            if v.get('tags') and len(v.get('tags', [])) > 0
        }
        filter_name = "Пользователи с тегами"
    else:
        await callback.answer("❌ Неизвестный фильтр")
        return
    
    keyboard = create_users_list_keyboard(filtered_users, page, filter_type)
    
    result_text = f"""
👥 <b>{filter_name}</b>

📊 <b>Найдено:</b> {len(filtered_users)} пользователей

📋 <b>Список:</b>
    """
    
    await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(lambda c: c.data.startswith("user_detail_"))
async def user_detail_handler(callback: CallbackQuery) -> None:
    """
    Показать детальную информацию о пользователе
    
    Args:
        callback (CallbackQuery): Callback с ID пользователя
        
    Returns:
        None
    """
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    user_id = callback.data.split("_")[-1]
    user_info = user_service.get_user(user_id)
    
    if not user_info:
        await callback.answer("❌ Пользователь не найден")
        return
    
    # Формируем детальную информацию
    username = user_info.get('username', '')
    if username and not username.startswith('@'):
        username = f"@{username}"
    
    tags = user_info.get('tags', [])
    if isinstance(tags, str):
        tags = [tags]
    elif not isinstance(tags, list):
        tags = []
    
    tags_display = ", ".join(tags) if tags else "Не указаны"
    
    status_emoji = {
        'active': '✅',
        'inactive': '⏸️',
        'banned': '🚫'
    }.get(user_info.get('status', 'unknown'), '❓')
    
    # Получаем роль пользователя
    role = user_info.get('role', 'user')
    role_display = {
        'user': '👤 Пользователь',
        'moderator': '🛡️ Модератор',
        'admin': '👑 Администратор'
    }.get(role, '👤 Пользователь')
    
    detail_text = f"""
👤 <b>Детальная информация о пользователе:</b>

🆔 ID: <code>{user_id}</code>
🔹 Имя: {user_info.get('name', 'Не указано')}
📌 Username: {username if username else 'Не указан'}
📅 Дата регистрации: {user_info.get('registered_at', 'Не указана')}
📍 Статус: {status_emoji} {user_info.get('status', 'Не указан')}
🎭 Роль: {role_display}
🏷️ Теги: {tags_display}
    """
    
    if user_info.get('activated_at'):
        detail_text += f"\n✅ Активирован: {user_info.get('activated_at')}"
    
    # Кнопки управления пользователем
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"user_ban_{user_id}"),
            InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"user_unban_{user_id}")
        ],
        [
            InlineKeyboardButton(text="🎭 Роли", callback_data=f"user_roles_{user_id}"),
            InlineKeyboardButton(text="🏷️ Добавить тег", callback_data=f"user_addtag_{user_id}")
        ],
        [
            InlineKeyboardButton(text="📊 Активность", callback_data=f"user_activity_{user_id}"),
            InlineKeyboardButton(text="🔙 Назад к списку", callback_data="users_filters")
        ]
    ])
    
    await callback.message.edit_text(detail_text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    bot_logger.log_admin_action(callback.from_user.id, f"просмотр деталей пользователя {user_id}")


@router.callback_query(lambda c: c.data.startswith("users_filters"))
async def users_filters_handler(callback: CallbackQuery) -> None:
    """
    Вернуться к фильтрам списка пользователей
    
    Args:
        callback (CallbackQuery): Callback для возврата к фильтрам
        
    Returns:
        None
    """
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    keyboard = create_users_filter_keyboard()
    
    users = user_service.get_all_users()
    total = len(users)
    active = len([u for u in users.values() if u.get('status') == 'active'])
    inactive = len([u for u in users.values() if u.get('status') == 'inactive'])
    banned = len([u for u in users.values() if u.get('status') == 'banned'])
    
    stats_text = f"""
👥 <b>Список пользователей</b>

📊 <b>Статистика:</b>
• Всего: {total}
• Активных: {active}
• Неактивных: {inactive}
• Заблокированных: {banned}

🔍 <b>Выберите фильтр:</b>
    """
    
    await callback.message.edit_text(stats_text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(lambda c: c.data.startswith("users_search"))
async def users_search_handler(callback: CallbackQuery) -> None:
    """
    Обработчик поиска пользователей
    
    Args:
        callback (CallbackQuery): Callback для поиска
        
    Returns:
        None
    """
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    await callback.message.edit_text(
        "🔍 <b>Поиск пользователей</b>\n\n"
        "Отправьте имя пользователя или username для поиска.\n"
        "Примеры:\n"
        "• Андрей\n"
        "• @username\n"
        "• ncux11\n\n"
        "Для отмены отправьте /cancel",
        parse_mode="HTML"
    )
    
    # TODO: Добавить FSM для поиска пользователей
    await callback.answer("🔍 Функция поиска в разработке")


@router.callback_query(lambda c: c.data.startswith("users_export"))
async def users_export_handler(callback: CallbackQuery) -> None:
    """
    Экспорт списка пользователей
    
    Args:
        callback (CallbackQuery): Callback для экспорта
        
    Returns:
        None
    """
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    users = user_service.get_all_users()
    
    if not users:
        await callback.answer("📝 Нет пользователей для экспорта")
        return
    
    # Формируем CSV-подобный текст
    export_text = "ID,Имя,Username,Статус,Дата регистрации,Теги\n"
    
    for user_id, user_data in users.items():
        name = user_data.get('name', '')
        if name:
            name = name.replace(',', ';')
        
        username = user_data.get('username', '')
        if username:
            username = username.replace(',', ';')
        
        status = user_data.get('status', '')
        registered = user_data.get('registered_at', '')
        tags = ','.join(user_data.get('tags', [])).replace(',', ';')
        
        export_text += f"{user_id},{name},{username},{status},{registered},{tags}\n"
    
    # Отправляем как файл с правильной кодировкой для Excel
    # Добавляем BOM для корректного отображения русских символов
    bom = '\ufeff'.encode('utf-8')
    csv_content = bom + export_text.encode('utf-8-sig')
    
    await callback.message.answer_document(
        types.BufferedInputFile(
            csv_content,
            filename=f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        ),
        caption="📊 Экспорт пользователей"
    )
    
    bot_logger.log_admin_action(callback.from_user.id, "экспорт списка пользователей")
    await callback.answer("✅ Экспорт завершен") 


@router.callback_query(lambda c: c.data.startswith("user_ban_"))
async def user_ban_handler(callback: CallbackQuery) -> None:
    """
    Заблокировать пользователя через интерфейс
    
    Args:
        callback (CallbackQuery): Callback с ID пользователя
        
    Returns:
        None
    """
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    user_id = callback.data.split("_")[-1]
    
    if user_service.ban_user(user_id):
        bot_logger.log_admin_action(callback.from_user.id, f"блокировка пользователя {user_id}")
        await callback.answer("✅ Пользователь заблокирован")
        
        # Обновляем сообщение с деталями пользователя
        user_info = user_service.get_user(user_id)
        if user_info:
            username = user_info.get('username', '')
            if username and not username.startswith('@'):
                username = f"@{username}"
            
            tags = user_info.get('tags', [])
            if isinstance(tags, str):
                tags = [tags]
            elif not isinstance(tags, list):
                tags = []
            
            tags_display = ", ".join(tags) if tags else "Не указаны"
            
            detail_text = f"""
👤 <b>Детальная информация о пользователе:</b>

🆔 ID: <code>{user_id}</code>
🔹 Имя: {user_info.get('name', 'Не указано')}
📌 Username: {username if username else 'Не указан'}
📅 Дата регистрации: {user_info.get('registered_at', 'Не указана')}
📍 Статус: 🚫 {user_info.get('status', 'Не указан')}
🏷️ Теги: {tags_display}
            """
            
            if user_info.get('activated_at'):
                detail_text += f"\n✅ Активирован: {user_info.get('activated_at')}"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"user_ban_{user_id}"),
                    InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"user_unban_{user_id}")
                ],
                [
                    InlineKeyboardButton(text="🏷️ Добавить тег", callback_data=f"user_addtag_{user_id}"),
                    InlineKeyboardButton(text="📊 Активность", callback_data=f"user_activity_{user_id}")
                ],
                [
                    InlineKeyboardButton(text="🔙 Назад к списку", callback_data="users_filters")
                ]
            ])
            
            await callback.message.edit_text(detail_text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    else:
        await callback.answer("❌ Ошибка блокировки пользователя")


@router.callback_query(lambda c: c.data.startswith("user_unban_"))
async def user_unban_handler(callback: CallbackQuery) -> None:
    """
    Разблокировать пользователя через интерфейс
    
    Args:
        callback (CallbackQuery): Callback с ID пользователя
        
    Returns:
        None
    """
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    user_id = callback.data.split("_")[-1]
    
    if user_service.unban_user(user_id):
        bot_logger.log_admin_action(callback.from_user.id, f"разблокировка пользователя {user_id}")
        await callback.answer("✅ Пользователь разблокирован")
        
        # Обновляем сообщение с деталями пользователя
        user_info = user_service.get_user(user_id)
        if user_info:
            username = user_info.get('username', '')
            if username and not username.startswith('@'):
                username = f"@{username}"
            
            tags = user_info.get('tags', [])
            if isinstance(tags, str):
                tags = [tags]
            elif not isinstance(tags, list):
                tags = []
            
            tags_display = ", ".join(tags) if tags else "Не указаны"
            
            status_emoji = {
                'active': '✅',
                'inactive': '⏸️',
                'banned': '🚫'
            }.get(user_info.get('status', 'unknown'), '❓')
            
            detail_text = f"""
👤 <b>Детальная информация о пользователе:</b>

🆔 ID: <code>{user_id}</code>
🔹 Имя: {user_info.get('name', 'Не указано')}
📌 Username: {username if username else 'Не указан'}
📅 Дата регистрации: {user_info.get('registered_at', 'Не указана')}
📍 Статус: {status_emoji} {user_info.get('status', 'Не указан')}
🏷️ Теги: {tags_display}
            """
            
            if user_info.get('activated_at'):
                detail_text += f"\n✅ Активирован: {user_info.get('activated_at')}"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"user_ban_{user_id}"),
                    InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"user_unban_{user_id}")
                ],
                [
                    InlineKeyboardButton(text="🏷️ Добавить тег", callback_data=f"user_addtag_{user_id}"),
                    InlineKeyboardButton(text="📊 Активность", callback_data=f"user_activity_{user_id}")
                ],
                [
                    InlineKeyboardButton(text="🔙 Назад к списку", callback_data="users_filters")
                ]
            ])
            
            await callback.message.edit_text(detail_text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    else:
        await callback.answer("❌ Ошибка разблокировки пользователя")


@router.callback_query(lambda c: c.data.startswith("user_addtag_"))
async def user_addtag_handler(callback: CallbackQuery) -> None:
    """
    Добавить тег пользователю через интерфейс
    
    Args:
        callback (CallbackQuery): Callback с ID пользователя
        
    Returns:
        None
    """
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    user_id = callback.data.split("_")[-1]
    user_info = user_service.get_user(user_id)
    
    if not user_info:
        await callback.answer("❌ Пользователь не найден")
        return
    
    # Показываем текущие теги и предлагаем добавить новый
    current_tags = user_info.get('tags', [])
    if isinstance(current_tags, str):
        current_tags = [current_tags]
    elif not isinstance(current_tags, list):
        current_tags = []
    
    tags_display = ", ".join(current_tags) if current_tags else "Не указаны"
    
    await callback.message.edit_text(
        f"🏷️ <b>Добавление тега пользователю</b>\n\n"
        f"👤 Пользователь: {user_info.get('name', 'Не указано')}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"🏷️ Текущие теги: {tags_display}\n\n"
        f"Отправьте новый тег для добавления.\n"
        f"Примеры:\n"
        f"• Модератор\n"
        f"• VIP\n"
        f"• Новый участник\n\n"
        f"Для отмены отправьте /cancel",
        parse_mode="HTML"
    )
    
    # TODO: Добавить FSM для добавления тегов
    await callback.answer("🏷️ Функция добавления тегов в разработке")


@router.callback_query(lambda c: c.data.startswith("user_activity_"))
async def user_activity_handler(callback: CallbackQuery) -> None:
    """
    Показать активность пользователя
    
    Args:
        callback (CallbackQuery): Callback с ID пользователя
        
    Returns:
        None
    """
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    user_id = callback.data.split("_")[-1]
    user_info = user_service.get_user(user_id)
    
    if not user_info:
        await callback.answer("❌ Пользователь не найден")
        return
    
    # Здесь можно добавить логику анализа активности
    # Пока просто показываем базовую информацию
    activity_text = f"""
📊 <b>Активность пользователя:</b>

👤 Пользователь: {user_info.get('name', 'Неизвестно')}
🆔 ID: <code>{user_id}</code>
📅 Дата регистрации: {user_info.get('registered_at', 'Не указана')}
📍 Статус: {user_info.get('status', 'Не указан')}

📈 <b>Статистика:</b>
• Первое взаимодействие: {user_info.get('first_interaction', 'Не указано')}
• Активирован: {user_info.get('activated_at', 'Не активирован')}

💡 <b>Примечание:</b>
Детальная аналитика активности будет добавлена в будущих версиях.
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Назад к пользователю", callback_data=f"user_detail_{user_id}")
        ]
    ])
    
    await callback.message.edit_text(activity_text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    bot_logger.log_admin_action(callback.from_user.id, f"просмотр активности пользователя {user_id}")


@router.callback_query(lambda c: c.data.startswith("user_roles_"))
async def user_roles_handler(callback: CallbackQuery) -> None:
    """
    Показать меню управления ролями пользователя
    
    Args:
        callback (CallbackQuery): Callback с ID пользователя
        
    Returns:
        None
    """
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    user_id = callback.data.split("_")[-1]
    user_info = user_service.get_user(user_id)
    
    if not user_info:
        await callback.answer("❌ Пользователь не найден")
        return
    
    current_role = user_info.get('role', 'user')
    role_display = {
        'user': '👤 Пользователь',
        'moderator': '🛡️ Модератор',
        'admin': '👑 Администратор'
    }.get(current_role, '👤 Пользователь')
    
    roles_text = f"""
🎭 <b>Управление ролями</b>

👤 Пользователь: {user_info.get('name', 'Неизвестно')}
🆔 ID: <code>{user_id}</code>
🎭 Текущая роль: {role_display}

📋 <b>Доступные роли:</b>
• 👤 Пользователь - базовые права
• 🛡️ Модератор - управление пользователями
• 👑 Администратор - полные права

💡 <b>Выберите новую роль:</b>
    """
    
    # Создаем кнопки для каждой роли
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"👤 Пользователь {'✅' if current_role == 'user' else ''}", 
                callback_data=f"user_setrole_{user_id}_user"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🛡️ Модератор {'✅' if current_role == 'moderator' else ''}", 
                callback_data=f"user_setrole_{user_id}_moderator"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"👑 Администратор {'✅' if current_role == 'admin' else ''}", 
                callback_data=f"user_setrole_{user_id}_admin"
            )
        ],
        [
            InlineKeyboardButton(text="🔙 Назад к пользователю", callback_data=f"user_detail_{user_id}")
        ]
    ])
    
    await callback.message.edit_text(roles_text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    bot_logger.log_admin_action(callback.from_user.id, f"открытие меню ролей для пользователя {user_id}")


@router.callback_query(lambda c: c.data.startswith("user_setrole_"))
async def user_setrole_handler(callback: CallbackQuery) -> None:
    """
    Установить роль пользователю
    
    Args:
        callback (CallbackQuery): Callback с ID пользователя и новой ролью
        
    Returns:
        None
    """
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!")
        return
    
    parts = callback.data.split("_")
    user_id = parts[2]
    new_role = parts[3]
    
    user_info = user_service.get_user(user_id)
    if not user_info:
        await callback.answer("❌ Пользователь не найден")
        return
    
    old_role = user_info.get('role', 'user')
    
    # Проверяем, не пытается ли админ понизить другого админа
    if old_role == 'admin' and new_role != 'admin' and int(user_id) in config.security.admin_ids:
        await callback.answer("❌ Нельзя изменить роль главного администратора!")
        return
    
    # Устанавливаем новую роль
    if user_service.set_user_role(user_id, new_role):
        role_display = {
            'user': '👤 Пользователь',
            'moderator': '🛡️ Модератор',
            'admin': '👑 Администратор'
        }.get(new_role, '👤 Пользователь')
        
        success_text = f"""
✅ <b>Роль успешно изменена!</b>

👤 Пользователь: {user_info.get('name', 'Неизвестно')}
🆔 ID: <code>{user_id}</code>
🔄 {old_role} → {new_role}
🎭 Новая роль: {role_display}

💡 <b>Изменения применены немедленно.</b>
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад к ролям", callback_data=f"user_roles_{user_id}"),
                InlineKeyboardButton(text="👤 К пользователю", callback_data=f"user_detail_{user_id}")
            ]
        ])
        
        await callback.message.edit_text(success_text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
        bot_logger.log_admin_action(callback.from_user.id, f"изменение роли пользователя {user_id} с {old_role} на {new_role}")
    else:
        await callback.answer("❌ Ошибка при изменении роли!")
        bot_logger.log_error(Exception("Ошибка изменения роли"), f"user_id: {user_id}, role: {new_role}") 
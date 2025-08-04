"""
@file: handlers/mailing_handlers.py
@description: Обработчики для рассылки сообщений (исправленная версия)
@dependencies: aiogram, asyncio, config, utils, services
@created: 2025-01-06
"""

import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from datetime import datetime

from config import config
from utils.logger import bot_logger
from utils.access_control import admin_required
from utils.states import MailingStates
from services.users import user_service

router = Router()


@router.message(Command("send"))
@admin_required
async def cmd_send_broadcast(message: Message, state: FSMContext, **kwargs) -> None:
    """
    Команда для массовой рассылки сообщений
    
    ИСПРАВЛЕНА: Теперь использует фоновые задачи вместо блокирующего цикла
    
    Args:
        message (Message): Сообщение с командой
        state (FSMContext): Состояние FSM
        
    Returns:
        None
    """
    bot_logger.log_admin_action(message.from_user.id, "запуск команды рассылки")
    
    await message.answer(
        "📢 <b>Создание рассылки</b>\n\n"
        "Отправьте текст сообщения для рассылки всем пользователям.\n"
        "Для отмены используйте /cancel",
        parse_mode="HTML"
    )
    
    await state.set_state(MailingStates.waiting_for_text)


@router.message(MailingStates.waiting_for_text)
async def process_broadcast_text(message: Message, state: FSMContext, bot) -> None:
    """
    Обработка текста для рассылки
    
    ИСПРАВЛЕНО: Рассылка выполняется в фоновой задаче
    
    Args:
        message (Message): Сообщение с текстом рассылки
        state (FSMContext): Состояние FSM
        bot: Экземпляр бота для отправки сообщений
        
    Returns:
        None
    """
    broadcast_text = message.text
    admin_id = message.from_user.id
    
    # Получаем всех пользователей
    users = user_service.get_all_users()
    
    if not users:
        await message.answer("❌ Нет пользователей для рассылки")
        await state.clear()
        return
    
    total_users = len(users)
    
    await message.answer(
        f"📢 <b>Запуск рассылки</b>\n\n"
        f"📊 Пользователей: {total_users}\n"
        f"📝 Текст: {broadcast_text[:100]}{'...' if len(broadcast_text) > 100 else ''}\n\n"
        f"⏳ Рассылка запущена в фоновом режиме...",
        parse_mode="HTML"
    )
    
    # ИСПРАВЛЕНИЕ: Запускаем рассылку в фоновой задаче
    asyncio.create_task(
        send_broadcast_async(bot, users, broadcast_text, admin_id, message.chat.id)
    )
    
    await state.clear()
    bot_logger.log_admin_action(admin_id, f"запуск рассылки для {total_users} пользователей")


async def send_broadcast_async(bot, users: dict, text: str, admin_id: int, admin_chat_id: int) -> None:
    """
    Асинхронная рассылка сообщений с отчетом
    
    НОВОЕ: Функция для неблокирующей рассылки с задержками и статистикой
    
    Args:
        bot: Экземпляр бота
        users (dict): Словарь пользователей
        text (str): Текст для рассылки
        admin_id (int): ID администратора
        admin_chat_id (int): Chat ID администратора для отчета
        
    Returns:
        None
    """
    total_users = len(users)
    successful = 0
    failed = 0
    blocked_by_user = 0
    
    start_time = datetime.now()
    
    bot_logger.log_admin_action(admin_id, f"начало рассылки для {total_users} пользователей")
    
    # Отправляем сообщения с задержками
    for i, (user_id, user_data) in enumerate(users.items(), 1):
        try:
            # ИСПРАВЛЕНИЕ: Добавляем задержку для соблюдения лимитов API
            if i > 1:  # Не ждем перед первым сообщением
                await asyncio.sleep(0.1)  # 100ms между сообщениями
            
            await bot.send_message(
                chat_id=int(user_id),
                text=text,
                parse_mode="HTML"
            )
            
            successful += 1
            
            # Промежуточный отчет каждые 50 пользователей
            if i % 50 == 0:
                await bot.send_message(
                    chat_id=admin_chat_id,
                    text=f"📊 Прогресс рассылки: {i}/{total_users} ({(i/total_users*100):.1f}%)",
                    parse_mode="HTML"
                )
        
        except Exception as e:
            failed += 1
            error_str = str(e).lower()
            
            # Определяем тип ошибки
            if "blocked" in error_str or "bot was blocked" in error_str:
                blocked_by_user += 1
            
            # Логируем ошибку, но не прерываем рассылку
            bot_logger.log_error(
                e, 
                f"Ошибка отправки рассылки пользователю {user_id}"
            )
    
    # Финальный отчет
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    report_text = f"""
📢 <b>Рассылка завершена</b>

📊 <b>Статистика:</b>
• Всего пользователей: {total_users}
• Успешно доставлено: {successful}
• Ошибки доставки: {failed}
• Заблокировали бота: {blocked_by_user}
• Процент успеха: {(successful/total_users*100):.1f}%

⏱️ <b>Время выполнения:</b> {duration:.1f} сек
⚡ <b>Скорость:</b> {total_users/duration:.1f} сообщений/сек

✅ Рассылка выполнена без блокировки бота!
    """
    
    try:
        await bot.send_message(
            chat_id=admin_chat_id,
            text=report_text,
            parse_mode="HTML"
        )
    except Exception as e:
        bot_logger.log_error(e, "Ошибка отправки финального отчета о рассылке")
    
    bot_logger.log_admin_action(
        admin_id, 
        f"завершение рассылки: {successful}/{total_users} успешно, {failed} ошибок"
    )


# === ПРИМЕРЫ СТАРОГО (БЛОКИРУЮЩЕГО) КОДА ===
# Оставлено для демонстрации проблемы

async def send_broadcast_blocking_example(bot, users: dict, text: str) -> None:
    """
    ПЛОХОЙ ПРИМЕР: Блокирующая рассылка
    
    ⚠️ НЕ ИСПОЛЬЗУЙТЕ ЭТОТ КОД! ⚠️
    
    Проблемы:
    1. Блокирует весь бот на время рассылки
    2. Нет задержек - может нарушить лимиты API
    3. Нет отчета об ошибках
    4. Нет промежуточного прогресса
    
    Args:
        bot: Экземпляр бота
        users (dict): Словарь пользователей
        text (str): Текст для рассылки
    """
    # ❌ ПРОБЛЕМА: Синхронный цикл блокирует бота
    for user_id in users.keys():
        try:
            # ❌ ПРОБЛЕМА: Нет задержек между запросами
            await bot.send_message(chat_id=int(user_id), text=text)
        except Exception:
            # ❌ ПРОБЛЕМА: Игнорируем ошибки без логирования
            pass  # Просто пропускаем ошибки
    
    # ❌ ПРОБЛЕМА: Нет отчета о результатах
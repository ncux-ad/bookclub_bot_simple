"""
@file: handlers/cancel_handlers.py
@description: Универсальные обработчики отмены операций
@dependencies: aiogram, utils
@created: 2025-01-06
"""

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ContentType
from aiogram.fsm.context import FSMContext

from utils.logger import bot_logger
from utils.states import (
    RegistrationStates, 
    BookSearchStates, 
    BookManagementStates, 
    BookLinkStates, 
    MailingStates,
    EventCreationStates,
    UserManagementStates
)

router = Router()


@router.message(Command("cancel"))
async def cmd_cancel_universal(message: Message, state: FSMContext) -> None:
    """
    Универсальная команда отмены для всех состояний FSM
    
    ИСПРАВЛЕНО: Работает во всех состояниях с информативными сообщениями
    
    Args:
        message (Message): Сообщение с командой отмены
        state (FSMContext): Контекст FSM
        
    Returns:
        None
    """
    current_state = await state.get_state()
    
    if not current_state:
        await message.answer(
            "ℹ️ Нет активных операций для отмены.\n"
            "Используйте /help для списка команд."
        )
        return
    
    # Получаем данные состояния для информативного сообщения
    state_data = await state.get_data()
    
    # Определяем тип операции и формируем сообщение
    cancel_message = get_cancel_message(current_state, state_data)
    
    # Очищаем состояние
    await state.clear()
    
    # Логируем отмену
    bot_logger.log_user_action(
        message.from_user.id, 
        f"отмена операции: {current_state}"
    )
    
    await message.answer(cancel_message)


def get_cancel_message(state_name: str, state_data: dict) -> str:
    """
    Получить информативное сообщение об отмене в зависимости от состояния
    
    Args:
        state_name (str): Название текущего состояния
        state_data (dict): Данные состояния
        
    Returns:
        str: Сообщение об отмене
    """
    # Регистрация
    if state_name == RegistrationStates.waiting_for_phrase.state:
        return (
            "❌ <b>Регистрация отменена</b>\n\n"
            "Вы можете попробовать снова командой /register\n"
            "Или используйте /help для других команд."
        )
    
    # Поиск книг
    elif state_name == BookSearchStates.waiting_for_query.state:
        return (
            "❌ <b>Поиск книг отменен</b>\n\n"
            "Вы можете:\n"
            "• /search - начать новый поиск\n"
            "• /library - просмотреть всю библиотеку\n"
            "• /help - список команд"
        )
    
    # Добавление книги
    elif state_name in [
        BookManagementStates.waiting_for_book_title.state,
        BookManagementStates.waiting_for_author.state,
        BookManagementStates.waiting_for_description.state,
        BookManagementStates.waiting_for_file_path.state,
        BookManagementStates.waiting_for_zip_file.state
    ]:
        book_title = state_data.get('book_title', 'новая книга')
        return (
            f"❌ <b>Добавление книги отменено</b>\n\n"
            f"📖 Книга: {book_title}\n\n"
            "Несохраненные данные удалены.\n"
            "Используйте /addbook для повторной попытки."
        )
    
    # Редактирование ссылок
    elif state_name in [
        BookLinkStates.waiting_for_yandex_url.state,
        BookLinkStates.waiting_for_litres_url.state,
        BookLinkStates.waiting_for_audio_format.state
    ]:
        book_title = state_data.get('book_title', 'книга')
        return (
            f"❌ <b>Редактирование ссылок отменено</b>\n\n"
            f"📖 Книга: {book_title}\n\n"
            "Изменения не сохранены.\n"
            "Используйте /editlinks для повторной попытки."
        )
    
    # Рассылка
    elif state_name == MailingStates.waiting_for_text.state:
        return (
            "❌ <b>Рассылка отменена</b>\n\n"
            "Текст рассылки не был сохранен.\n"
            "Используйте /send для создания новой рассылки."
        )
    
    # Создание события  
    elif state_name in [
        EventCreationStates.waiting_for_title.state,
        EventCreationStates.waiting_for_date.state,
        EventCreationStates.waiting_for_time.state,
        EventCreationStates.waiting_for_description.state
    ]:
        return (
            "❌ <b>Создание события отменено</b>\n\n"
            "Несохраненные данные удалены.\n"
            "Используйте админ-панель для создания нового события."
        )
    
    # Управление пользователями
    elif state_name in [
        UserManagementStates.waiting_for_user_id.state,
        UserManagementStates.waiting_for_action.state
    ]:
        return (
            "❌ <b>Управление пользователями отменено</b>\n\n"
            "Используйте админ-панель для управления пользователями."
        )
    
    # Общее сообщение для неизвестных состояний
    else:
        return (
            "❌ <b>Операция отменена</b>\n\n"
            "Используйте /help для списка доступных команд."
        )


# Обработчик неверного типа контента в FSM
@router.message(StateFilter("*"), ~F.text)
async def handle_wrong_content_type_in_fsm(message: Message, state: FSMContext) -> None:
    """
    Обработчик неверного типа контента во время FSM
    
    НОВОЕ: Обрабатывает случаи, когда пользователь отправляет не текст
    
    Args:
        message (Message): Сообщение с неверным типом контента
        state (FSMContext): Контекст FSM
        
    Returns:
        None
    """
    current_state = await state.get_state()
    
    if not current_state:
        return  # Нет активного состояния, пропускаем
    
    # Определяем, что ожидается в текущем состоянии
    expected_content = get_expected_content_message(current_state)
    
    await message.answer(
        f"❌ <b>Неверный тип сообщения!</b>\n\n"
        f"{expected_content}\n\n"
        "💡 Для отмены используйте /cancel",
        parse_mode="HTML"
    )
    
    bot_logger.log_user_action(
        message.from_user.id,
        f"неверный тип контента в состоянии {current_state}"
    )


def get_expected_content_message(state_name: str) -> str:
    """
    Получить сообщение о том, что ожидается в данном состоянии
    
    Args:
        state_name (str): Название состояния
        
    Returns:
        str: Сообщение о том, что ожидается
    """
    text_states = [
        RegistrationStates.waiting_for_phrase.state,
        BookSearchStates.waiting_for_query.state,
        BookManagementStates.waiting_for_book_title.state,
        BookManagementStates.waiting_for_author.state,
        BookManagementStates.waiting_for_description.state,
        BookLinkStates.waiting_for_yandex_url.state,
        BookLinkStates.waiting_for_litres_url.state,
        BookLinkStates.waiting_for_audio_format.state,
        MailingStates.waiting_for_text.state
    ]
    
    file_states = [
        BookManagementStates.waiting_for_zip_file.state
    ]
    
    if state_name in text_states:
        return "📝 Ожидается текстовое сообщение."
    elif state_name in file_states:
        return "📎 Ожидается файл (документ)."
    else:
        return "📝 Ожидается текст или следуйте инструкциям выше."


# Дополнительные обработчики для улучшения UX

@router.message(StateFilter(BookManagementStates.waiting_for_zip_file), F.content_type != ContentType.DOCUMENT)
async def handle_wrong_file_type(message: Message) -> None:
    """
    Обработчик неверного типа файла при ожидании ZIP
    
    Args:
        message (Message): Сообщение с неверным типом файла
        
    Returns:
        None
    """
    content_type_names = {
        ContentType.PHOTO: "фото",
        ContentType.VIDEO: "видео", 
        ContentType.AUDIO: "аудио",
        ContentType.VOICE: "голосовое сообщение",
        ContentType.STICKER: "стикер",
        ContentType.ANIMATION: "GIF"
    }
    
    content_name = content_type_names.get(message.content_type, "этот тип файла")
    
    await message.answer(
        f"❌ <b>Неподходящий тип файла!</b>\n\n"
        f"Вы отправили: {content_name}\n"
        f"Ожидается: ZIP-архив с книгами\n\n"
        f"📁 Отправьте ZIP-файл как документ\n"
        f"❌ Для отмены используйте /cancel",
        parse_mode="HTML"
    )


# Убираем обработчик /help из cancel_handlers.py, так как он конфликтует
# с основным обработчиком в user_handlers.py
"""
@file: utils/states.py
@description: Состояния FSM для различных сценариев
@dependencies: aiogram.fsm.state
@created: 2024-01-15
"""

from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Состояния для процесса регистрации"""
    waiting_for_phrase = State()


class BookSearchStates(StatesGroup):
    """Состояния для поиска книг"""
    waiting_for_query = State()


class EventCreationStates(StatesGroup):
    """Состояния для создания событий (админ)"""
    waiting_for_title = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_description = State()


class UserManagementStates(StatesGroup):
    """Состояния для управления пользователями (админ)"""
    waiting_for_user_id = State()
    waiting_for_action = State()


class BookManagementStates(StatesGroup):
    """Состояния для управления книгами (админ)"""
    waiting_for_book_title = State()
    waiting_for_author = State()
    waiting_for_description = State()
    waiting_for_file_path = State()
    waiting_for_zip_file = State()
    waiting_for_yandex_url = State()
    waiting_for_litres_url = State()
    waiting_for_audio_format = State()


class BookLinkStates(StatesGroup):
    """Состояния для редактирования ссылок на книги (админ)"""
    waiting_for_yandex_url = State()
    waiting_for_litres_url = State()
    waiting_for_audio_format = State() 
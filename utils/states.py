"""
@file: utils/states.py
@description: Состояния FSM для бота
@dependencies: aiogram.fsm.state
@created: 2025-01-03
"""

from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Состояния для регистрации пользователя"""
    waiting_for_secret_phrase = State()


class BookSearchStates(StatesGroup):
    """Состояния для поиска книг"""
    waiting_for_search_query = State()


class BookAddStates(StatesGroup):
    """Состояния для добавления книг"""
    waiting_for_book_file = State()  # Ожидание ZIP файла с книгой
    waiting_for_book_title = State()  # Ручной ввод названия
    waiting_for_book_author = State()  # Ручной ввод автора
    waiting_for_book_description = State()  # Описание книги
    waiting_for_yandex_link = State()  # Ссылка на Яндекс.Книги
    waiting_for_litres_link = State()  # Ссылка на ЛитРес
    waiting_for_audio_link = State()  # Ссылка на аудиокнигу
    waiting_for_confirmation = State()  # Подтверждение добавления


class EventAddStates(StatesGroup):
    """Состояния для добавления событий"""
    waiting_for_event_title = State()  # Название события
    waiting_for_event_date = State()  # Дата события
    waiting_for_event_time = State()  # Время события
    waiting_for_event_description = State()  # Описание события
    waiting_for_event_book = State()  # Выбор книги для события
    waiting_for_event_confirmation = State()  # Подтверждение события 
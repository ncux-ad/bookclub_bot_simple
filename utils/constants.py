"""
@file: utils/constants.py
@description: Константы для унификации callback_data и предотвращения конфликтов
@dependencies: None
@created: 2025-01-06
"""


class CallbackPrefixes:
    """
    Унифицированные префиксы для callback_data
    
    Цель: предотвратить конфликты между похожими префиксами
    типа "book:" и "book_", "download:" и "download_"
    """
    
    # === КНИГИ ===
    BOOK_SHOW = "book_show"           # Показать книгу (замена "book:")
    BOOK_CARD = "book_card"           # Карточка книги (замена "book_")
    BOOK_DOWNLOAD = "book_dl"         # Скачать книгу (замена "download:")
    BOOK_DOWNLOAD_ALT = "book_down"   # Альтернативное скачивание (замена "download_")
    BOOK_EDIT = "book_edit"           # Редактировать книгу
    BOOK_DELETE = "book_del"          # Удалить книгу
    
    # === ПОЛЬЗОВАТЕЛИ ===
    USER_DETAIL = "user_show"         # Детали пользователя (замена "user_detail_")
    USER_BAN = "user_ban"             # Заблокировать
    USER_UNBAN = "user_unban"         # Разблокировать
    USER_ROLE = "user_role"           # Управление ролями
    USER_TAG = "user_tag"             # Управление тегами
    USER_ACTIVITY = "user_activity"   # Активность пользователя
    
    # === АДМИНИСТРИРОВАНИЕ ===
    ADMIN_STATS = "admin_stats"       # Статистика
    ADMIN_USERS = "admin_users"       # Управление пользователями
    ADMIN_BOOKS = "admin_books"       # Управление книгами
    ADMIN_EVENTS = "admin_events"     # Управление событиями
    ADMIN_BACK = "admin_back"         # Назад в админ-панель
    
    # === ССЫЛКИ НА КНИГИ ===
    LINK_YANDEX = "link_yandex"       # Яндекс.Книги
    LINK_LITRES = "link_litres"       # ЛитРес
    LINK_AUDIO = "link_audio"         # Аудиоформат
    
    # === НАВИГАЦИЯ ===
    BACK_TO_BOOKS = "back_books"      # Назад к книгам
    BACK_TO_LIBRARY = "back_lib"      # Назад к библиотеке
    BACK_TO_EDITLINKS = "back_editlinks"  # Назад к редактированию ссылок
    
    # === ФИЛЬТРАЦИЯ И СОРТИРОВКА ===
    USERS_FILTER = "users_filter"     # Фильтр пользователей
    USERS_PAGE = "users_page"         # Пагинация пользователей
    USERS_SEARCH = "users_search"     # Поиск пользователей
    USERS_EXPORT = "users_export"     # Экспорт пользователей
    
    # === РОЛИ ===
    USER_SET_ROLE = "user_setrole"    # Установить роль


class CallbackActions:
    """Стандартные действия для callback_data"""
    
    SHOW = "show"
    EDIT = "edit"
    DELETE = "delete"
    DOWNLOAD = "download"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    NEXT = "next"
    PREV = "prev"
    FILTER = "filter"
    SORT = "sort"
    BAN = "ban"
    UNBAN = "unban"
    ADD = "add"
    REMOVE = "remove"


class CallbackData:
    """
    Утилитарные методы для создания callback_data
    
    Обеспечивает консистентность формата и автоматическую
    обработку длинных названий
    """
    
    @staticmethod
    def create(prefix: str, action: str = "", data: str = "") -> str:
        """
        Создать callback_data в едином формате
        
        Args:
            prefix (str): Префикс из CallbackPrefixes
            action (str): Действие из CallbackActions
            data (str): Дополнительные данные
            
        Returns:
            str: Сформированный callback_data
        """
        parts = [prefix]
        
        if action:
            parts.append(action)
        
        if data:
            parts.append(data)
        
        callback = "_".join(parts)
        
        # Обрезаем если превышает лимит Telegram (64 байта)
        if len(callback.encode('utf-8')) > 64:
            # Обрезаем data, сохраняя структуру
            max_data_len = 64 - len("_".join(parts[:-1]).encode('utf-8')) - 1
            if max_data_len > 0:
                data = data[:max_data_len]
                parts[-1] = data
                callback = "_".join(parts)
        
        return callback
    
    @staticmethod
    def parse(callback_data: str) -> tuple[str, str, str]:
        """
        Разобрать callback_data на компоненты
        
        Args:
            callback_data (str): Callback data для разбора
            
        Returns:
            tuple[str, str, str]: (prefix, action, data)
        """
        parts = callback_data.split("_", 2)
        
        prefix = parts[0] if len(parts) > 0 else ""
        action = parts[1] if len(parts) > 1 else ""
        data = parts[2] if len(parts) > 2 else ""
        
        return prefix, action, data


# === МИГРАЦИОННАЯ ТАБЛИЦА ===
# Для постепенной замены старых префиксов на новые

CALLBACK_MIGRATION_MAP = {
    # Старый префикс -> Новый префикс
    "book:": CallbackPrefixes.BOOK_SHOW,
    "book_": CallbackPrefixes.BOOK_CARD,
    "download:": CallbackPrefixes.BOOK_DOWNLOAD,
    "download_": CallbackPrefixes.BOOK_DOWNLOAD_ALT,
    "editlinks_": CallbackPrefixes.BOOK_EDIT,
    "user_detail_": CallbackPrefixes.USER_DETAIL,
    "user_ban_": CallbackPrefixes.USER_BAN,
    "user_unban_": CallbackPrefixes.USER_UNBAN,
    "user_roles_": CallbackPrefixes.USER_ROLE,
    "user_addtag_": CallbackPrefixes.USER_TAG,
    "user_activity_": CallbackPrefixes.USER_ACTIVITY,
    "user_setrole_": CallbackPrefixes.USER_SET_ROLE,
    "link_yandex_": CallbackPrefixes.LINK_YANDEX,
    "link_litres_": CallbackPrefixes.LINK_LITRES,
    "link_audio_": CallbackPrefixes.LINK_AUDIO,
    "users_filter_": CallbackPrefixes.USERS_FILTER,
    "users_page_": CallbackPrefixes.USERS_PAGE,
    "users_search": CallbackPrefixes.USERS_SEARCH,
    "users_export": CallbackPrefixes.USERS_EXPORT,
    "admin_stats": CallbackPrefixes.ADMIN_STATS,
    "admin_back": CallbackPrefixes.ADMIN_BACK,
    "back_to_books": CallbackPrefixes.BACK_TO_BOOKS,
    "back_to_editlinks": CallbackPrefixes.BACK_TO_EDITLINKS,
}


def migrate_callback_data(old_callback: str) -> str:
    """
    Мигрировать старый callback_data в новый формат
    
    Args:
        old_callback (str): Старый callback_data
        
    Returns:
        str: Новый callback_data или исходный, если миграция не нужна
    """
    for old_prefix, new_prefix in CALLBACK_MIGRATION_MAP.items():
        if old_callback.startswith(old_prefix):
            # Заменяем префикс
            data_part = old_callback[len(old_prefix):]
            return f"{new_prefix}_{data_part}" if data_part else new_prefix
    
    return old_callback


def check_callback_conflicts() -> List[str]:
    """
    Проверить конфликты между callback_data префиксами
    
    Returns:
        List[str]: Список найденных конфликтов
    """
    prefixes = []
    conflicts = []
    
    # Собираем все префиксы из класса
    for attr_name in dir(CallbackPrefixes):
        if not attr_name.startswith('_'):
            prefix = getattr(CallbackPrefixes, attr_name)
            if isinstance(prefix, str):
                prefixes.append(prefix)
    
    # Ищем потенциальные конфликты
    for i, prefix1 in enumerate(prefixes):
        for prefix2 in prefixes[i+1:]:
            if prefix1.startswith(prefix2) or prefix2.startswith(prefix1):
                conflicts.append(f"Конфликт: '{prefix1}' и '{prefix2}'")
    
    return conflicts
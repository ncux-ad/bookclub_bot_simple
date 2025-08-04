"""
@file: utils/validators.py
@description: Валидаторы для FSM и пользовательского ввода
@dependencies: typing, re
@created: 2025-01-06
"""

import re
from typing import Optional, Tuple, List
from pathlib import Path


class ValidationResult:
    """Результат валидации"""
    
    def __init__(self, is_valid: bool, error_message: str = "", cleaned_value: str = ""):
        self.is_valid = is_valid
        self.error_message = error_message
        self.cleaned_value = cleaned_value


class FSMValidators:
    """Валидаторы для FSM состояний"""
    
    @staticmethod
    def validate_book_title(title: str) -> ValidationResult:
        """
        Валидация названия книги
        
        Args:
            title (str): Название книги
            
        Returns:
            ValidationResult: Результат валидации
        """
        if not title or not title.strip():
            return ValidationResult(False, "❌ Название книги не может быть пустым!")
        
        cleaned_title = title.strip()
        
        if len(cleaned_title) < 2:
            return ValidationResult(False, "❌ Название книги слишком короткое (минимум 2 символа)!")
        
        if len(cleaned_title) > 200:
            return ValidationResult(False, "❌ Название книги слишком длинное (максимум 200 символов)!")
        
        # Проверка на недопустимые символы
        invalid_chars = ['<', '>', '"', '|', '\\', '/', ':', '*', '?']
        for char in invalid_chars:
            if char in cleaned_title:
                return ValidationResult(False, f"❌ Название содержит недопустимый символ: {char}")
        
        return ValidationResult(True, "", cleaned_title)
    
    @staticmethod
    def validate_author_name(author: str) -> ValidationResult:
        """
        Валидация имени автора
        
        Args:
            author (str): Имя автора
            
        Returns:
            ValidationResult: Результат валидации
        """
        if not author or not author.strip():
            return ValidationResult(False, "❌ Имя автора не может быть пустым!")
        
        cleaned_author = author.strip()
        
        if len(cleaned_author) < 2:
            return ValidationResult(False, "❌ Имя автора слишком короткое (минимум 2 символа)!")
        
        if len(cleaned_author) > 100:
            return ValidationResult(False, "❌ Имя автора слишком длинное (максимум 100 символов)!")
        
        # Проверка на цифры в начале (некорректные имена типа "123 Автор")
        if cleaned_author[0].isdigit():
            return ValidationResult(False, "❌ Имя автора не может начинаться с цифры!")
        
        return ValidationResult(True, "", cleaned_author)
    
    @staticmethod
    def validate_book_description(description: str) -> ValidationResult:
        """
        Валидация описания книги
        
        Args:
            description (str): Описание книги
            
        Returns:
            ValidationResult: Результат валидации
        """
        if not description or not description.strip():
            return ValidationResult(False, "❌ Описание не может быть пустым! Напишите хотя бы краткое описание.")
        
        cleaned_description = description.strip()
        
        if len(cleaned_description) < 10:
            return ValidationResult(False, "❌ Описание слишком короткое (минимум 10 символов)!")
        
        if len(cleaned_description) > 2000:
            return ValidationResult(False, "❌ Описание слишком длинное (максимум 2000 символов)!")
        
        return ValidationResult(True, "", cleaned_description)
    
    @staticmethod
    def validate_search_query(query: str) -> ValidationResult:
        """
        Валидация поискового запроса
        
        Args:
            query (str): Поисковый запрос
            
        Returns:
            ValidationResult: Результат валидации
        """
        if not query or not query.strip():
            return ValidationResult(False, "❌ Поисковый запрос не может быть пустым!")
        
        cleaned_query = query.strip()
        
        if len(cleaned_query) < 2:
            return ValidationResult(False, "❌ Слишком короткий запрос (минимум 2 символа)!")
        
        if len(cleaned_query) > 100:
            return ValidationResult(False, "❌ Слишком длинный запрос (максимум 100 символов)!")
        
        # Проверка на подозрительные запросы (только специальные символы)
        if re.match(r'^[^\w\s]+$', cleaned_query):
            return ValidationResult(False, "❌ Запрос должен содержать буквы или цифры!")
        
        return ValidationResult(True, "", cleaned_query)
    
    @staticmethod
    def validate_secret_phrase(phrase: str) -> ValidationResult:
        """
        Валидация секретной фразы
        
        Args:
            phrase (str): Секретная фраза
            
        Returns:
            ValidationResult: Результат валидации
        """
        if not phrase or not phrase.strip():
            return ValidationResult(False, "❌ Введите секретную фразу!")
        
        cleaned_phrase = phrase.strip()
        
        # Проверка длины (секретные фразы обычно не очень длинные)
        if len(cleaned_phrase) > 200:
            return ValidationResult(False, "❌ Фраза слишком длинная!")
        
        return ValidationResult(True, "", cleaned_phrase)
    
    @staticmethod
    def validate_url(url: str, url_type: str = "ссылка") -> ValidationResult:
        """
        Валидация URL для ссылок на книги
        
        Args:
            url (str): URL для проверки
            url_type (str): Тип ссылки для сообщения об ошибке
            
        Returns:
            ValidationResult: Результат валидации
        """
        if not url or not url.strip():
            return ValidationResult(False, f"❌ {url_type} не может быть пустой!")
        
        cleaned_url = url.strip()
        
        # Проверка на "нет" или "отсутствует" для удаления ссылки
        if cleaned_url.lower() in ['нет', 'отсутствует', 'удалить', 'delete', 'remove']:
            return ValidationResult(True, "", "")  # Пустая строка = удаление
        
        # Простая проверка формата URL
        url_pattern = re.compile(
            r'^https?://'  # http:// или https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # доменное имя
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...или IP
            r'(?::\d+)?'  # необязательный порт
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(cleaned_url):
            return ValidationResult(False, f"❌ Некорректный формат {url_type}! Используйте полный URL (например: https://example.com)")
        
        if len(cleaned_url) > 500:
            return ValidationResult(False, f"❌ {url_type} слишком длинная (максимум 500 символов)!")
        
        return ValidationResult(True, "", cleaned_url)
    
    @staticmethod
    def validate_audio_format(format_str: str) -> ValidationResult:
        """
        Валидация аудиоформата
        
        Args:
            format_str (str): Строка с описанием аудиоформата
            
        Returns:
            ValidationResult: Результат валидации
        """
        if not format_str or not format_str.strip():
            return ValidationResult(False, "❌ Описание аудиоформата не может быть пустым!")
        
        cleaned_format = format_str.strip()
        
        # Проверка на "нет" для удаления
        if cleaned_format.lower() in ['нет', 'отсутствует', 'удалить']:
            return ValidationResult(True, "", "")
        
        if len(cleaned_format) > 200:
            return ValidationResult(False, "❌ Описание аудиоформата слишком длинное (максимум 200 символов)!")
        
        return ValidationResult(True, "", cleaned_format)
    
    @staticmethod
    def validate_broadcast_text(text: str) -> ValidationResult:
        """
        Валидация текста для рассылки
        
        Args:
            text (str): Текст рассылки
            
        Returns:
            ValidationResult: Результат валидации
        """
        if not text or not text.strip():
            return ValidationResult(False, "❌ Текст рассылки не может быть пустым!")
        
        cleaned_text = text.strip()
        
        if len(cleaned_text) < 5:
            return ValidationResult(False, "❌ Текст рассылки слишком короткий (минимум 5 символов)!")
        
        if len(cleaned_text) > 4000:  # Telegram лимит ~4096 символов
            return ValidationResult(False, "❌ Текст рассылки слишком длинный (максимум 4000 символов)!")
        
        # Проверка на спам-подобный контент
        spam_indicators = ['СРОЧНО!!!', 'ЖМИТЕ СЮДА', 'ХАЛЯВА', 'ВЫИГРАЛ']
        text_upper = cleaned_text.upper()
        
        spam_count = sum(1 for indicator in spam_indicators if indicator in text_upper)
        if spam_count >= 2:
            return ValidationResult(False, "❌ Текст похож на спам! Используйте более нейтральные формулировки.")
        
        return ValidationResult(True, "", cleaned_text)


class ContentTypeValidator:
    """Валидатор типов контента (файлы, фото и т.д.)"""
    
    @staticmethod
    def validate_document_type(file_name: str, allowed_extensions: List[str] = None) -> ValidationResult:
        """
        Валидация типа документа
        
        Args:
            file_name (str): Имя файла
            allowed_extensions (List[str]): Разрешенные расширения
            
        Returns:
            ValidationResult: Результат валидации
        """
        if allowed_extensions is None:
            allowed_extensions = ['.fb2', '.epub', '.pdf', '.txt', '.mobi', '.zip']
        
        if not file_name:
            return ValidationResult(False, "❌ Имя файла не определено!")
        
        file_path = Path(file_name.lower())
        file_extension = file_path.suffix
        
        if not file_extension:
            return ValidationResult(False, "❌ Файл должен иметь расширение!")
        
        if file_extension not in [ext.lower() for ext in allowed_extensions]:
            allowed_str = ", ".join(allowed_extensions)
            return ValidationResult(False, f"❌ Неподдерживаемый формат файла! Разрешены: {allowed_str}")
        
        return ValidationResult(True, "", file_name)


def create_validation_middleware():
    """
    Создать middleware для автоматической валидации
    
    Returns:
        callable: Middleware функция
    """
    async def validation_middleware(handler, event, data):
        """Middleware для валидации входящих сообщений"""
        # Здесь можно добавить автоматическую валидацию
        # на основе текущего состояния FSM
        return await handler(event, data)
    
    return validation_middleware
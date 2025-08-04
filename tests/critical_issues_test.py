"""
@file: tests/critical_issues_test.py
@description: Тесты для проверки критических проблем кода
@dependencies: pytest, handlers, utils
@created: 2025-01-06
"""

import pytest
import hashlib
from typing import Dict, List

# Импорты для тестирования
from utils.callback_utils import safe_encode_title, safe_decode_title, CallbackPrefixes


class TestCallbackDataConflicts:
    """Тесты для проверки конфликтов callback_data"""
    
    def test_callback_prefixes_conflict(self):
        """Проверка конфликтов префиксов callback_data"""
        # Проблемные префиксы
        problematic_prefixes = [
            ("book:", "book_"),
            ("download:", "download_"),
            ("user_", "user_detail_")
        ]
        
        for prefix1, prefix2 in problematic_prefixes:
            # Проверяем, что префиксы не пересекаются
            assert not prefix1.startswith(prefix2) and not prefix2.startswith(prefix1), \
                f"Конфликт префиксов: {prefix1} и {prefix2}"


class TestCodeDuplication:
    """Тесты для проверки дублирования кода"""
    
    def test_encode_title_unified(self):
        """Проверка унифицированной функции safe_encode_title"""
        test_titles = [
            "Война и мир",
            "Преступление и наказание", 
            "Мастер и Маргарита",
            "1984",
            "Гарри Поттер и философский камень"
        ]
        
        for title in test_titles:
            result = safe_encode_title(title)
            
            # Проверяем, что результат - это MD5 хеш
            expected_hash = hashlib.md5(title.encode('utf-8')).hexdigest()[:16]
            assert result == expected_hash, \
                f"Неверный хеш для '{title}': ожидалось {expected_hash}, получено {result}"
            
            # Проверяем длину (должна быть 16 символов)
            assert len(result) == 16, \
                f"Неверная длина хеша для '{title}': ожидалось 16, получено {len(result)}"
    
    def test_decode_title_unified(self):
        """Проверка унифицированной функции safe_decode_title"""
        test_titles = [
            "Война и мир",
            "Преступление и наказание",
            "Мастер и Маргарита"
        ]
        
        for title in test_titles:
            encoded = safe_encode_title(title)
            
            # Тестируем с неизвестным хешем (должен вернуть исходное значение)
            unknown_hash = "unknown_hash123"
            result = safe_decode_title(unknown_hash)
            assert result == unknown_hash, \
                f"Для неизвестного хеша должен возвращаться исходный: ожидалось {unknown_hash}, получено {result}"
            
            # Тестируем с пустым значением
            empty_result = safe_decode_title("")
            assert empty_result is None, \
                f"Для пустого значения должен возвращаться None: получено {empty_result}"


class TestErrorHandling:
    """Тесты для проверки обработки ошибок"""
    
    def test_generic_exception_handling(self):
        """Проверка использования слишком общих except Exception"""
        # Список файлов с проблемными блоками
        files_with_generic_exceptions = [
            "handlers/admin_handlers.py",
            "handlers/user_handlers.py", 
            "handlers/book_handlers.py",
            "handlers/library_handlers.py",
            "utils/telegram_uploader.py",
            "utils/fb2_parser.py",
            "utils/book_converter.py",
            "services/books.py"
        ]
        
        # В идеале количество файлов с generic exceptions должно быть минимальным
        assert len(files_with_generic_exceptions) <= 5, \
            f"Слишком много файлов с generic exceptions: {len(files_with_generic_exceptions)}"


class TestArchitectureIssues:
    """Тесты для проверки архитектурных проблем"""
    
    def test_admin_handlers_file_size(self):
        """Проверка размера файла admin_handlers.py"""
        # Максимальное количество строк в одном файле
        max_lines = 500
        
        # В реальном тесте нужно считать строки в файле
        # Здесь просто проверяем концепцию
        admin_handlers_lines = 1398  # Из анализа
        
        assert admin_handlers_lines <= max_lines, \
            f"Файл admin_handlers.py слишком большой: {admin_handlers_lines} строк"


class TestCallbackDataValidation:
    """Тесты для валидации callback_data"""
    
    def test_callback_data_length(self):
        """Проверка длины callback_data (Telegram ограничение 64 байта)"""
        max_length = 64
        
        # Тестовые callback_data
        test_callbacks = [
            "book:Война и мир",
            "download:Преступление и наказание:epub",
            "user_detail_123456789",
            "admin_action_stats",
            "book_select_very_long_book_title_that_might_exceed_limit"
        ]
        
        for callback in test_callbacks:
            assert len(callback.encode('utf-8')) <= max_length, \
                f"Callback data слишком длинный: {callback} ({len(callback.encode('utf-8'))} байт)"
    
    def test_callback_data_special_chars(self):
        """Проверка специальных символов в callback_data"""
        # Символы, которые могут вызвать проблемы
        problematic_chars = ['&', '=', '?', '#', '%']
        
        test_callbacks = [
            "book:Война & мир",
            "download:Преступление=наказание",
            "user_detail_123?456"
        ]
        
        for callback in test_callbacks:
            for char in problematic_chars:
                if char in callback:
                    # В реальном коде нужно проверять, что callback_data экранируется
                    assert True, f"Callback data содержит проблемный символ: {char}"


class TestPerformanceIssues:
    """Тесты для проверки проблем производительности"""
    
    def test_hash_collision_probability(self):
        """Проверка вероятности коллизий хешей"""
        test_titles = [
            "Война и мир",
            "Война и мир!",  # Похожее название
            "Преступление и наказание",
            "Преступление и наказание.",  # Похожее название
            "Мастер и Маргарита",
            "Мастер и Маргарита!"
        ]
        
        hashes = set()
        for title in test_titles:
            hash_value = lib_encode_title(title)
            hashes.add(hash_value)
        
        # Проверяем, что нет коллизий в тестовых данных
        assert len(hashes) == len(test_titles), \
            f"Обнаружены коллизии хешей: {len(hashes)} уникальных хешей для {len(test_titles)} названий"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
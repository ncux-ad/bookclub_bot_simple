"""
@file: utils/book_converter.py
@description: Конвертер книг между форматами (FB2 -> EPUB -> MOBI)
@dependencies: subprocess, pathlib, tempfile, platform
@created: 2025-01-04
"""

import subprocess
import tempfile
import platform
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import shutil

from utils.logger import bot_logger


class BookConverter:
    """Конвертер книг между различными форматами"""
    
    def __init__(self):
        self.logger = bot_logger
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        self.is_windows = platform.system() == "Windows"
        
        # Определяем путь к Calibre в зависимости от ОС
        self.calibre_path = self._find_calibre_path()
    
    def _find_calibre_path(self) -> Optional[str]:
        """
        Найти путь к Calibre в зависимости от ОС
        
        Returns:
            str: Путь к ebook-convert или None
        """
        if self.is_windows:
            # Сначала проверяем портативную версию
            portable_paths = [
                "./calibre-portable/ebook-convert.exe",
                "./calibre-portable/calibre/ebook-convert.exe",
                "./calibre-portable/Calibre2/ebook-convert.exe"
            ]
            
            # Затем стандартные пути
            system_paths = [
                r"C:\Program Files\Calibre2\ebook-convert.exe",
                r"C:\Program Files (x86)\Calibre2\ebook-convert.exe",
                r"C:\Program Files\Calibre\ebook-convert.exe",
                r"C:\Program Files (x86)\Calibre\ebook-convert.exe",
                "ebook-convert.exe",  # Если в PATH
                "ebook-convert"       # Если в PATH
            ]
            
            possible_paths = portable_paths + system_paths
        else:
            # Linux/Ubuntu пути
            possible_paths = [
                "./calibre-portable/ebook-convert",
                "./calibre-portable/calibre/ebook-convert",
                "/usr/bin/ebook-convert",
                "/usr/local/bin/ebook-convert",
                "ebook-convert",  # Если в PATH
                "calibre-ebook-convert"  # Альтернативное имя
            ]
        
        for path in possible_paths:
            try:
                if self.is_windows and not path.endswith('.exe'):
                    # Проверяем с .exe для Windows
                    test_path = path + '.exe'
                    if os.path.exists(test_path):
                        return test_path
                
                # Проверяем существование файла
                if os.path.exists(path):
                    return path
                
                # Проверяем через which/where
                if self.is_windows:
                    result = subprocess.run(['where', path], capture_output=True, text=True)
                else:
                    result = subprocess.run(['which', path], capture_output=True, text=True)
                
                if result.returncode == 0:
                    return path.strip()
                    
            except Exception:
                continue
        
        return None
    
    def fb2_to_epub(self, fb2_path: str) -> Optional[str]:
        """
        Конвертировать FB2 в EPUB
        
        Args:
            fb2_path: Путь к FB2 файлу
            
        Returns:
            str: Путь к созданному EPUB файлу или None
        """
        try:
            fb2_path = Path(fb2_path)
            epub_path = self.temp_dir / f"{fb2_path.stem}.epub"
            
            if not self.calibre_path:
                self.logger.log_error(
                    Exception("Calibre не найден. Установите Calibre или добавьте в PATH"),
                    f"fb2_path: {fb2_path}"
                )
                return None
            
            # Используем Calibre для конвертации
            cmd = [
                self.calibre_path,
                str(fb2_path),
                str(epub_path)
            ]
            
            # Настройки для Windows
            if self.is_windows:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 минут таймаут
                    encoding='utf-8',
                    errors='ignore'
                )
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 минут таймаут
                )
            
            if result.returncode == 0 and epub_path.exists():
                self.logger.log_file_operation("конвертация FB2->EPUB", str(epub_path), True)
                return str(epub_path)
            else:
                self.logger.log_error(
                    Exception(f"Ошибка конвертации FB2->EPUB: {result.stderr}"),
                    f"fb2_path: {fb2_path}"
                )
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.log_error(Exception("Таймаут конвертации FB2->EPUB"), f"fb2_path: {fb2_path}")
            return None
        except Exception as e:
            self.logger.log_error(e, f"ошибка конвертации FB2->EPUB: {fb2_path}")
            return None
    
    def epub_to_mobi(self, epub_path: str) -> Optional[str]:
        """
        Конвертировать EPUB в MOBI
        
        Args:
            epub_path: Путь к EPUB файлу
            
        Returns:
            str: Путь к созданному MOBI файлу или None
        """
        try:
            epub_path = Path(epub_path)
            mobi_path = self.temp_dir / f"{epub_path.stem}.mobi"
            
            if not self.calibre_path:
                self.logger.log_error(
                    Exception("Calibre не найден. Установите Calibre или добавьте в PATH"),
                    f"epub_path: {epub_path}"
                )
                return None
            
            # Используем Calibre для конвертации
            cmd = [
                self.calibre_path,
                str(epub_path),
                str(mobi_path)
            ]
            
            # Настройки для Windows
            if self.is_windows:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 минут таймаут
                    encoding='utf-8',
                    errors='ignore'
                )
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 минут таймаут
                )
            
            if result.returncode == 0 and mobi_path.exists():
                self.logger.log_file_operation("конвертация EPUB->MOBI", str(mobi_path), True)
                return str(mobi_path)
            else:
                self.logger.log_error(
                    Exception(f"Ошибка конвертации EPUB->MOBI: {result.stderr}"),
                    f"epub_path: {epub_path}"
                )
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.log_error(Exception("Таймаут конвертации EPUB->MOBI"), f"epub_path: {epub_path}")
            return None
        except Exception as e:
            self.logger.log_error(e, f"ошибка конвертации EPUB->MOBI: {epub_path}")
            return None
    
    def convert_book_formats(self, fb2_path: str) -> Dict[str, str]:
        """
        Конвертировать книгу во все форматы
        
        Args:
            fb2_path: Путь к исходному FB2 файлу
            
        Returns:
            Dict[str, str]: Словарь с путями к файлам разных форматов
        """
        converted_files = {}
        
        # Добавляем исходный FB2 файл
        converted_files['fb2'] = fb2_path
        
        # Конвертируем в EPUB
        epub_path = self.fb2_to_epub(fb2_path)
        if epub_path:
            converted_files['epub'] = epub_path
            
            # Конвертируем EPUB в MOBI
            mobi_path = self.epub_to_mobi(epub_path)
            if mobi_path:
                converted_files['mobi'] = mobi_path
        
        return converted_files
    
    def check_calibre_installed(self) -> bool:
        """
        Проверить, установлен ли Calibre
        
        Returns:
            bool: True если Calibre установлен
        """
        if self.calibre_path:
            try:
                if self.is_windows:
                    result = subprocess.run(
                        [self.calibre_path, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        encoding='utf-8',
                        errors='ignore'
                    )
                else:
                    result = subprocess.run(
                        [self.calibre_path, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False
        return False
    
    def get_installation_instructions(self) -> str:
        """
        Получить инструкции по установке Calibre
        
        Returns:
            str: Инструкции для установки
        """
        if self.is_windows:
            return """
📚 <b>Установка портативного Calibre для Windows:</b>

1. Скачайте Calibre Portable:
   https://calibre-ebook.com/download_windows
   (выберите "Calibre Portable")

2. Распакуйте в папку calibre-portable/ в корне бота

3. Убедитесь, что файл ebook-convert.exe находится в:
   calibre-portable/ebook-convert.exe

4. Используйте /checkcalibre для проверки

📝 <b>Альтернативно:</b>
Установите обычную версию Calibre в систему
            """
        else:
            return """
📚 <b>Установка Calibre для Ubuntu/Linux:</b>

1. Установите через apt:
   sudo apt update
   sudo apt install calibre

2. Или скопируйте в папку calibre-portable/:
   cp /usr/bin/ebook-convert ./calibre-portable/

3. Проверьте установку:
   ebook-convert --version
            """
    
    def cleanup_temp_files(self, file_paths: list) -> None:
        """
        Очистить временные файлы
        
        Args:
            file_paths: Список путей к файлам для удаления
        """
        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    self.logger.log_file_operation("удаление временного файла", file_path, True)
            except Exception as e:
                self.logger.log_error(e, f"ошибка удаления временного файла: {file_path}")


# Создаем глобальный экземпляр конвертера
book_converter = BookConverter() 
# 🚀 Быстрая установка портативного Calibre

## Для Windows:

### Вариант 1: Портативная версия (рекомендуется)

1. **Скачайте Calibre Portable:**
   - Перейдите на https://calibre-ebook.com/download_windows
   - Выберите "Calibre Portable" (не обычную версию)

2. **Распакуйте в папку бота:**
   - Распакуйте архив в папку `calibre-portable/` в корне бота
   - Убедитесь, что файл `ebook-convert.exe` находится в `calibre-portable/ebook-convert.exe`

3. **Проверьте установку:**
   ```bash
   python test_calibre.py
   ```

### Вариант 2: Системная установка

1. **Установите Calibre:**
   - Скачайте обычную версию с https://calibre-ebook.com/download_windows
   - Установите в папку по умолчанию

2. **Проверьте установку:**
   ```bash
   python test_calibre.py
   ```

## Для Ubuntu/Linux:

### Вариант 1: Через apt (рекомендуется)

```bash
sudo apt update
sudo apt install calibre
python test_calibre.py
```

### Вариант 2: Портативная версия

```bash
# Скопируйте из системной установки
cp /usr/bin/ebook-convert ./calibre-portable/
python test_calibre.py
```

## ✅ Проверка в боте

После установки используйте команду `/checkcalibre` в боте для проверки.

## 🔧 Устранение проблем

- Если Calibre не найден, проверьте пути в `test_calibre.py`
- Убедитесь, что файл `ebook-convert.exe` (Windows) или `ebook-convert` (Linux) существует
- Для Windows: проверьте, что файл находится в правильной папке

## 📝 Примечания

- Портативная версия не требует установки в систему
- Все файлы Calibre остаются в папке бота
- Работает на любом компьютере без дополнительной настройки
- Бот автоматически найдет Calibre в портативной или системной установке 
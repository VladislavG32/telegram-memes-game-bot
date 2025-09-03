# text_utils.py
def safe_text(text, default="Текст"):
    """
    Безопасная обработка текста с проблемами кодировки
    """
    if text is None:
        return default
        
    try:
        # Если это bytes, пробуем декодировать
        if isinstance(text, bytes):
            try:
                return text.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    return text.decode('latin-1')
                except UnicodeDecodeError:
                    return default
        
        # Если это строка, проверяем кодировку
        if isinstance(text, str):
            # Пробуем закодировать в UTF-8
            text.encode('utf-8')
            return text
            
        # Для других типов преобразуем в строку
        return str(text)
        
    except UnicodeEncodeError:
        try:
            # Пробуем latin-1 как fallback
            return text.encode('latin-1').decode('utf-8', errors='ignore')
        except:
            return default
    except Exception:
        return default

def safe_filename(text, default="file"):
    """
    Безопасное имя файла
    """
    safe = safe_text(text, default)
    # Убираем проблемные символы
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        safe = safe.replace(char, '_')
    return safe
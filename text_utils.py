# text_utils.py
def safe_text(text, default="�����"):
    """
    ���������� ��������� ������ � ���������� ���������
    """
    if text is None:
        return default
        
    try:
        # ���� ��� bytes, ������� ������������
        if isinstance(text, bytes):
            try:
                return text.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    return text.decode('latin-1')
                except UnicodeDecodeError:
                    return default
        
        # ���� ��� ������, ��������� ���������
        if isinstance(text, str):
            # ������� ������������ � UTF-8
            text.encode('utf-8')
            return text
            
        # ��� ������ ����� ����������� � ������
        return str(text)
        
    except UnicodeEncodeError:
        try:
            # ������� latin-1 ��� fallback
            return text.encode('latin-1').decode('utf-8', errors='ignore')
        except:
            return default
    except Exception:
        return default

def safe_filename(text, default="file"):
    """
    ���������� ��� �����
    """
    safe = safe_text(text, default)
    # ������� ���������� �������
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        safe = safe.replace(char, '_')
    return safe
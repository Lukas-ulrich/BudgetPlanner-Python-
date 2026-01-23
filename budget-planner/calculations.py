from datetime import datetime, timedelta
import re
import numpy as np

def validate_month_format(ym_str):
    """Validiert YYYY-MM Format"""
    pattern = r'^\d{4}-\d{2}$'
    if not re.match(pattern, ym_str):
        return False
    try:
        year, month = map(int, ym_str.split('-'))
        return 1 <= month <= 12 and 1900 <= year <= 2100
    except:
        return False

def get_previous_month(ym_str):
    """Gibt den vorherigen Monat zurück"""
    try:
        year, month = map(int, ym_str.split('-'))
        if month == 1:
            return f"{year-1}-12"
        else:
            return f"{year}-{month-1:02d}"
    except:
        return None

def get_next_month(ym_str):
    """Gibt den nächsten Monat zurück"""
    try:
        year, month = map(int, ym_str.split('-'))
        if month == 12:
            return f"{year+1}-01"
        else:
            return f"{year}-{month+1:02d}"
    except:
        return None

def month_key_from_selection(ym_str):
    return ym_str.strip()

def ensure_float(s):
    """Konvertiert String zu Float mit Fehlerbehandlung"""
    try:
        s = str(s).strip().replace(',', '.')
        if s == "":
            return 0.0
        return float(s)
    except (ValueError, AttributeError):
        return 0.0
    
def ensure_dir(path):
    """Erstellt Verzeichnis falls nicht vorhanden"""
    if not os.path.exists(path):
        os.makedirs(path)

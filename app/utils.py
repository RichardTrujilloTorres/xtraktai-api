"""
Utility functions for the Receipt Processing API
"""
from datetime import datetime
from typing import Optional
import re


def parse_date(date_string: str) -> Optional[str]:
    """
    Parse various date formats to ISO format (YYYY-MM-DD)
    
    Args:
        date_string: Date in various formats
        
    Returns:
        Date in YYYY-MM-DD format or None
    """
    if not date_string:
        return None
    
    # Common date formats
    date_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_string.strip(), fmt)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return None


def parse_time(time_string: str) -> Optional[str]:
    """
    Parse various time formats to HH:MM format (24-hour)
    
    Args:
        time_string: Time in various formats
        
    Returns:
        Time in HH:MM format or None
    """
    if not time_string:
        return None
    
    # Common time formats
    time_formats = [
        "%H:%M",
        "%H:%M:%S",
        "%I:%M %p",
        "%I:%M:%S %p",
    ]
    
    for fmt in time_formats:
        try:
            parsed_time = datetime.strptime(time_string.strip(), fmt)
            return parsed_time.strftime("%H:%M")
        except ValueError:
            continue
    
    return None


def extract_amount(amount_string: str) -> Optional[float]:
    """
    Extract numeric amount from string (handles currency symbols)
    
    Args:
        amount_string: String containing amount
        
    Returns:
        Float amount or None
    """
    if not amount_string:
        return None
    
    # Remove common currency symbols and whitespace
    cleaned = re.sub(r'[$€£¥,\s]', '', amount_string)
    
    try:
        return float(cleaned)
    except ValueError:
        return None


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format amount as currency string
    
    Args:
        amount: Numeric amount
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    currency_symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
    }
    
    symbol = currency_symbols.get(currency, currency)
    return f"{symbol}{amount:.2f}"


def clean_text(text: str) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Raw text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Remove special characters (but keep basic punctuation)
    text = re.sub(r'[^\w\s.,!?;:\-\(\)/@]', '', text)
    
    return text.strip()


def validate_file_size(file_size_bytes: int, max_size_mb: int = 10) -> bool:
    """
    Validate file size is within limits
    
    Args:
        file_size_bytes: File size in bytes
        max_size_mb: Maximum size in MB
        
    Returns:
        True if valid, False otherwise
    """
    max_bytes = max_size_mb * 1024 * 1024
    return file_size_bytes <= max_bytes

import asyncio
from typing import Any, Callable, TypeVar
from functools import wraps

T = TypeVar('T')

def async_retry(max_attempts: int = 3, delay: float = 1.0):
    """Decorator for async functions with retry logic"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
                    
            raise last_exception
        return wrapper
    return decorator

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def clean_html_text(text: str) -> str:
    """Clean HTML artifacts from text"""
    import re
    
    text = re.sub(r'<[^>]+>', '', text)
   
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

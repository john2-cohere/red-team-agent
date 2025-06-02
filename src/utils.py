import asyncio
import functools
import logging
from typing import Any, Callable, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar('T')

def retry_async(max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0, 
               exceptions: tuple = (Exception,)) -> Callable:
    """
    Retry decorator for async functions.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff_factor: Multiplier for delay on each retry (default: 2.0)
        exceptions: Tuple of exception types to retry on (default: (Exception,))
    
    Usage:
        @retry_async(max_retries=3, delay=1.0)
        async def my_function():
            # function implementation
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 because we want max_retries attempts after the first try
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"Function {func.__name__} succeeded on attempt {attempt + 1}")
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries + 1} attempts. Final error: {e}")
                        raise e
                    
                    logger.warning(f"Function {func.__name__} failed on attempt {attempt + 1}/{max_retries + 1}: {e}")
                    logger.info(f"Retrying in {current_delay} seconds...")
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
            
            # This should never be reached, but just in case
            raise last_exception
            
        return wrapper
    return decorator

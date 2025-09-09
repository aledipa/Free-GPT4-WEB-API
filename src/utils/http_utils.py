"""HTTP utilities for handling timeouts and retries."""

import asyncio
import time
from typing import Optional, Dict, Any, Callable, Awaitable
from functools import wraps

from .logging import logger

class TimeoutConfig:
    """Configuration for timeouts and retries."""
    
    DEFAULT_TIMEOUT = 60  # 60 seconds
    CONNECT_TIMEOUT = 10  # 10 seconds for connection
    READ_TIMEOUT = 50     # 50 seconds for reading response
    MAX_RETRIES = 3       # Maximum number of retries
    RETRY_DELAY = 2       # Delay between retries in seconds
    BACKOFF_FACTOR = 2    # Exponential backoff factor

def timeout_handler(timeout_seconds: float = TimeoutConfig.DEFAULT_TIMEOUT):
    """Decorator to add timeout handling to async functions."""
    
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                logger.warning(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
                raise
        return wrapper
    return decorator

def retry_handler(
    max_retries: int = TimeoutConfig.MAX_RETRIES,
    delay: float = TimeoutConfig.RETRY_DELAY,
    backoff_factor: float = TimeoutConfig.BACKOFF_FACTOR,
    exceptions: tuple = (Exception,)
):
    """Decorator to add retry logic to async functions."""
    
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    logger.info(f"Retrying in {current_delay} seconds...")
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        return wrapper
    return decorator

async def safe_api_call(
    api_func: Callable[..., Awaitable[Any]],
    *args,
    timeout: float = TimeoutConfig.DEFAULT_TIMEOUT,
    max_retries: int = TimeoutConfig.MAX_RETRIES,
    **kwargs
) -> Optional[Any]:
    """Safely call an API function with timeout and retry logic.
    
    Args:
        api_func: The async function to call
        *args: Positional arguments for the function
        timeout: Timeout in seconds
        max_retries: Maximum number of retries
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the API call or None if all attempts failed
    """
    current_delay = TimeoutConfig.RETRY_DELAY
    
    for attempt in range(max_retries + 1):
        try:
            return await asyncio.wait_for(api_func(*args, **kwargs), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"API call timed out (attempt {attempt + 1}/{max_retries + 1})")
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for specific error types
            if "401" in error_msg or "unauthorized" in error_msg:
                logger.warning(f"API call returned unauthorized error: {e}")
                return None  # Don't retry auth errors
            elif "chrome" in error_msg or "browser" in error_msg:
                logger.warning(f"API call requires browser: {e}")
                return None  # Don't retry browser errors
            elif "too slow" in error_msg or "timeout" in error_msg:
                logger.warning(f"API call connection timeout (attempt {attempt + 1}/{max_retries + 1}): {e}")
            else:
                logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
        
        # Don't wait after the last attempt
        if attempt < max_retries:
            logger.info(f"Retrying in {current_delay} seconds...")
            await asyncio.sleep(current_delay)
            current_delay *= TimeoutConfig.BACKOFF_FACTOR
    
    logger.error(f"API call failed after {max_retries + 1} attempts")
    return None

def configure_g4f_timeouts():
    """Configure g4f library with appropriate timeouts."""
    try:
        import g4f
        
        # Try to set global timeout if supported
        if hasattr(g4f, 'timeout'):
            g4f.timeout = TimeoutConfig.DEFAULT_TIMEOUT
        
        # Set environment variables that might be used by underlying libraries
        import os
        os.environ.setdefault('REQUESTS_TIMEOUT', str(TimeoutConfig.DEFAULT_TIMEOUT))
        os.environ.setdefault('HTTP_TIMEOUT', str(TimeoutConfig.DEFAULT_TIMEOUT))
        
        logger.debug("Configured g4f timeouts")
    except Exception as e:
        logger.warning(f"Could not configure g4f timeouts: {e}")

# Configure timeouts on import
configure_g4f_timeouts()

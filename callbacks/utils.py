import logging
import time

def log_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        logging.info(f"{func.__name__} executed in {duration:.4f} seconds")
        return result
    return wrapper
import time
import functools


def timing_decorator(func):
    """Decorator to measure execution time of pipeline processing."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed_microseconds = (end - start) * 1_000_000
        
        # Set processing time on DiameterMessage
        if func.__name__ == 'main_pipeline' and len(args) >= 2:
            context = args[1]
            diameter_message = context.message
            diameter_message.processing_time_microseconds = elapsed_microseconds
        return result
    return wrapper

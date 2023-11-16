import functools
import time
import logging

logger = logging.getLogger()


# def timing_decorator(func):
#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         start_time = time.time()
#         result = func(*args, **kwargs)
#         end_time = time.time()
#         if inspect.isgenerator(result):
#             # If the result is a generator, log the start time and return the generator object directly.
#             logger.info(f"Generator function {func.__name__!r} started execution")
#             return result
#         else:
#             # If it's not a generator, log the execution time.
#             logger.info(f"Function {func.__name__!r} executed in {(end_time - start_time):.4f}s")
#             return result
#     return wrapper


def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"Function {func.__name__!r} executed in {(end_time - start_time):.4f}s")
        return result

    return wrapper

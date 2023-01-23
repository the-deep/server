import time


class log_time:
    """
    A decorator to track time of excecution. Can also be used as context manager
    as with statement
    """
    def __init__(self, block_name="BLOCK", log_function=print):
        self.block_name = block_name
        self.start = 0
        self.end = 0
        self.log_function = log_function

    def __enter__(self, *args, **kwargs):
        self.start = time.time()

    def log(self):
        dtime = self.end - self.start
        self.log_function(f"{self.block_name} took {round(dtime, 4)} seconds.")

    def __exit__(self, *args, **kwargs):
        self.end = time.time()
        self.log()

    def __call__(self, f):
        self.block_name = f.__name__

        def wrapped_f(*args, **kwargs):
            self.start = time.time()
            res = f(*args, **kwargs)
            self.end = time.time()
            self.log()
            return res

        wrapped_f.__name__ = f.__name__
        return wrapped_f


def warn_on_exception(logger, exceptions=[]):
    """A decorator that just catches exceptions and warns"""
    def wrapper(f):
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except (exceptions or Exception) as e:
                logger.warning(f"Error: {e}", exc_info=True)
        return wrapped
    return wrapper

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

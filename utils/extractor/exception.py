class ExtractError(Exception):
    def __init__(self, *args, **kwargs):
        super(ExtractError, self).__init__(*args, **kwargs)

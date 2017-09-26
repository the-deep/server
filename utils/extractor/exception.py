class StripError(Exception):
    def __init__(self, *args, **kwargs):
        super(StripError, self).__init__(*args, **kwargs)

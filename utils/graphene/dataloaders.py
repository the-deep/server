from promise.dataloader import DataLoader


class WithContextMixin():
    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop('context')
        super().__init__(*args, **kwargs)


class DataLoaderWithContext(WithContextMixin, DataLoader):
    # def batch_load_fn  TODO: Add logging for errors traceback (for graphene v3)
    pass

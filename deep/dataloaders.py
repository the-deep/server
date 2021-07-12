from promise.dataloader import DataLoader


class DataLoaderWithContext(DataLoader):
    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop('context')
        super().__init__(*args, **kwargs)
    # def batch_load_fn

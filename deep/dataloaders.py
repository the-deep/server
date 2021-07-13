from aiodataloader import DataLoader


class DataLoaderWithContext(DataLoader):
    """
    New Documentation: https://github.com/graphql-python/graphene/pull/1190/files

    """
    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop('context')
        super().__init__(*args, **kwargs)
    # def batch_load_fn

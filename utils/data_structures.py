
class Dict(dict):
    """
    Dict class where items can be accessed/set using dot notation
    """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __convert_nested(self, d):
        """ convert dictionary(nested) to Dict """
        new_kw = {}
        for k, v in d.items():
            if isinstance(v, dict):
                new_kw[k] = Dict(**v)
            else:
                new_kw[k] = v
        return new_kw

    def __init__(self, *args, **kwargs):
        # This is for nested constructor dict
        newargs = []
        for i, arg in enumerate(args):
            if isinstance(arg, dict):
                newargs.append(self.__convert_nested(arg))
            else:
                newargs.append(arg)
        newkwargs = self.__convert_nested(kwargs)
        super().__init__(*newargs, **newkwargs)

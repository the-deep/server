from collections import OrderedDict


class Schema:
    def __init__(self, title='', description='', **kwargs):
        self.title = title
        self.description = description
        self.kwargs = kwargs

    def __repr__(self):
        return str(self)

    def __str__(self):
        return 'Data'


class Integer(Schema):
    def __str__(self):
        return 'int'


class String(Schema):
    def __str__(self):
        return 'string'


class Number(Schema):
    def __str__(self):
        return 'number'


class Boolean(Schema):
    def __str__(self):
        return 'boolean'


class Enum(Schema):
    def __init__(self, enum=[], title='', description='', **kwargs):
        super(Enum, self).__init__(title, description, **kwargs)
        self.enum = enum

    def __str__(self):
        return 'One of ({})'.format(
            ','.join(str(e) for e in self.enum)
        )


class Array(Schema):
    def __init__(self, items=None, title='', description='', **kwargs):
        super(Array, self).__init__(title, description, **kwargs)
        self.items = items

    def __str__(self):
        return 'List of {}'.format(str(self.items))


class Object(Schema):
    def __init__(self, properties=OrderedDict([]), title='', description='',
                 **kwargs):
        super(Object, self).__init__(title, description, **kwargs)
        self.properties = properties

    def __str__(self):
        return 'Object of {{}}'.format(
            '{}: {}'.format(key, str(value))
            for key, value in self.properties.items()
        )

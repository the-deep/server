from collections import OrderedDict


class Schema:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '"Data"'


class Recursive(Schema):
    def __str__(self):
        return '"*"'


class Integer(Schema):
    def __str__(self):
        return '"int"'


class String(Schema):
    def __str__(self):
        return '"string"'


class Number(Schema):
    def __str__(self):
        return '"number"'


class Boolean(Schema):
    def __str__(self):
        return '"boolean"'


class CustomJson(Schema):
    def __str__(self):
        return '"custom json data"'


class Date(Schema):
    def __str__(self):
        return '"date"'


class Time(Schema):
    def __str__(self):
        return '"time"'


class DateTime(Schema):
    def __str__(self):
        return '"datetime"'


class File(Schema):
    def __str__(self):
        return '"file"'


class URL(Schema):
    def __str__(self):
        return '"url"'


class Enum(Schema):
    def __init__(self, enum=[], **kwargs):
        super().__init__(**kwargs)
        self.enum = enum

    def __str__(self):
        return '"One of ({})"'.format(
            ', '.join(str(e) for e in self.enum)
        )


class Array(Schema):
    def __init__(self, items=None, **kwargs):
        super().__init__(**kwargs)
        self.items = items

    def __str__(self):
        return '[{}]'.format(str(self.items))


class Object(Schema):
    def __init__(self, properties=OrderedDict([]),
                 **kwargs):
        super().__init__(**kwargs)
        self.properties = properties

    def __str__(self):
        return '{{\n{}\n}}'.format(
            ',\n'.join(
                '"{}": {}'.format(key, str(value))
                for key, value in self.properties.items()
            )
        )

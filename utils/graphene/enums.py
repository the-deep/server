from django_enumfield import enum


def enum_description(v: enum.Enum) -> str:
    try:
        return v.label
    except AttributeError:
        return None

from django import template

register = template.Library()

@register.filter
def get_value_from_dict(dictionary, key):
    """Returns the value from the dictionary corresponding to the given key."""
    return dictionary.get(key, '')

from django import template

register = template.Library()

@register.filter
def get_item(list, key):
    """Return the value for a given key in a dictionary."""
    return list.get(key, '')  #


from django import template

register = template.Library()

@register.filter
def zipl(list1, list2):
    """Return zipped lists as a list of tuples."""
    return zip(list1, list2)

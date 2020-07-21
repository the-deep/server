from django import template

from mdmail.api import EmailContent


register = template.Library()


@register.filter(is_safe=True)
def markdown_render(value):
    if value:
        content = EmailContent(value)
        return content.html
    return '-'

"""Money formatting template filters."""

from django import template

register = template.Library()


@register.filter
def to_money(cents: int) -> str:
    if cents == 0:
        return "$0.00"

    digits = str(cents)
    cut = len(digits) - 2

    if cut < 0:
        msg = "index -3 out of string"
        raise IndexError(msg)

    return f"${digits[:cut]}.{digits[cut:]}"

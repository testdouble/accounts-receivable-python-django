"""The Django counterpart of the Rails source's `app/helpers/invoices_helper.rb`."""

from django import template

register = template.Library()


@register.filter
def to_money(cents: int) -> str:
    """Format whole cents as dollars, reproducing the Rails helper's flaws.

    The source is::

        def to_money(cents)
          return "$0.00" if cents == 0
          "$#{cents.to_s.insert(-3, ".")}"
        end

    `String#insert(-3, ".")` splices a dot in at `len - 2` and raises `IndexError` when
    the string is shorter than two characters, which produces:

    ======  ==================  ==================================
    cents   result              note
    ======  ==================  ==================================
    0       ``"$0.00"``         the one case the guard clause gets right
    5       ``IndexError``      any amount under ten cents crashes
    50      ``"$.50"``          no leading zero
    100     ``"$1.00"``
    100000  ``"$1000.00"``      no thousands separator
    -50     ``"$-.50"``
    -5      ``"$.-5"``          the minus sign lands after the dot
    ======  ==================  ==================================

    This is a **deliberately preserved defect**, not an oversight: the Rails app is an
    interview exercise whose git history includes a commit reverting correct money
    formatting back to this string surgery, and every port carries it. Fixing it here
    would quietly destroy the exercise. See CLAUDE.md, "Planted bugs are preserved".
    """
    if cents == 0:
        return "$0.00"

    digits = str(cents)
    # Where Ruby's insert(-3) lands. Negative means the string is a single character,
    # which is the index error.
    cut = len(digits) - 2

    if cut < 0:
        msg = "index -3 out of string"
        raise IndexError(msg)

    return f"${digits[:cut]}.{digits[cut:]}"

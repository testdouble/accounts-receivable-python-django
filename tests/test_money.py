"""The `to_money` filter, including the defect it deliberately preserves.

Every assertion here is a port of the Rails helper's real output, captured by running
`InvoicesHelper#to_money` against the source app. They pin a **known bug** in place --
see CLAUDE.md, "Planted bugs are preserved". If one of these fails because someone
corrected the formatter, the fix is the regression.
"""

import pytest

from accounts_receivable.templatetags.money import to_money


def test_zero_is_the_one_amount_the_guard_clause_gets_right() -> None:
    assert to_money(0) == "$0.00"


@pytest.mark.parametrize(
    ("cents", "expected"),
    [
        (100, "$1.00"),
        (2000, "$20.00"),
        (20000, "$200.00"),
        (4000, "$40.00"),
        (-2000, "$-20.00"),
    ],
)
def test_amounts_of_a_dollar_or_more_format_correctly(cents: int, expected: str) -> None:
    assert to_money(cents) == expected


def test_a_thousand_dollars_loses_its_separator() -> None:
    """Bug: the helper splices in a decimal point and never groups the thousands."""
    assert to_money(100000) == "$1000.00"


@pytest.mark.parametrize(("cents", "expected"), [(50, "$.50"), (99, "$.99")])
def test_sub_dollar_amounts_lose_their_leading_zero(cents: int, expected: str) -> None:
    """Bug: 50 cents prints as `$.50`, not `$0.50`."""
    assert to_money(cents) == expected


def test_a_negative_amount_puts_the_sign_in_the_wrong_place() -> None:
    """Bug: the minus sign is just another character to splice around."""
    assert to_money(-50) == "$-.50"
    assert to_money(-5) == "$.-5"


@pytest.mark.parametrize("cents", [1, 5, 9])
def test_amounts_under_ten_cents_raise(cents: int) -> None:
    """Bug: Ruby's `String#insert(-3, ".")` raises on a one-character string, so this does.

    A line item priced at a few cents therefore takes the invoice page down with a 500,
    exactly as it does in the Rails app.
    """
    with pytest.raises(IndexError):
        to_money(cents)

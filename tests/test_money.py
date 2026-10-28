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
    assert to_money(100000) == "$1000.00"


@pytest.mark.parametrize(("cents", "expected"), [(50, "$.50"), (99, "$.99")])
def test_sub_dollar_amounts_lose_their_leading_zero(cents: int, expected: str) -> None:
    assert to_money(cents) == expected


def test_a_negative_amount_puts_the_sign_in_the_wrong_place() -> None:
    assert to_money(-50) == "$-.50"
    assert to_money(-5) == "$.-5"


@pytest.mark.parametrize("cents", [1, 5, 9])
def test_amounts_under_ten_cents_raise(cents: int) -> None:
    with pytest.raises(IndexError):
        to_money(cents)

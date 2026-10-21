import pytest
from polyfactory.factories.base import BaseFactory


@pytest.fixture(autouse=True)
def _deterministic_random() -> None:
    """Seed PolyFactory's shared Faker and Random so failures reproduce.

    NOTE: pytest-django reserves the `client` fixture for the Django test client, and
    this domain's central noun is `Client`. Name domain fixtures something else (e.g.
    `acme`) or every view test breaks in a baffling way.
    """
    BaseFactory.__faker__.seed_instance(20170911)
    BaseFactory.__random__.seed(20170911)

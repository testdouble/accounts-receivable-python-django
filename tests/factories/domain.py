"""Factories for the domain models, ported from the Rails source app's spec/factories.

Built on the hand-written adapter in `tests/factories/base.py`, since PolyFactory ships
no DjangoModelFactory of its own.
"""

from polyfactory import Use
from polyfactory.factories.base import BaseFactory

from accounts_receivable.models import Client
from tests.factories.base import DjangoModelFactory

faker = BaseFactory.__faker__


class ClientFactory(DjangoModelFactory[Client]):
    __set_as_default_factory_for_type__ = True

    name = Use(faker.name)
    # The adapter maps EmailField -> str via the CharField MRO fallback, which would
    # generate a random string rather than an address. Declare it, exactly as the Rails
    # FactoryBot definition declared `Faker::Internet.email`.
    email = Use(faker.email)

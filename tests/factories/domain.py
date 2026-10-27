"""Factories for the domain models, ported from the Rails source app's spec/factories.

Built on the hand-written adapter in `tests/factories/base.py`, since PolyFactory ships
no DjangoModelFactory of its own.
"""

from polyfactory import Use
from polyfactory.factories.base import BaseFactory

from accounts_receivable.models import Client, Product, Service
from tests.factories.base import DjangoModelFactory

faker = BaseFactory.__faker__


class ClientFactory(DjangoModelFactory[Client]):
    __set_as_default_factory_for_type__ = True

    name = Use(faker.name)
    # The adapter maps EmailField -> str via the CharField MRO fallback, which would
    # generate a random string rather than an address. Declare it, exactly as the Rails
    # FactoryBot definition declared `Faker::Internet.email`.
    email = Use(faker.email)


class ProductFactory(DjangoModelFactory[Product]):
    __set_as_default_factory_for_type__ = True

    # Rails' FactoryBot definition uses `Faker::Hacker.adjective`; `faker.word` is the
    # nearest stock equivalent.
    name = Use(faker.word)
    # The adapter maps IntegerField -> int, which would generate an arbitrary (and
    # arbitrarily large) value. Bounded here to match the Rails factory's
    # `Faker::Number.number(digits: 4)`.
    price_cents = Use(lambda: BaseFactory.__random__.randint(1000, 9999))


class ServiceFactory(DjangoModelFactory[Service]):
    __set_as_default_factory_for_type__ = True

    # `Faker::Name.name` in the Rails factory, as odd as that reads for a service.
    name = Use(faker.name)
    price_cents = Use(lambda: BaseFactory.__random__.randint(1000, 9999))

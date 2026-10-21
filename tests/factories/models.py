"""Factories for the throwaway test models, demonstrating the Django adapter.

The real domain factories (clients, products, services, invoices, line items) follow
this shape in the domain pass.
"""

from polyfactory import Use
from polyfactory.factories.base import BaseFactory

from tests.factories.base import DjangoModelFactory
from tests.testapp.models import Author, Widget

faker = BaseFactory.__faker__


class AuthorFactory(DjangoModelFactory[Author]):
    __model__ = Author
    __set_as_default_factory_for_type__ = True

    name = Use(faker.name)
    # The adapter maps EmailField -> str via the CharField MRO fallback, which would
    # generate a random string rather than an address. Declare it, exactly as the Rails
    # FactoryBot definition declared `Faker::Internet.email`.
    email = Use(faker.email)


class WidgetFactory(DjangoModelFactory[Widget]):
    __model__ = Widget
    __set_as_default_factory_for_type__ = True

    # The FactoryBot "implicit association", made explicit. Persisted even under
    # .build() -- see the note in tests/factories/base.py.
    author = Use(AuthorFactory.create_sync)
    name = Use(faker.word)
    price_cents = Use(lambda: BaseFactory.__random__.randint(100, 999_900))
    quantity = Use(lambda: BaseFactory.__random__.randint(1, 40))
    note = Use(faker.sentence)

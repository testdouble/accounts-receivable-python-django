"""Factories for the domain models, ported from the Rails source app's spec/factories.

Built on the hand-written adapter in `tests/factories/base.py`, since PolyFactory ships
no DjangoModelFactory of its own.
"""

from polyfactory import Use
from polyfactory.factories.base import BaseFactory

from accounts_receivable.models import Client, Invoice, LineItem, Product, Service
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


class InvoiceFactory(DjangoModelFactory[Invoice]):
    __set_as_default_factory_for_type__ = True

    # FactoryBot's bare `client` association. Declared rather than left to
    # `__set_foreign_keys__`, which is off; see the note in tests/factories/base.py.
    client = Use(ClientFactory.create_sync)
    net_days = 30
    # The Rails factory has `Faker::Config.random`, which stringifies a Random object
    # into the note -- almost certainly a slip for a text generator. Not ported.
    note = Use(faker.sentence)


class LineItemFactory(DjangoModelFactory[LineItem]):
    """Builds a line item with **neither** a product nor a service.

    `product` and `service` are deliberately left undeclared. `__set_foreign_keys__` is
    False, so they come out None and the caller passes exactly one -- which is the XOR
    shape the adapter's docstring was written for, and the shape the Rails factory has
    (`spec/factories/line_item.rb` declares no associations at all).

    Note this bypasses `LineItem.clean()`: Django's `Model.save()` does not run it, so a
    bare `create_sync()` persists an invalid row. That mirrors FactoryBot's `build`
    followed by an explicit `save!` in the Rails specs, and it is why the
    product-or-service rule is tested through `LineItemForm`.
    """

    __set_as_default_factory_for_type__ = True

    invoice = Use(InvoiceFactory.create_sync)
    # `Faker::Number.within(range: 1..40)` in the Rails factory.
    quantity = Use(lambda: BaseFactory.__random__.randint(1, 40))
    # `Faker::Quote.yoda` there; `faker.sentence` is the nearest stock equivalent.
    description = Use(faker.sentence)
    price_override_cents = None

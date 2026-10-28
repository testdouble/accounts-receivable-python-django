"""Factories for the domain models.

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
    # generate a random string rather than an address, so declare it.
    email = Use(faker.email)


class ProductFactory(DjangoModelFactory[Product]):
    __set_as_default_factory_for_type__ = True

    name = Use(faker.word)
    # The adapter maps IntegerField -> int, which would generate an arbitrary (and
    # arbitrarily large) value, so bound it here.
    price_cents = Use(lambda: BaseFactory.__random__.randint(1000, 9999))


class ServiceFactory(DjangoModelFactory[Service]):
    __set_as_default_factory_for_type__ = True

    name = Use(faker.name)
    price_cents = Use(lambda: BaseFactory.__random__.randint(1000, 9999))


class InvoiceFactory(DjangoModelFactory[Invoice]):
    __set_as_default_factory_for_type__ = True

    # Declared rather than left to `__set_foreign_keys__`, which is off; see the note
    # in tests/factories/base.py.
    client = Use(ClientFactory.create_sync)
    net_days = 30
    note = Use(faker.sentence)


class LineItemFactory(DjangoModelFactory[LineItem]):
    """Builds a line item with **neither** a product nor a service.

    `product` and `service` are deliberately left undeclared. `__set_foreign_keys__` is
    False, so they come out None and the caller passes exactly one.

    Note this bypasses `LineItem.clean()`: Django's `Model.save()` does not run it, so a
    bare `create_sync()` persists an invalid row, which is why the product-or-service
    rule is tested through `LineItemForm`.
    """

    __set_as_default_factory_for_type__ = True

    invoice = Use(InvoiceFactory.create_sync)
    quantity = Use(lambda: BaseFactory.__random__.randint(1, 40))
    description = Use(faker.sentence)
    price_override_cents = None

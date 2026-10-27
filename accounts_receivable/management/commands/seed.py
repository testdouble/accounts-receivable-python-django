"""Development seed data, ported from the Rails source app's `db/seeds.rb`.

A management command rather than a fixture loaded with `loaddata`: fixtures pin primary
keys and overwrite rows on every load, while `get_or_create` is the direct counterpart of
the Rails seed's `find_or_create_by` and leaves existing rows alone.
"""

from django.core.management.base import BaseCommand
from django.db import models

from accounts_receivable.models import Client, Invoice, LineItem, Product, Service

# "Acme inc" / ap@acme.com is verbatim from the Rails seed; the second client follows the
# same `ap@` (accounts payable) convention.
CLIENTS = [
    ("Acme inc", {"email": "ap@acme.com"}),
    ("Dunder Mifflin", {"email": "ap@dundermifflin.com"}),
]

# Products and services are verbatim from the Rails seed, prices included: there it
# writes them as `200_00` and `1000_00`, i.e. dollars with an underscore before the cents.
PRODUCTS = [
    ("Anti-virus software", {"price_cents": 20000}),
    ("Serverless servers", {"price_cents": 100000}),
]

SERVICES = [
    ("Programming", {"price_cents": 8000}),
    ("Refactoring", {"price_cents": 35000}),
]

# The Rails seed bills both of these to Acme, the first client. Net 30 on both.
INVOICES = [
    "Invoice for writing software for Acme",
    "Invoice for refactoring software for Acme",
]

# (invoice note, product name, service name, defaults) -- verbatim from the Rails seed,
# including Justin's price override, which is the one row that exercises the override
# path on the invoice page.
LINE_ITEMS = [
    (
        INVOICES[0],
        None,
        "Programming",
        {"quantity": 40, "description": "Amber's quality programming"},
    ),
    (
        INVOICES[0],
        None,
        "Programming",
        {
            "price_override_cents": 4000,
            "quantity": 40,
            "description": "Justin's discount programming",
        },
    ),
    (
        INVOICES[0],
        "Serverless servers",
        None,
        {
            "quantity": 20,
            "description": "Enough serverless hardware to achieve web-scale",
        },
    ),
    (
        INVOICES[1],
        None,
        "Refactoring",
        {
            "quantity": 40,
            "description": "Megan fixing previous discount programming",
        },
    ),
    (
        INVOICES[1],
        "Anti-virus software",
        None,
        {"quantity": 1, "description": "Anti-virus software subscription"},
    ),
]


class Command(BaseCommand):
    help = "Load development seed data. Safe to re-run."

    def handle(self, *args: object, **options: object) -> None:
        self._load(Client, "client", CLIENTS)
        self._load(Product, "product", PRODUCTS)
        self._load(Service, "service", SERVICES)
        self._load_invoices()
        self._load_line_items()

    def _load(
        self,
        model: type[models.Model],
        label: str,
        rows: list[tuple[str, dict[str, object]]],
    ) -> None:
        for name, defaults in rows:
            # Keyed on name alone, with everything else in `defaults`, so correcting an
            # address or a price later does not seed a duplicate row. The Rails seed keys
            # `find_or_create_by` on the price too, which would.
            _, created = model.objects.get_or_create(name=name, defaults=defaults)

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {label} {name}"))
            else:
                self.stdout.write(f"{label.capitalize()} {name} already exists")

    def _load_invoices(self) -> None:
        """The two Acme invoices. Keyed on client and note, which are unique in the seed.

        Invoices and line items have no `name`, so `_load` above does not fit them.
        """
        acme = Client.objects.get(name=CLIENTS[0][0])

        for note in INVOICES:
            _, created = Invoice.objects.get_or_create(
                client=acme, note=note, defaults={"net_days": 30}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created invoice {note}"))
            else:
                self.stdout.write(f"Invoice {note} already exists")

    def _load_line_items(self) -> None:
        """Acme's five line items. Keyed on invoice and description, which is unique."""
        for note, product_name, service_name, defaults in LINE_ITEMS:
            invoice = Invoice.objects.get(note=note)
            # Exactly one of these is set, as `LineItem.clean()` requires. The command
            # writes through the ORM, which does not run `clean()`, so the seed data
            # itself has to hold the rule up.
            catalog = {
                "product": Product.objects.get(name=product_name) if product_name else None,
                "service": Service.objects.get(name=service_name) if service_name else None,
            }
            fields = {**defaults, **catalog}
            description = fields.pop("description")
            _, created = LineItem.objects.get_or_create(
                invoice=invoice,
                description=description,
                defaults=fields,
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created line item {description}"))
            else:
                self.stdout.write(f"Line item {description} already exists")

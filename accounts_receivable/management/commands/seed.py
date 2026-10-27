"""Development seed data, ported from the Rails source app's `db/seeds.rb`.

A management command rather than a fixture loaded with `loaddata`: fixtures pin primary
keys and overwrite rows on every load, while `get_or_create` is the direct counterpart of
the Rails seed's `find_or_create_by` and leaves existing rows alone.
"""

from django.core.management.base import BaseCommand
from django.db import models

from accounts_receivable.models import Client, Product, Service

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


class Command(BaseCommand):
    help = "Load development seed data. Safe to re-run."

    def handle(self, *args: object, **options: object) -> None:
        self._load(Client, "client", CLIENTS)
        self._load(Product, "product", PRODUCTS)
        self._load(Service, "service", SERVICES)

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

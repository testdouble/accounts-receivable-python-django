"""Development seed data, ported from the Rails source app's `db/seeds.rb`.

A management command rather than a fixture loaded with `loaddata`: fixtures pin primary
keys and overwrite rows on every load, while `get_or_create` is the direct counterpart of
the Rails seed's `find_or_create_by` and leaves existing rows alone.
"""

from django.core.management.base import BaseCommand

from accounts_receivable.models import Client

# "Acme inc" / ap@acme.com is verbatim from the Rails seed; the second client follows the
# same `ap@` (accounts payable) convention.
CLIENTS = [
    ("Acme inc", "ap@acme.com"),
    ("Dunder Mifflin", "ap@dundermifflin.com"),
]


class Command(BaseCommand):
    help = "Load development seed data. Safe to re-run."

    def handle(self, *args: object, **options: object) -> None:
        for name, email in CLIENTS:
            # Keyed on name alone, with the email in `defaults`, so correcting an address
            # later does not seed a duplicate client.
            _, created = Client.objects.get_or_create(name=name, defaults={"email": email})

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created client {name}"))
            else:
                self.stdout.write(f"Client {name} already exists")

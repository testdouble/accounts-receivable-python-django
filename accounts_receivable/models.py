"""Domain models ported from the Rails source app.

The remaining four tables (products, services, invoices, line_items) land in a later
pass; this one covers `clients`.
"""

from django.db import models


class Client(models.Model):
    """A customer who receives invoices.

    The Rails source declares `name` and `email` as `string, null: false` with no length
    cap -- SQLite ignores varchar limits. Django requires `max_length`, so the caps below
    are a port artifact rather than a domain rule.
    """

    name = models.CharField(max_length=120)
    email = models.EmailField(max_length=254)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name

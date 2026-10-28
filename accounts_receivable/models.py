"""Domain models: clients, products, services, invoices and line items."""

import datetime as dt

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class Client(models.Model):
    """A customer who receives invoices."""

    name = models.CharField(max_length=120)
    email = models.EmailField(max_length=254)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        """Where create and update land."""
        return reverse("client_detail", kwargs={"pk": self.pk})


class Product(models.Model):
    """Something sold by the unit, which a line item can reference."""

    name = models.CharField(max_length=120)
    price_cents = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        """Where create and update land."""
        return reverse("product_detail", kwargs={"pk": self.pk})


class Service(models.Model):
    """Work that is billed for, which a line item can reference."""

    name = models.CharField(max_length=120)
    price_cents = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        """Where create and update land."""
        return reverse("service_detail", kwargs={"pk": self.pk})


class Invoice(models.Model):
    """A bill addressed to one client, totalled from its line items.

    There is no subject or issue-date column -- the show page prints the note as the
    invoice's subject line, and `created_at` is the issue date that the due date is
    measured from.
    """

    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="invoices")
    net_days = models.IntegerField(default=30)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"Invoice #{self.pk}"

    def get_absolute_url(self) -> str:
        """Where create and update land."""
        return reverse("invoice_detail", kwargs={"pk": self.pk})

    @property
    def due_date(self) -> dt.date | None:
        """The creation date plus `net_days`.

        Derived from the stored `created_at` rather than from the clock, so it does not
        move between requests. None before the row is saved, since `auto_now_add` has
        not run yet.
        """
        if self.created_at is None:
            return None

        return self.created_at.date() + dt.timedelta(days=self.net_days)

    @property
    def total_cents(self) -> int:
        """Every line item's subtotal, summed."""
        return sum(item.subtotal_cents or 0 for item in self.line_items.all())


class LineItem(models.Model):
    """One billable row on an invoice, priced from a product or a service.

    Exactly one of `product` and `service` is set; see `clean()`.
    """

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="line_items")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, null=True, blank=True, related_name="line_items"
    )
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT, null=True, blank=True, related_name="line_items"
    )
    # NULL means "no override, use the catalog price". It is not the same as an override
    # of 0, which is a free line -- see `unit_price_cents`.
    price_override_cents = models.IntegerField(null=True, blank=True)
    quantity = models.IntegerField(default=1)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.description or f"Line item #{self.pk}"

    def get_absolute_url(self) -> str:
        return reverse("line_item_detail", kwargs={"pk": self.pk})

    def clean(self) -> None:
        if self.product_id is None and self.service_id is None:
            raise ValidationError("A line item must be either a product or a service")

        if self.product_id is not None and self.service_id is not None:
            raise ValidationError("A line item can't be both a product and a service")

    @property
    def unit_price_cents(self) -> int | None:
        if self.price_override_cents is not None:
            return self.price_override_cents

        catalog = self.product or self.service

        return catalog.price_cents if catalog else None

    @property
    def subtotal_cents(self) -> int | None:
        unit_price = self.unit_price_cents

        return None if unit_price is None else unit_price * self.quantity

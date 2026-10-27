"""Views for the domain models.

Plain Django class-based views: the Rails source is scaffold-generated CRUD, and the
generic views are the closest Django equivalent of `resources :clients`.
"""

from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    RedirectView,
    UpdateView,
)

from accounts_receivable.forms import (
    ClientForm,
    InvoiceForm,
    LineItemForm,
    ProductForm,
    ServiceForm,
)
from accounts_receivable.models import Client, Invoice, LineItem, Product, Service


class RootRedirectView(RedirectView):
    """Send `/` to the invoices index, as the Rails `root to: redirect("/invoices")` does."""

    pattern_name = "invoice_list"
    permanent = False


class ClientListView(ListView):
    model = Client
    context_object_name = "clients"
    template_name = "accounts_receivable/clients/index.html"


class ClientDetailView(DetailView):
    model = Client
    # `client` is reserved for the Django test client in tests, and `object` reads as
    # nothing at all in a template, so the record gets an explicit name.
    context_object_name = "record"
    template_name = "accounts_receivable/clients/show.html"


class ClientCreateView(SuccessMessageMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "accounts_receivable/clients/form.html"
    success_message = "Client created."
    extra_context = {
        "heading": "New client",
        "subheading": "Add a client. Companies you bill. Every invoice is addressed to one client.",
        "submit_label": "Create client",
        "crumb": "new",
    }


class ClientUpdateView(SuccessMessageMixin, UpdateView):
    model = Client
    form_class = ClientForm
    context_object_name = "record"
    template_name = "accounts_receivable/clients/form.html"
    success_message = "Client updated."
    extra_context = {
        "heading": "Edit client",
        "subheading": "Update this client's billing details.",
        "submit_label": "Save client",
    }


class ClientDeleteView(SuccessMessageMixin, DeleteView):
    model = Client
    context_object_name = "record"
    template_name = "accounts_receivable/clients/confirm_delete.html"
    success_message = "Client deleted."
    success_url = reverse_lazy("client_list")


class ProductListView(ListView):
    model = Product
    context_object_name = "products"
    template_name = "accounts_receivable/products/index.html"


class ProductDetailView(DetailView):
    model = Product
    context_object_name = "record"
    template_name = "accounts_receivable/products/show.html"


class ProductCreateView(SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "accounts_receivable/products/form.html"
    success_message = "Product created."
    extra_context = {
        "heading": "New product",
        "subheading": "Add something you sell by the unit.",
        "submit_label": "Create product",
    }


class ProductUpdateView(SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    context_object_name = "record"
    template_name = "accounts_receivable/products/form.html"
    success_message = "Product updated."
    extra_context = {
        "heading": "Edit product",
        "subheading": "Update this product's name or price.",
        "submit_label": "Save product",
    }


class ProductDeleteView(SuccessMessageMixin, DeleteView):
    model = Product
    context_object_name = "record"
    template_name = "accounts_receivable/products/confirm_delete.html"
    success_message = "Product deleted."
    success_url = reverse_lazy("product_list")


class ServiceListView(ListView):
    model = Service
    context_object_name = "services"
    template_name = "accounts_receivable/services/index.html"


class ServiceDetailView(DetailView):
    model = Service
    context_object_name = "record"
    template_name = "accounts_receivable/services/show.html"


class ServiceCreateView(SuccessMessageMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = "accounts_receivable/services/form.html"
    success_message = "Service created."
    extra_context = {
        "heading": "New service",
        "subheading": "Add work you bill for.",
        "submit_label": "Create service",
    }


class ServiceUpdateView(SuccessMessageMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    context_object_name = "record"
    template_name = "accounts_receivable/services/form.html"
    success_message = "Service updated."
    extra_context = {
        "heading": "Edit service",
        "subheading": "Update this service's name or price.",
        "submit_label": "Save service",
    }


class ServiceDeleteView(SuccessMessageMixin, DeleteView):
    model = Service
    context_object_name = "record"
    template_name = "accounts_receivable/services/confirm_delete.html"
    success_message = "Service deleted."
    success_url = reverse_lazy("service_list")


class InvoiceListView(ListView):
    model = Invoice
    context_object_name = "invoices"
    template_name = "accounts_receivable/invoices/index.html"
    # The index prints `record.client.name`; without this it is a query per row.
    queryset = Invoice.objects.select_related("client")


class InvoiceDetailView(DetailView):
    model = Invoice
    context_object_name = "record"
    template_name = "accounts_receivable/invoices/show.html"
    queryset = Invoice.objects.select_related("client")

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        """Split the line items into products and services, and total them.

        A port of `InvoicesController#show`, including its defect. Rails builds the table
        from::

            line_items.joins(:product).where("products.price_cents != 0") +
            line_items.joins(:service).where("services.price_cents != 0")

        `filter(product__isnull=False)` is the inner join `joins(:product)` performs, and
        `exclude(product__price_cents=0)` is the `!= 0` clause. That clause is a
        **deliberately preserved defect**: a line item priced from a zero-cost product or
        service silently vanishes from the table and from the total, even when it carries
        a price override that should bill for it. See CLAUDE.md, "Planted bugs are
        preserved", and do not quietly drop the `exclude`.
        """
        context = super().get_context_data(**kwargs)
        items = self.object.line_items.select_related("product", "service")
        products = list(items.filter(product__isnull=False).exclude(product__price_cents=0))
        services = list(items.filter(service__isnull=False).exclude(service__price_cents=0))

        context["product_items"] = products
        context["service_items"] = services
        # `subtotal_cents` is never None here: every row in these two lists has either a
        # product or a service by construction.
        context["total_cents"] = sum(item.subtotal_cents for item in products + services)

        return context


class InvoiceCreateView(SuccessMessageMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "accounts_receivable/invoices/form.html"
    success_message = "Invoice created."
    extra_context = {
        "heading": "New invoice",
        "subheading": "Bill a client. Add line items once the invoice exists.",
        "submit_label": "Create invoice",
    }


class InvoiceUpdateView(SuccessMessageMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    context_object_name = "record"
    template_name = "accounts_receivable/invoices/form.html"
    success_message = "Invoice updated."
    extra_context = {
        "heading": "Edit invoice",
        "subheading": "Change who this invoice bills, its payment window, or its subject.",
        "submit_label": "Save invoice",
    }


class InvoiceDeleteView(SuccessMessageMixin, DeleteView):
    model = Invoice
    context_object_name = "record"
    template_name = "accounts_receivable/invoices/confirm_delete.html"
    success_message = "Invoice deleted."
    success_url = reverse_lazy("invoice_list")


class LineItemListView(ListView):
    model = LineItem
    context_object_name = "line_items"
    template_name = "accounts_receivable/line_items/index.html"
    queryset = LineItem.objects.select_related("invoice", "product", "service")


class LineItemDetailView(DetailView):
    model = LineItem
    context_object_name = "record"
    template_name = "accounts_receivable/line_items/show.html"
    queryset = LineItem.objects.select_related("invoice", "product", "service")


class LineItemCreateView(SuccessMessageMixin, CreateView):
    model = LineItem
    form_class = LineItemForm
    template_name = "accounts_receivable/line_items/form.html"
    success_message = "Line item created."
    extra_context = {
        "heading": "New line item",
        "subheading": "Add a billable row to an invoice, priced from a product or a service.",
        "submit_label": "Create line item",
    }


class LineItemUpdateView(SuccessMessageMixin, UpdateView):
    model = LineItem
    form_class = LineItemForm
    context_object_name = "record"
    template_name = "accounts_receivable/line_items/form.html"
    success_message = "Line item updated."
    extra_context = {
        "heading": "Edit line item",
        "subheading": "Change what this row bills for, how many, or at what price.",
        "submit_label": "Save line item",
    }


class LineItemDeleteView(SuccessMessageMixin, DeleteView):
    model = LineItem
    context_object_name = "record"
    template_name = "accounts_receivable/line_items/confirm_delete.html"
    success_message = "Line item deleted."
    success_url = reverse_lazy("line_item_list")

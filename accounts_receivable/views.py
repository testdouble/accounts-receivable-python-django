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

from accounts_receivable.forms import ClientForm
from accounts_receivable.models import Client


class RootRedirectView(RedirectView):
    """Send `/` to the clients index.

    The Rails source does `root to: redirect("/invoices")`. Invoices do not exist yet,
    so clients is the only index there is; point this at invoices once they land.
    """

    pattern_name = "client_list"
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

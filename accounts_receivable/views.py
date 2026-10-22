from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Placeholder landing page proving the template layer renders.

    The domain pass replaces this with a redirect to the invoice index, matching the
    Rails source app's `root to: redirect("/invoices")`.
    """

    template_name = "accounts_receivable/home.html"

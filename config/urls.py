from django.urls import include, path

from accounts_receivable.api import api

urlpatterns = [
    path("api/", api.urls),
    path("", include("accounts_receivable.urls")),
]

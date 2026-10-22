from django.urls import path

from accounts_receivable.views import HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
]

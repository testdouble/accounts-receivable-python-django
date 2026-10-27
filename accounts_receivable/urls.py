from django.urls import path

from accounts_receivable.views import (
    ClientCreateView,
    ClientDeleteView,
    ClientDetailView,
    ClientListView,
    ClientUpdateView,
    ProductCreateView,
    ProductDeleteView,
    ProductDetailView,
    ProductListView,
    ProductUpdateView,
    RootRedirectView,
    ServiceCreateView,
    ServiceDeleteView,
    ServiceDetailView,
    ServiceListView,
    ServiceUpdateView,
)

urlpatterns = [
    path("", RootRedirectView.as_view(), name="home"),
    path("clients/", ClientListView.as_view(), name="client_list"),
    path("clients/new/", ClientCreateView.as_view(), name="client_create"),
    path("clients/<int:pk>/", ClientDetailView.as_view(), name="client_detail"),
    path("clients/<int:pk>/edit/", ClientUpdateView.as_view(), name="client_update"),
    path("clients/<int:pk>/delete/", ClientDeleteView.as_view(), name="client_delete"),
    path("products/", ProductListView.as_view(), name="product_list"),
    path("products/new/", ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
    path("products/<int:pk>/edit/", ProductUpdateView.as_view(), name="product_update"),
    path("products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product_delete"),
    path("services/", ServiceListView.as_view(), name="service_list"),
    path("services/new/", ServiceCreateView.as_view(), name="service_create"),
    path("services/<int:pk>/", ServiceDetailView.as_view(), name="service_detail"),
    path("services/<int:pk>/edit/", ServiceUpdateView.as_view(), name="service_update"),
    path("services/<int:pk>/delete/", ServiceDeleteView.as_view(), name="service_delete"),
]

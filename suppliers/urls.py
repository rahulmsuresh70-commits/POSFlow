from django.urls import path

from . import views


urlpatterns = [
    path("", views.supplier_list, name="supplier_list"),

    path(
        "add/",
        views.supplier_create,
        name="supplier_create",
    ),

    path(
        "<int:supplier_id>/edit/",
        views.supplier_edit,
        name="supplier_edit",
    ),

    path(
        "<int:supplier_id>/delete/",
        views.supplier_delete,
        name="supplier_delete",
    ),

    path(
        "<int:supplier_id>/toggle/",
        views.supplier_toggle_status,
        name="supplier_toggle_status",
    ),
]
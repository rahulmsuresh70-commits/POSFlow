from django.urls import path

from . import views


urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("staff/", views.staff_list, name="staff_list"),
    path("staff/add/", views.staff_create, name="staff_create"),
    path("staff/<int:staff_id>/edit/", views.staff_edit, name="staff_edit"),
    path(
        "staff/<int:staff_id>/toggle/",
        views.staff_toggle_status,
        name="staff_toggle_status",
    ),
]
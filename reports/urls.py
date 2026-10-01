from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.reports_page,
        name="reports_page"
    ),
]
from django.urls import path
from . import views


urlpatterns = [

  
    path(
        "",
        views.billing_page,
        name="billing"
    ),

 
    path(
        "add/<int:product_id>/",
        views.add_to_cart,
        name="add_to_cart"
    ),

    path(
        "remove/<int:product_id>/",
        views.remove_from_cart,
        name="remove_from_cart"
    ),

   
    path(
        "checkout/",
        views.checkout,
        name="checkout"
    ),

    path(
        "transactions/",
        views.transaction_list,
        name="transaction_list"
    ),
    path("returns/", views.returns_page, name="returns_page"),
    path("returns/process/", views.process_return, name="process_return"),
    path(
        "ledger/",
        views.ledger_page,
        name="ledger_page"
    ),
]
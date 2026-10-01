from django.contrib import admin
from .models import Sale, SaleItem, ProductReturn


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "staff",
        "total",
        "payment_method",
        "created_at",
    )
    search_fields = ("invoice_number",)
    list_filter = ("payment_method", "created_at")
    inlines = [SaleItemInline]


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = (
        "sale",
        "product",
        "quantity",
        "price",
        "total",
    )


@admin.register(ProductReturn)
class ProductReturnAdmin(admin.ModelAdmin):
    list_display = (
        "sale_item",
        "quantity",
        "refund_amount",
        "processed_by",
        "created_at",
    )
    search_fields = ("sale_item__sale__invoice_number",)
    list_filter = ("created_at",)
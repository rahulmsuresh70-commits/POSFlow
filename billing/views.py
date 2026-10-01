from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Sum

from products.models import Product
from accounts.models import StaffProfile
from .models import Sale, SaleItem, ProductReturn,Product





@login_required
def ledger_page(request):

    ledger_date = request.GET.get(
        "date",
        ""
    ).strip()

    sales = Sale.objects.select_related(
        "staff"
    ).order_by("-created_at")

    returns = ProductReturn.objects.select_related(
        "sale_item__sale",
        "sale_item__product",
        "processed_by",
    ).order_by("-created_at")

    from reports.models import Expense

    expenses = Expense.objects.order_by(
        "-date"
    )


    if ledger_date:

        sales = sales.filter(
            created_at__date=ledger_date
        )

        returns = returns.filter(
            created_at__date=ledger_date
        )

        expenses = expenses.filter(
            date=ledger_date
        )

   
    total_sales = (
        sales.aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )



    total_refunds = (
        returns.aggregate(
            total=Sum("refund_amount")
        )["total"]
        or Decimal("0.00")
    )



    total_expenses = (
        expenses.aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

  

    net_amount = (
        total_sales
        - total_refunds
        - total_expenses
    )

    context = {
        "sales": sales,
        "returns": returns,
        "expenses": expenses,

        "total_sales": total_sales,
        "total_refunds": total_refunds,
        "total_expenses": total_expenses,
        "net_amount": net_amount,

        "ledger_date": ledger_date,
    }

    return render(
        request,
        "billing/ledger.html",
        context
    )




@login_required
def returns_page(request):

    invoice_number = request.GET.get(
        "invoice",
        ""
    ).strip()

    sale = None
    error = ""

    if invoice_number:

        try:
            sale = (
                Sale.objects
                .select_related("staff")
                .prefetch_related("items__product")
                .get(invoice_number__iexact=invoice_number)
            )

        except Sale.DoesNotExist:
            error = "Invoice not found."

    returns = (
        ProductReturn.objects
        .select_related(
            "sale_item__sale",
            "sale_item__product",
            "processed_by",
        )
        .order_by("-created_at")
    )

    context = {
        "sale": sale,
        "invoice_number": invoice_number,
        "error": error,
        "returns": returns,
    }

    return render(
        request,
        "billing/returns.html",
        context
    )


@login_required
def process_return(request):

    if request.method != "POST":
        return redirect("returns_page")

    sale_item_id = request.POST.get(
        "sale_item_id"
    )

    quantity = request.POST.get(
        "quantity"
    )

    reason = request.POST.get(
        "reason",
        ""
    ).strip()

    if not sale_item_id or not quantity:
        return redirect("returns_page")

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return redirect("returns_page")

    if quantity <= 0:
        return redirect("returns_page")

    sale_item = get_object_or_404(
        SaleItem.objects.select_related(
            "sale",
            "product",
        ),
        id=sale_item_id
    )


    already_returned = (
        ProductReturn.objects
        .filter(sale_item=sale_item)
        .aggregate(
            total=Sum("quantity")
        )["total"]
        or 0
    )

    remaining_quantity = (
        sale_item.quantity - already_returned
    )

    if quantity > remaining_quantity:
        return redirect(
            f"/billing/returns/?invoice={sale_item.sale.invoice_number}"
        )

 

    refund_amount = (
        sale_item.price * quantity
    )

 

    ProductReturn.objects.create(
        sale_item=sale_item,
        quantity=quantity,
        reason=reason,
        refund_amount=refund_amount,
        processed_by=request.user,
    )


    product = sale_item.product

    product.stock_quantity += quantity

    product.save(
        update_fields=["stock_quantity"]
    )

    return redirect(
        f"/billing/returns/?invoice={sale_item.sale.invoice_number}"
    )


@login_required
def billing_page(request):
    products = Product.objects.filter(
        is_active=True,
        stock_quantity__gt=0
    )

    cart = request.session.get("cart", {})

    cart_items = []
    subtotal = Decimal("0.00")

    for product_id, quantity in cart.items():

        product = get_object_or_404(
            Product,
            id=product_id
        )

        quantity = int(quantity)

        item_total = product.selling_price * quantity

        subtotal += item_total

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "total": item_total,
        })

    return render(
        request,
        "billing/billing.html",
        {
            "products": products,
            "cart_items": cart_items,
            "subtotal": subtotal,
        }
    )




@login_required
def add_to_cart(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    cart = request.session.get("cart", {})

    product_id = str(product.id)

    current_quantity = int(
        cart.get(product_id, 0)
    )

    if current_quantity < product.stock_quantity:

        cart[product_id] = current_quantity + 1

    request.session["cart"] = cart

    return redirect("billing")




@login_required
def remove_from_cart(request, product_id):

    cart = request.session.get("cart", {})

    product_id = str(product_id)

    if product_id in cart:

        del cart[product_id]

    request.session["cart"] = cart

    return redirect("billing")



@login_required
def checkout(request):

    if request.method != "POST":

        return redirect("billing")

    cart = request.session.get("cart", {})

    if not cart:

        return redirect("billing")

    sale = Sale.objects.create(
        invoice_number=f"INV-{Sale.objects.count() + 1:05d}",
        staff=request.user,
        payment_method=request.POST.get(
            "payment_method",
            "cash"
        ),
    )

    subtotal = Decimal("0.00")

    for product_id, quantity in cart.items():

        product = get_object_or_404(
            Product,
            id=product_id
        )

        quantity = int(quantity)

        if quantity > product.stock_quantity:

            continue

        item_total = (
            product.selling_price * quantity
        )

        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=quantity,
            price=product.selling_price,
            total=item_total,
        )

        product.stock_quantity -= quantity

        product.save(
            update_fields=["stock_quantity"]
        )

        subtotal += item_total

    sale.subtotal = subtotal
    sale.total = subtotal

    sale.save()

    request.session["cart"] = {}

    return render(
        request,
        "billing/invoice.html",
        {
            "sale": sale
        }
    )




@login_required
def admin_dashboard(request):

    # Only superusers can access Admin Dashboard
    if not request.user.is_superuser:

        return redirect("billing")

    today = timezone.localdate()


    today_sales = (
        Sale.objects
        .filter(
            created_at__date=today
        )
        .aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )



    total_products = Product.objects.count()

  

    low_stock = Product.objects.filter(
        is_active=True,
        stock_quantity__lte=5
    ).count()

 
    staff_count = StaffProfile.objects.filter(
        role="staff"
    ).count()


    returns_count = ProductReturn.objects.count()


    total_revenue = (
        Sale.objects
        .aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )


    recent_transactions = (
        Sale.objects
        .select_related("staff")
        .order_by("-created_at")[:5]
    )

    context = {
        "today_sales": today_sales,
        "total_products": total_products,
        "low_stock": low_stock,
        "staff_count": staff_count,
        "returns_count": returns_count,
        "total_revenue": total_revenue,
        "recent_transactions": recent_transactions,
        "today": today,
    }

    return render(
        request,
        "admin/dashboard.html",
        context
    )


@login_required
def transaction_list(request):

    transactions = (
        Sale.objects
        .select_related("staff")
        .prefetch_related("items__product")
        .order_by("-created_at")
    )


    search = request.GET.get("search", "").strip()

    if search:
        transactions = transactions.filter(
            invoice_number__icontains=search
        )



    payment_method = request.GET.get(
        "payment_method",
        ""
    ).strip()

    if payment_method:
        transactions = transactions.filter(
            payment_method=payment_method
        )


    transaction_date = request.GET.get(
        "date",
        ""
    ).strip()

    if transaction_date:
        transactions = transactions.filter(
            created_at__date=transaction_date
        )

  

    context = {
        "transactions": transactions,
        "search": search,
        "payment_method": payment_method,
        "transaction_date": transaction_date,
    }

    return render(
        request,
        "billing/transactions.html",
        context
    )
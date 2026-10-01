from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.shortcuts import render

from billing.models import Sale, ProductReturn
from reports.models import Expense


@login_required
def reports_page(request):

    report_date = request.GET.get(
        "date",
        ""
    ).strip()

    sales = Sale.objects.select_related(
        "staff"
    ).order_by("-created_at")

    returns = ProductReturn.objects.select_related(
        "sale_item__product",
        "sale_item__sale",
        "processed_by",
    ).order_by("-created_at")

    expenses = Expense.objects.order_by("-date")



    if report_date:

        sales = sales.filter(
            created_at__date=report_date
        )

        returns = returns.filter(
            created_at__date=report_date
        )

        expenses = expenses.filter(
            date=report_date
        )



    total_revenue = (
        sales.aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    total_transactions = sales.count()


    total_returns = returns.aggregate(
        total=Sum("quantity")
    )["total"] or 0

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
        total_revenue
        - total_refunds
        - total_expenses
    )

   

    cash_sales = (
        sales.filter(
            payment_method="cash"
        ).aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    card_sales = (
        sales.filter(
            payment_method="card"
        ).aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

    upi_sales = (
        sales.filter(
            payment_method="upi"
        ).aggregate(
            total=Sum("total")
        )["total"]
        or Decimal("0.00")
    )

   
    recent_sales = sales[:10]

    context = {
        "report_date": report_date,

        "total_revenue": total_revenue,
        "total_transactions": total_transactions,

        "total_returns": total_returns,
        "total_refunds": total_refunds,

        "total_expenses": total_expenses,
        "net_amount": net_amount,

        "cash_sales": cash_sales,
        "card_sales": card_sales,
        "upi_sales": upi_sales,

        "recent_sales": recent_sales,
    }

    return render(
        request,
        "reports/reports.html",
        context
    )
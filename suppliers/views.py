from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Supplier


def admin_only(request):
    return request.user.is_superuser


@login_required
def supplier_list(request):
    if not admin_only(request):
        return redirect("billing")

    suppliers = Supplier.objects.all().order_by("-created_at")

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        suppliers = suppliers.filter(
            name__icontains=search
        ) | Supplier.objects.filter(
            phone__icontains=search
        ) | Supplier.objects.filter(
            email__icontains=search
        )

    if status == "active":
        suppliers = suppliers.filter(is_active=True)
    elif status == "inactive":
        suppliers = suppliers.filter(is_active=False)

    return render(
        request,
        "admin/suppliers/list.html",
        {
            "suppliers": suppliers,
            "search": search,
            "selected_status": status,
        },
    )


@login_required
def supplier_create(request):
    if not admin_only(request):
        return redirect("billing")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
        is_active = request.POST.get("is_active") == "on"

        if not name or not phone:
            messages.error(
                request,
                "Supplier name and phone are required.",
            )
            return render(
                request,
                "admin/suppliers/form.html",
                {"supplier": None},
            )

        supplier = Supplier.objects.create(
            name=name,
            phone=phone,
            email=email,
            address=address,
            is_active=is_active,
        )

        messages.success(
            request,
            f"Supplier '{supplier.name}' added successfully.",
        )

        return redirect("supplier_list")

    return render(
        request,
        "admin/suppliers/form.html",
        {"supplier": None},
    )


@login_required
def supplier_edit(request, supplier_id):
    if not admin_only(request):
        return redirect("billing")

    supplier = get_object_or_404(
        Supplier,
        id=supplier_id,
    )

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
        is_active = request.POST.get("is_active") == "on"

        if not name or not phone:
            messages.error(
                request,
                "Supplier name and phone are required.",
            )

            return render(
                request,
                "admin/suppliers/form.html",
                {"supplier": supplier},
            )

        supplier.name = name
        supplier.phone = phone
        supplier.email = email
        supplier.address = address
        supplier.is_active = is_active
        supplier.save()

        messages.success(
            request,
            f"Supplier '{supplier.name}' updated successfully.",
        )

        return redirect("supplier_list")

    return render(
        request,
        "admin/suppliers/form.html",
        {"supplier": supplier},
    )


@login_required
def supplier_delete(request, supplier_id):
    if not admin_only(request):
        return redirect("billing")

    supplier = get_object_or_404(
        Supplier,
        id=supplier_id,
    )

    if request.method == "POST":
        name = supplier.name
        supplier.delete()

        messages.success(
            request,
            f"Supplier '{name}' deleted successfully.",
        )

    return redirect("supplier_list")


@login_required
def supplier_toggle_status(request, supplier_id):
    if not admin_only(request):
        return redirect("billing")

    if request.method != "POST":
        return redirect("supplier_list")

    supplier = get_object_or_404(
        Supplier,
        id=supplier_id,
    )

    supplier.is_active = not supplier.is_active
    supplier.save(update_fields=["is_active"])

    status_text = (
        "activated"
        if supplier.is_active
        else "deactivated"
    )

    messages.success(
        request,
        f"Supplier '{supplier.name}' {status_text} successfully.",
    )

    return redirect("supplier_list")
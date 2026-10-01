from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from .models import Product, Category, ProductImage


def admin_only(request):
    return request.user.is_superuser


@login_required
def product_list(request):
    if not admin_only(request):
        return redirect("billing")

    products = (
        Product.objects
        .select_related("category")
        .prefetch_related("images")
        .all()
        .order_by("-created_at")
    )

    search = request.GET.get("search", "").strip()
    category_id = request.GET.get("category", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(sku__icontains=search)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if status == "active":
        products = products.filter(is_active=True)
    elif status == "inactive":
        products = products.filter(is_active=False)
    elif status == "low_stock":
        products = products.filter(is_active=True, stock_quantity__lte=5)

    categories = Category.objects.filter(is_active=True).order_by("name")

    return render(
        request,
        "admin/products/list.html",
        {
            "products": products,
            "categories": categories,
            "search": search,
            "selected_category": category_id,
            "selected_status": status,
        },
    )


@login_required
def product_create(request):
    if not admin_only(request):
        return redirect("billing")

    categories = Category.objects.filter(is_active=True).order_by("name")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        sku = request.POST.get("sku", "").strip()
        category_id = request.POST.get("category")
        purchase_price = request.POST.get("purchase_price", "0")
        selling_price = request.POST.get("selling_price", "0")
        stock_quantity = request.POST.get("stock_quantity", "0")
        is_active = request.POST.get("is_active") == "on"

        if not all([name, sku, category_id]):
            messages.error(request, "Please fill all required fields.")
            return render(
                request,
                "admin/products/form.html",
                {"categories": categories, "product": None},
            )

        if Product.objects.filter(sku=sku).exists():
            messages.error(request, "SKU already exists.")
            return render(
                request,
                "admin/products/form.html",
                {"categories": categories, "product": None},
            )

        product = Product.objects.create(
            name=name,
            sku=sku,
            category_id=category_id,
            purchase_price=purchase_price,
            selling_price=selling_price,
            stock_quantity=stock_quantity,
            is_active=is_active,
        )

        for image in request.FILES.getlist("images"):
            ProductImage.objects.create(product=product, image=image)

        messages.success(request, f"{product.name} added successfully.")
        return redirect("product_list")

    return render(
        request,
        "admin/products/form.html",
        {"categories": categories, "product": None},
    )


@login_required
def product_edit(request, product_id):
    if not admin_only(request):
        return redirect("billing")

    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.filter(is_active=True).order_by("name")
    existing_images = product.images.all()

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        sku = request.POST.get("sku", "").strip()
        category_id = request.POST.get("category")
        purchase_price = request.POST.get("purchase_price", "0")
        selling_price = request.POST.get("selling_price", "0")
        stock_quantity = request.POST.get("stock_quantity", "0")
        is_active = request.POST.get("is_active") == "on"

        if not all([name, sku, category_id]):
            messages.error(request, "Please fill all required fields.")
            return render(
                request,
                "admin/products/form.html",
                {
                    "categories": categories,
                    "product": product,
                    "existing_images": existing_images,
                },
            )

        if Product.objects.filter(sku=sku).exclude(id=product.id).exists():
            messages.error(request, "SKU already exists.")
            return render(
                request,
                "admin/products/form.html",
                {
                    "categories": categories,
                    "product": product,
                    "existing_images": existing_images,
                },
            )

        product.name = name
        product.sku = sku
        product.category_id = category_id
        product.purchase_price = purchase_price
        product.selling_price = selling_price
        product.stock_quantity = stock_quantity
        product.is_active = is_active
        product.save()

        for image in request.FILES.getlist("images"):
            ProductImage.objects.create(product=product, image=image)

        messages.success(request, f"{product.name} updated successfully.")
        return redirect("product_list")

    return render(
        request,
        "admin/products/form.html",
        {
            "categories": categories,
            "product": product,
            "existing_images": existing_images,
        },
    )


@login_required
def product_delete(request, product_id):
    if not admin_only(request):
        return redirect("billing")

    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        try:
            name = product.name
            product.delete()
            messages.success(request, f"{name} deleted successfully.")
        except ProtectedError:
            messages.error(
                request,
                "This product cannot be deleted because it is used in a transaction.",
            )

    return redirect("product_list")


@login_required
def product_image_delete(request, image_id):
    if not admin_only(request):
        return redirect("billing")

    product_image = get_object_or_404(ProductImage, id=image_id)
    product_id = product_image.product.id

    if request.method == "POST":
        if product_image.image:
            product_image.image.delete(save=False)
        product_image.delete()
        messages.success(request, "Product image removed successfully.")

    return redirect("product_edit", product_id=product_id)


@login_required
def category_list(request):
    if not admin_only(request):
        return redirect("billing")

    categories = (
        Category.objects
        .prefetch_related("products")
        .all()
        .order_by("name")
    )

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        categories = categories.filter(name__icontains=search)

    if status == "active":
        categories = categories.filter(is_active=True)
    elif status == "inactive":
        categories = categories.filter(is_active=False)

    return render(
        request,
        "admin/categories/list.html",
        {
            "categories": categories,
            "search": search,
            "selected_status": status,
        },
    )


@login_required
def category_create(request):
    if not admin_only(request):
        return redirect("billing")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        is_active = request.POST.get("is_active") == "on"
        image = request.FILES.get("image")

        if not name:
            messages.error(request, "Category name is required.")
        elif Category.objects.filter(name__iexact=name).exists():
            messages.error(request, "Category already exists.")
        else:
            Category.objects.create(
                name=name,
                description=description,
                image=image,
                is_active=is_active,
            )
            messages.success(request, "Category added successfully.")
            return redirect("category_list")

    return render(
        request,
        "admin/categories/form.html",
        {"category": None},
    )


@login_required
def category_edit(request, category_id):
    if not admin_only(request):
        return redirect("billing")

    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        is_active = request.POST.get("is_active") == "on"
        image = request.FILES.get("image")

        if not name:
            messages.error(request, "Category name is required.")
        elif (
            Category.objects
            .filter(name__iexact=name)
            .exclude(id=category.id)
            .exists()
        ):
            messages.error(request, "Category already exists.")
        else:
            category.name = name
            category.description = description
            category.is_active = is_active

            if image:
                if category.image:
                    category.image.delete(save=False)
                category.image = image

            category.save()

            messages.success(request, "Category updated successfully.")
            return redirect("category_list")

    return render(
        request,
        "admin/categories/form.html",
        {"category": category},
    )

@login_required
def category_delete(request, category_id):
    if not admin_only(request):
        return redirect("billing")

    if request.method != "POST":
        return redirect("category_list")

    category = get_object_or_404(Category, id=category_id)
    name = category.name

    try:
       
        if category.products.exists():
            messages.error(
                request,
                f"Category '{name}' cannot be deleted because it is assigned to one or more products."
            )
            return redirect("category_list")

   
        category.delete()

        messages.success(
            request,
            f"Category '{name}' deleted successfully."
        )

    except ProtectedError:
        messages.error(
            request,
            f"Category '{name}' cannot be deleted because it is being used by a product."
        )

    except Exception as e:
        messages.error(
            request,
            f"Unable to delete category: {e}"
        )

    return redirect("category_list")
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login, logout
from .models import StaffProfile

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin_dashboard")

        try:
            profile = request.user.staffprofile
            if profile.role == "staff":
                return redirect("billing")
        except StaffProfile.DoesNotExist:
            pass

        return redirect("billing")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            if not user.is_active:
                messages.error(request, "Your account is inactive.")
                return render(request, "accounts/login.html")

            login(request, user)

            if user.is_superuser:
                return redirect("admin_dashboard")

            try:
                profile = user.staffprofile
                if profile.role == "staff":
                    return redirect("billing")
            except StaffProfile.DoesNotExist:
                logout(request)
                messages.error(request, "Staff profile not found.")
                return render(request, "accounts/login.html")

            logout(request)
            messages.error(request, "You do not have access to this system.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

def admin_only(request):
    return request.user.is_superuser


@login_required
def staff_list(request):
    if not admin_only(request):
        return redirect("billing")

    staff_members = (
        StaffProfile.objects
        .select_related("user")
        .all()
        .order_by("-id")
    )

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        staff_members = staff_members.filter(
            user__username__icontains=search
        ) | StaffProfile.objects.select_related("user").filter(
            user__email__icontains=search
        )

    if status == "active":
        staff_members = staff_members.filter(user__is_active=True)
    elif status == "inactive":
        staff_members = staff_members.filter(user__is_active=False)

    return render(
        request,
        "admin/staff/list.html",
        {
            "staff_members": staff_members,
            "search": search,
            "selected_status": status,
        },
    )


@login_required
def staff_create(request):
    if not admin_only(request):
        return redirect("billing")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        is_active = request.POST.get("is_active") == "on"

        if not username or not password or not confirm_password:
            messages.error(
                request,
                "Username, password and confirm password are required.",
            )
            return render(
                request,
                "admin/staff/form.html",
                {"staff_member": None},
            )

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Username already exists.")
            return render(
                request,
                "admin/staff/form.html",
                {"staff_member": None},
            )

        if email and User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email already exists.")
            return render(
                request,
                "admin/staff/form.html",
                {"staff_member": None},
            )

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(
                request,
                "admin/staff/form.html",
                {"staff_member": None},
            )

        if len(password) < 6:
            messages.error(
                request,
                "Password must contain at least 6 characters.",
            )
            return render(
                request,
                "admin/staff/form.html",
                {"staff_member": None},
            )

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=is_active,
                is_staff=False,
                is_superuser=False,
            )

            StaffProfile.objects.create(
                user=user,
                phone=phone,
                role="staff",
            )

            messages.success(
                request,
                f"Staff '{username}' added successfully.",
            )
            return redirect("staff_list")

        except IntegrityError:
            messages.error(
                request,
                "Unable to create staff. Please check the entered details.",
            )

    return render(
        request,
        "admin/staff/form.html",
        {"staff_member": None},
    )


@login_required
def staff_edit(request, staff_id):
    if not admin_only(request):
        return redirect("billing")

    staff_member = get_object_or_404(
        StaffProfile.objects.select_related("user"),
        id=staff_id,
    )

    user = staff_member.user

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        is_active = request.POST.get("is_active") == "on"

        if not username:
            messages.error(request, "Username is required.")
            return render(
                request,
                "admin/staff/form.html",
                {"staff_member": staff_member},
            )

        if User.objects.filter(username__iexact=username).exclude(
            id=user.id
        ).exists():
            messages.error(request, "Username already exists.")
            return render(
                request,
                "admin/staff/form.html",
                {"staff_member": staff_member},
            )

        if email and User.objects.filter(
            email__iexact=email
        ).exclude(id=user.id).exists():
            messages.error(request, "Email already exists.")
            return render(
                request,
                "admin/staff/form.html",
                {"staff_member": staff_member},
            )

        if password or confirm_password:
            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(
                    request,
                    "admin/staff/form.html",
                    {"staff_member": staff_member},
                )

            if len(password) < 6:
                messages.error(
                    request,
                    "Password must contain at least 6 characters.",
                )
                return render(
                    request,
                    "admin/staff/form.html",
                    {"staff_member": staff_member},
                )

            user.set_password(password)

        user.username = username
        user.email = email
        user.is_active = is_active
        user.save()

        staff_member.phone = phone
        staff_member.save(update_fields=["phone"])

        messages.success(
            request,
            f"Staff '{username}' updated successfully.",
        )
        return redirect("staff_list")

    return render(
        request,
        "admin/staff/form.html",
        {"staff_member": staff_member},
    )


@login_required
def staff_toggle_status(request, staff_id):
    if not admin_only(request):
        return redirect("billing")

    if request.method != "POST":
        return redirect("staff_list")

    staff_member = get_object_or_404(
        StaffProfile.objects.select_related("user"),
        id=staff_id,
    )

    user = staff_member.user
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])

    status_text = "activated" if user.is_active else "deactivated"

    messages.success(
        request,
        f"Staff '{user.username}' {status_text} successfully.",
    )

    return redirect("staff_list")
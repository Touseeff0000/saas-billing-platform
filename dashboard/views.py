import datetime
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from accounts.models import User
from tenants.models import Tenant
from billing.models import UsageRecord, Plan, Subscription

stripe.api_key = settings.STRIPE_SECRET_KEY


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard-home')

    if request.method == "POST":
        name = request.POST.get("company_name")
        slug = request.POST.get("slug")
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email", "")

        if not all([name, slug, username, password]):
            messages.error(request, "All fields except email are required.")
            return render(request, "dashboard/register.html")

        if Tenant.objects.filter(slug=slug).exists():
            messages.error(request, "That company slug is already taken.")
            return render(request, "dashboard/register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "That username is already taken.")
            return render(request, "dashboard/register.html")

        with transaction.atomic():
            tenant = Tenant.objects.create(name=name, slug=slug)
            user = User.objects.create_user(
                username=username, email=email, password=password,
                tenant=tenant, role="owner",
            )

        auth_login(request, user)
        messages.success(request, f"Welcome, {name}! Your account is ready.")
        return redirect('dashboard-home')

    return render(request, "dashboard/register.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard-home')

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard-home')
        messages.error(request, "Invalid username or password.")

    return render(request, "dashboard/login.html")


def logout_view(request):
    auth_logout(request)
    return redirect('login')


@login_required(login_url='login')
def home_view(request):
    tenant = request.user.tenant
    subscription = getattr(tenant, "subscription", None)
    usage = None
    usage_percent = 0

    if subscription:
        period_start = datetime.date.today().replace(day=1)
        usage, created = UsageRecord.objects.get_or_create(
            tenant=tenant, period_start=period_start
        )
        limit = subscription.plan.max_records
        usage_percent = int((usage.count / limit) * 100) if limit else 0

    return render(request, "dashboard/home.html", {
        "tenant": tenant,
        "subscription": subscription,
        "usage": usage,
        "usage_percent": usage_percent,
    })


@login_required(login_url='login')
def plans_view(request):
    plans = Plan.objects.all()
    current_plan_id = None
    subscription = getattr(request.user.tenant, "subscription", None)
    if subscription:
        current_plan_id = subscription.plan_id

    return render(request, "dashboard/plans.html", {
        "plans": plans,
        "current_plan_id": current_plan_id,
    })


@login_required(login_url='login')
def start_checkout_view(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    tenant = request.user.tenant

    if not plan.stripe_price_id:
        messages.error(request, "This plan has no Stripe price attached yet.")
        return redirect('plans')

    success_url = request.build_absolute_uri('/checkout/success/') + '?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = request.build_absolute_uri('/checkout/cancel/')

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(tenant.id),
            metadata={"tenant_id": str(tenant.id), "plan_id": str(plan.id)},
        )
    except Exception as e:
        messages.error(request, f"Stripe error: {e}")
        return redirect('plans')

    return redirect(session.url)


@login_required(login_url='login')
def checkout_success_view(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, "Missing checkout session.")
        return redirect('plans')

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        messages.error(request, f"Could not verify payment: {e}")
        return redirect('plans')

    if session.payment_status != "paid" and session.status != "complete":
        messages.error(request, "Payment was not completed.")
        return redirect('plans')

    tenant_id = session.metadata["tenant_id"]
    plan_id = session.metadata["plan_id"]
    plan = get_object_or_404(Plan, id=plan_id)
    tenant = get_object_or_404(Tenant, id=tenant_id)

    Subscription.objects.update_or_create(
        tenant=tenant,
        defaults={
            "plan": plan,
            "status": "active",
            "stripe_customer_id": session.customer or "",
            "stripe_subscription_id": session.subscription or "",
        },
    )

    messages.success(request, f"Subscribed to {plan.name} successfully!")
    return redirect('dashboard-home')


@login_required(login_url='login')
def checkout_cancel_view(request):
    messages.warning(request, "Checkout was cancelled. No charge was made.")
    return redirect('plans')
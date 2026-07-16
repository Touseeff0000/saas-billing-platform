import datetime
import stripe

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Plan, Subscription, UsageRecord
from .serializers import PlanSerializer, SubscriptionSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


class PlanListView(generics.ListAPIView):
    """Public: anyone can see available pricing plans."""
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]


class MySubscriptionView(generics.RetrieveAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.tenant.subscription


class CreateCheckoutSessionView(APIView):
    """
    Creates a Stripe Checkout session for the logged-in user's tenant to
    subscribe to a plan. Frontend redirects the browser to the returned URL.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get("plan_id")
        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            return Response({"error": "invalid plan"}, status=400)

        tenant = request.user.tenant

        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
            success_url="http://localhost:8000/billing/success/",
            cancel_url="http://localhost:8000/billing/cancel/",
            client_reference_id=str(tenant.id),
        )
        return Response({"checkout_url": session.url})


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    """
    Stripe calls this URL directly whenever a billing event happens
    (payment success, subscription canceled, etc). This is how the
    subscription status in our DB stays in sync with Stripe.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            return HttpResponse(status=400)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            tenant_id = session.get("client_reference_id")
            stripe_customer_id = session.get("customer")
            stripe_subscription_id = session.get("subscription")

            try:
                sub = Subscription.objects.get(tenant_id=tenant_id)
                sub.stripe_customer_id = stripe_customer_id
                sub.stripe_subscription_id = stripe_subscription_id
                sub.status = "active"
                sub.save()
            except Subscription.DoesNotExist:
                pass

        return HttpResponse(status=200)


class UsageView(APIView):
    """
    Returns current month's usage vs the tenant's plan limit.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tenant = request.user.tenant
        period_start = datetime.date.today().replace(day=1)
        usage, _ = UsageRecord.objects.get_or_create(
            tenant=tenant, period_start=period_start
        )
        limit = tenant.subscription.plan.max_records
        return Response(
            {
                "period_start": period_start,
                "used": usage.count,
                "limit": limit,
                "remaining": max(limit - usage.count, 0),
            }
        )


def record_usage(tenant, amount=1):
    """
    Call this from anywhere in the app when a tenant does a metered action:
        from billing.views import record_usage
        record_usage(request.user.tenant)
    """
    period_start = datetime.date.today().replace(day=1)
    usage, _ = UsageRecord.objects.get_or_create(
        tenant=tenant, period_start=period_start
    )
    usage.count += amount
    usage.save()
    return usage
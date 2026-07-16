from django.urls import path
from .views import (
    PlanListView,
    MySubscriptionView,
    CreateCheckoutSessionView,
    StripeWebhookView,
    UsageView,
)

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plan-list"),
    path("my-subscription/", MySubscriptionView.as_view(), name="my-subscription"),
    path("checkout/", CreateCheckoutSessionView.as_view(), name="checkout"),
    path("webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("usage/", UsageView.as_view(), name="usage"),
]
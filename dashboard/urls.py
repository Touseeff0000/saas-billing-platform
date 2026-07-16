from django.urls import path
from .views import (
    register_view, login_view, logout_view, home_view,
    plans_view, start_checkout_view, checkout_success_view, checkout_cancel_view,
)

urlpatterns = [
    path("", home_view, name="dashboard-home"),
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("plans/", plans_view, name="plans"),
    path("checkout/start/<int:plan_id>/", start_checkout_view, name="start-checkout"),
    path("checkout/success/", checkout_success_view, name="checkout-success"),
    path("checkout/cancel/", checkout_cancel_view, name="checkout-cancel"),
]
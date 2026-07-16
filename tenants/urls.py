from django.urls import path
from .views import RegisterTenantView, MyTenantView

urlpatterns = [
    path("register/", RegisterTenantView.as_view(), name="register-tenant"),
    path("me/", MyTenantView.as_view(), name="my-tenant"),
]
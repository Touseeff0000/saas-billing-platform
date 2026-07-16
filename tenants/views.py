from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction

from accounts.models import User
from .models import Tenant
from .serializers import TenantSerializer


class RegisterTenantView(APIView):
    """
    Public endpoint: signing up creates a brand new Tenant PLUS the first
    User for that tenant (role=owner) in one atomic step.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        name = request.data.get("company_name")
        slug = request.data.get("slug")
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email", "")

        if not all([name, slug, username, password]):
            return Response(
                {"error": "company_name, slug, username, password are required"},
                status=400,
            )

        if Tenant.objects.filter(slug=slug).exists():
            return Response({"error": "slug already taken"}, status=400)

        with transaction.atomic():
            tenant = Tenant.objects.create(name=name, slug=slug)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                tenant=tenant,
                role="owner",
            )

        return Response(
            {
                "tenant": TenantSerializer(tenant).data,
                "user": {"id": user.id, "username": user.username, "role": user.role},
            },
            status=201,
        )


class MyTenantView(generics.RetrieveAPIView):
    """Returns the tenant the currently logged-in user belongs to."""
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.tenant
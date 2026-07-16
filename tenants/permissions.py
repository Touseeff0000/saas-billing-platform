from rest_framework.permissions import BasePermission


class IsTenantMember(BasePermission):
    """
    Only allows access if the requesting user belongs to a tenant.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.tenant_id is not None
        )
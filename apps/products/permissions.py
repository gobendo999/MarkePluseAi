from rest_framework import permissions


class IsOwnerOnly(permissions.BasePermission):
    

    def has_permission(self, request, view):
        # login required for any action
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # admin allowed to view/edit/delete any product
        if request.user.is_staff:
            return True

        return obj.user == request.user
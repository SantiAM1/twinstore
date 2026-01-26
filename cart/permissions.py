from rest_framework.permissions import BasePermission

class TieneCarrito(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return True if request.session['carrito'] else False

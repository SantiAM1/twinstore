from rest_framework.permissions import BasePermission

class TieneCarrito(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return 'anon_cart_id' in request.session and 'carrito' in request.session and request.session['carrito']

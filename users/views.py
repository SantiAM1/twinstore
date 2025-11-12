from .models import PerfilUsuario,TokenUsers
from .decorators import login_required_modal
from .emails import mail_recuperar_cuenta_html

from payment.models import HistorialCompras
from cart.utils import merge_carts,clear_carrito_cache
from core.permissions import BloquearSiMantenimiento
from core.throttling import ModalUsers,MiCuentaThrottle
from products.models import ReseñaProducto, TokenReseña

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.http import HttpRequest, JsonResponse
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import PedidoSerializer,LoginSerializer,RegisterSerializer,TokenSerializer, MiCuentaSerializer,RecuperarCuentaSerializer,NuevaContraseñaSerializer,ReseñaSerializer

class LoginAPIView(APIView):
    permission_classes = [BloquearSiMantenimiento]
    throttle_classes = [ModalUsers]
    def post(self, request:HttpRequest):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "El email no está registrado."},status=status.HTTP_404_NOT_FOUND)

        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response({"error": "Credenciales incorrectas."},status=status.HTTP_400_BAD_REQUEST)

        perfil:PerfilUsuario = getattr(user, "perfil", None)
        if perfil and not perfil.email_verificado:
            tiene_token = TokenUsers.objects.filter(user=user,tipo="verificar").first()
            if tiene_token and tiene_token.expirado():
                tiene_token.delete()
                TokenUsers.objects.create(user=user,tipo="verificar")
            return Response({"error": "Verificá tu email antes de iniciar sesión.","verificar": True,"modal": "verificar-cuenta"}, status=status.HTTP_400_BAD_REQUEST)

        login(request, user)
        merge_carts(request, user)
        clear_carrito_cache(request)

        key = make_template_fragment_key("header_main")
        cache.delete(key)
        
        messages.success(request,'Has iniciado sesión correctamente.')

        next_url = request.data.get("next",'')
        if next_url:
            return Response({"redirect": next_url}, status=status.HTTP_200_OK)

        return Response({"reload": True}, status=status.HTTP_200_OK)

class RegisterView(APIView):
    permission_classes = [BloquearSiMantenimiento]
    throttle_classes = [ModalUsers]
    def post(self, request:HttpRequest):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.create_user(
            username=serializer.validated_data["email"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"]
        )

        perfil:PerfilUsuario = user.perfil

        perfil.telefono = serializer.validated_data["telefono"]
        perfil.nombre = serializer.validated_data["nombre"]
        perfil.apellido = serializer.validated_data["apellido"]
        perfil.save()

        token = TokenUsers.objects.create(
            user=user,
            tipo="verificar"
        )

        request.session['email_tag'] = serializer.validated_data["email"]

        return Response({"verificar": True,"modal": "verificar-cuenta"}, status=status.HTTP_200_OK)

class RecuperarCuentaView(APIView):
    permission_classes = [BloquearSiMantenimiento]
    throttle_classes = [ModalUsers]
    def post(self, request:HttpRequest):
        serializer = RecuperarCuentaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "No existe un usuario con ese email."}, status=status.HTTP_404_NOT_FOUND)
        
        perfil:PerfilUsuario = user.perfil
        if not perfil.email_verificado:
            return Response({"error": "El email no ha sido verificado. No se puede recuperar la cuenta."}, status=status.HTTP_400_BAD_REQUEST)
        
        tiene_token = TokenUsers.objects.filter(user=user,tipo="recuperar").first()
        if tiene_token:
            if tiene_token.expirado():
                tiene_token.delete()
            else:
                return Response({"verificar": True,"modal": "recuperar-cuenta"}, status=status.HTTP_200_OK)
        
        token = TokenUsers.objects.create(user=user,tipo="recuperar")
        request.session['email_tag'] = email

        mail_recuperar_cuenta_html(user)

        return Response({"verificar": True,"modal": "recuperar-cuenta"}, status=status.HTTP_200_OK)

class VerificarTokenView(APIView):
    permission_classes = [BloquearSiMantenimiento]
    throttle_classes = [ModalUsers]
    def post(self, request:HttpRequest):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = request.session.get('email_tag','')
        if not email:
            return Response({"error": "Sesión expirada, volvé a ingresar tu email."}, status=status.HTTP_400_BAD_REQUEST)

        codigo = serializer.validated_data["codigo"]

        try:
            token = TokenUsers.objects.get(codigo=str(codigo), user__email=email)
        except TokenUsers.DoesNotExist:
            return Response({"error": "Código inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if token.expirado():
            token.delete()
            return Response({"error": "El código ha expirado. Solicitá uno nuevo."}, status=status.HTTP_400_BAD_REQUEST)
        
        if token.tipo == "verificar":
            perfil = getattr(token.user, "perfil", None)
            if perfil:
                perfil.email_verificado = True
                perfil.save()

            login(request, token.user, backend='django.contrib.auth.backends.ModelBackend')
            merge_carts(request, token.user)
            clear_carrito_cache(request)

            request.session.pop('email_tag', None)
            token.delete()

            messages.success(request,'Cuenta confirmada de manera exitosa.')

            key = make_template_fragment_key("header_main",[request.user.id])
            cache.delete(key)

            next_url = request.data.get("next",'')
            return Response({"redirect": next_url} if next_url else {"reload": True}, status=status.HTTP_200_OK)

        elif token.tipo == "recuperar":
            request.session['new_password_aprove'] = True
            token.delete()
            return Response({"verificar": True,"modal": "nueva-contraseña"}, status=status.HTTP_200_OK)

class NuevaContraseñaView(APIView):
    permission_classes = [BloquearSiMantenimiento]
    throttle_classes = [ModalUsers]
    def post(self, request:HttpRequest):

        if not request.session.get('new_password_aprove',False):
            return Response({"error": "Acción no autorizada."}, status=status.HTTP_403_FORBIDDEN)
        
        email = request.session.get('email_tag')
        if not email:
            return Response({'error': 'Sesión expirada o no autorizada.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = NuevaContraseñaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nueva_contraseña = serializer.validated_data["password"]

        user = User.objects.filter(email=email).first()
        user.set_password(nueva_contraseña)
        user.save()

        request.session.pop('new_password_aprove', None)
        request.session.pop('email_tag', None)

        return Response({"verificar": True,"modal": "signin"}, status=status.HTTP_200_OK)

class MiCuentaView(APIView):
    permission_classes = [IsAuthenticated, BloquearSiMantenimiento]
    throttle_classes = [MiCuentaThrottle]
    def get(self, request:HttpRequest):
        perfil:PerfilUsuario = request.user.perfil
        data = {
            "nombre": perfil.nombre,
            "apellido": perfil.apellido,
            "telefono": perfil.telefono,
            "email":perfil.user.email,
            "dni_cuit": perfil.dni_cuit,
            "codigo_postal": perfil.codigo_postal,
            "direccion": perfil.direccion,
            "localidad": perfil.localidad,
            "provincia": perfil.provincia,
            "razon_social": perfil.razon_social,
            "condicion_iva": perfil.condicion_iva,
        }
        return Response(data, status=status.HTTP_200_OK)
    
    def post(self, request:HttpRequest):
        serializer =  MiCuentaSerializer(data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        perfil:PerfilUsuario = request.user.perfil
        perfil.condicion_iva = data.get("condicion_iva", perfil.condicion_iva)
        perfil.dni_cuit = data.get("dni_cuit", perfil.dni_cuit)
        perfil.razon_social = data.get("razon_social", perfil.razon_social)
        perfil.direccion = data.get("direccion", perfil.direccion)
        perfil.codigo_postal = data.get("codigo_postal", perfil.codigo_postal)
        perfil.localidad = data.get("localidad", perfil.localidad)
        perfil.provincia = data.get("provincia", perfil.provincia)
        perfil.save()

        return Response({"success": True}, status=status.HTTP_200_OK)

class VerPedidoAPIView(APIView):
    permission_classes = [BloquearSiMantenimiento]
    throttle_classes = [MiCuentaThrottle]
    def post(self, request:HttpRequest):
        serializer = PedidoSerializer(data=request.data)
        if serializer.is_valid():
            try:
                historial = HistorialCompras.objects.get(merchant_order_id=serializer.validated_data["order_id"])
            except HistorialCompras.DoesNotExist:
                return Response({"error": "No se encontró un pedido con ese ID."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({"redirect": f"/usuario/pedido/{historial.merchant_order_id}"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CrearReseñaView(APIView):
    permission_classes = [IsAuthenticated, BloquearSiMantenimiento]
    throttle_classes = [MiCuentaThrottle]
    def post(self, request:HttpRequest):
        serializer = ReseñaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]

        try:
            token_obj = TokenReseña.objects.get(token=token)
        except TokenReseña.DoesNotExist:
            return Response({"error": "Token inválido."}, status=status.HTTP_400_BAD_REQUEST)

        rating = serializer.validated_data.get("rating")
        review_text = serializer.validated_data.get("review","")

        reseña = ReseñaProducto.objects.create(
            producto=token_obj.producto,
            usuario=request.user.perfil,
            calificacion=rating,
            comentario=review_text
        )

        token_obj.delete()

        messages.success(request,'Muchas gracias por dejar tu reseña!')

        return Response({"success": True}, status=status.HTTP_201_CREATED)

def check_auth(request):
    return JsonResponse({'is_authenticated': request.user.is_authenticated})

@login_required_modal
def mi_perfil(request):
    historial = HistorialCompras.objects.filter(usuario=request.user).order_by('-fecha_compra').prefetch_related('tickets','comprobante')
    return render(request,'users/micuenta.html',{'historial':historial})

@login_required
def cerrar_sesion(request):
    logout(request)
    key = make_template_fragment_key("header_main", [request.user.id])
    cache.delete(key)
    messages.success(request,'Has cerrado sesión correctamente.')
    return redirect('core:home')

def ver_pedido(request, order_id:str):
    historial = get_object_or_404(HistorialCompras, merchant_order_id=order_id)
    return render(request,'users/pedido.html',{'order':historial})

@login_required_modal
def review_pedido(request:HttpRequest,token:str):
    token_obj = get_object_or_404(TokenReseña, token=token)
    if not token_obj:
        messages.error(request,'No se encontró el token.')
        return redirect('users:perfil')

    if token_obj.usuario.user != request.user:
        messages.error(request, 'No estás autorizado para dejar una reseña para este producto.')
        return redirect('users:perfil')

    producto = token_obj.producto
    return render(request,'users/review_pedido.html',{'producto':producto,'token':token_obj.token})
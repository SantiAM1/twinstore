from django.shortcuts import get_object_or_404, render, redirect
from .forms import RegistrarForm,LoginForm,BuscarPedidoForm,UsuarioForm
from .models import PerfilUsuario,TokenUsers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.views.decorators.http import require_POST
from payment.models import HistorialCompras
import uuid
from django.contrib.auth.decorators import login_required
from .emails import mail_confirm_user_html
from django.utils import timezone
from datetime import timedelta
from .tasks import enviar_mail_reset_password
from django.conf import settings
from .forms import EmailUsuarioRecuperacion,RestablecerContraseña
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordResetForm
from django.utils.translation import gettext_lazy as _
from django.core import signing


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import HistorialIdSerializer

from core.permissions import BloquearSiMantenimiento

from django.template.loader import render_to_string
from core.throttling import ToggleNotificacionesThrottle

from axes.handlers.proxy import AxesProxyHandler

class RecibirMailView(APIView):
    permission_classes = [BloquearSiMantenimiento]
    throttle_classes = [ToggleNotificacionesThrottle]
    def post(self,request):
        serializer = HistorialIdSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            historial_id = signing.loads(data.get('id'))
            historial = HistorialCompras.objects.get(id=historial_id)
            historial.recibir_mail = not historial.recibir_mail
            historial.save()
            html = render_to_string('partials/notificacion.html',{
                'pedido':historial
            })

            return Response({'html':html})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@require_POST
def arrepentimiento_post(request, historial_signed):
    historial_id = signing.loads(historial_signed)
    historial = get_object_or_404(HistorialCompras,id=historial_id)
    if not historial.check_arrepentimiento():
        messages.error(request,'Hubo un error al solicitar el Arrepentimiento')
        return redirect('users:ver_pedidos',token=historial.token_consulta)
    historial.estado = 'arrepentido'
    historial.save()
    messages.success(request,'Arrepentimiento solicitado con éxito')
    return redirect('users:ver_pedidos',token=historial.token_consulta)

@login_required
def asociar_pedido(request):
    if request.method == "POST":
        form = BuscarPedidoForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['token']
            historial = HistorialCompras.objects.filter(token_consulta=token).first()
            if historial:
                if historial.usuario == request.user:
                    messages.error(request,'Ya tienes este pedido asociado')
                else:
                    historial.usuario = request.user
                    historial.save()
                    messages.success(request,'Pedido asociado con éxito!')
                return redirect('users:mispedidos')
            else:
                messages.error(request, "No existe un pedido con ese código.")
                return redirect('users:mispedidos')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
                    return redirect('users:mispedidos')

@login_required
def mi_perfil(request):
    perfil, created = PerfilUsuario.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = UsuarioForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            perfil.condicion_iva = data['condicion_iva']
            perfil.dni_cuit = data['dni_cuit']
            perfil.razon_social = data['razon_social']
            perfil.nombre = data['nombre']
            perfil.apellido = data['apellido']
            perfil.calle = data['calle']
            perfil.calle_detail = data['calle_detail']
            perfil.ciudad = data['ciudad']
            perfil.provincia = data['provincia']
            perfil.codigo_postal = data['codigo_postal']
            perfil.telefono = data['telefono']
            perfil.preferencias_promociones = data['preferencias_promociones']
            perfil.save()
            messages.success(request,'Usuario actualizado con éxito!')
    form = UsuarioForm(initial={
            'condicion_iva': perfil.condicion_iva,
            'dni_cuit': perfil.dni_cuit,
            'razon_social': perfil.razon_social,
            'nombre': perfil.nombre,
            'apellido': perfil.apellido,
            'calle': perfil.calle,
            'calle_detail': perfil.calle_detail,
            'ciudad': perfil.ciudad,
            'provincia': perfil.provincia,
            'codigo_postal': perfil.codigo_postal,
            'email': request.user.email,
            'telefono': perfil.telefono,
            'preferencias_promociones': perfil.preferencias_promociones
        })
    return render(request,'users/perfil.html',{
        'form':form
    })

@login_required
def users_pedidos(request):
    form = BuscarPedidoForm()
    historial = HistorialCompras.objects.filter(usuario=request.user)
    return render(request,'users/pedidos.html',{'historial':historial,'form':form})

def buscar_pedidos(request):
    form = BuscarPedidoForm()
    if request.method == "POST":
        form = BuscarPedidoForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['token']
            return redirect('users:ver_pedidos',token=token)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
                    return redirect('users:buscar_pedidos')
    return render(request, 'users/buscar_pedido.html', {'form': form})

def ver_pedido(request,token):
    historial = HistorialCompras.objects.filter(token_consulta=token)
    if historial:
        return render(request, 'users/ver_pedido.html', {'historial': historial})
    else:
        messages.error(request, "No existe un pedido con ese código.")
        return redirect('users:buscar_pedidos')

@login_required
def cerrar_sesion(request):
    logout(request)
    messages.info(request,'Sesión cerrada con éxito!')
    return redirect('core:home')

def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect('core:home')
    form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            # 🔒 Verificar si el intento está bloqueado por Axes
            if AxesProxyHandler.is_locked(request, credentials={'username': form.cleaned_data['email']}):
                messages.error(request, "Demasiados intentos fallidos. Esperá 1 hora para volver a intentar.")
                return redirect('users:login')
            
            user = authenticate(
                request=request,
                username=form.cleaned_data['email'],
                password=form.cleaned_data['password']
                )
            if user is not None:
                perfil = user.perfil
                if not perfil.email_verificado:
                    messages.warning(request, "Primero tenes que verificar tu correo para ingresar")
                    return redirect('users:login')
                login(request, user)
                messages.info(request,'Bienvenido a Twistore!')
                return redirect('core:home')
            else:
                messages.error(request, "El email o la contraseña ingresados no son correctos.")
                return redirect('users:login')
    return render(request,'users/login.html',{'form':form})

def registarse(request):
    if request.user.is_authenticated:
        return redirect('core:home')
    form = RegistrarForm()
    if request.method == "POST":
        form = RegistrarForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            # * Forzamos acceso al perfil (por si aún no se generó en el signal)
            _ = user.perfil

            mail_confirm_user_html(user)

            request.session['token_verificacion'] = str(user.perfil.token_verificacion)
            return redirect('users:email_enviado')
        else:
            if form.errors.get('email'):
                for error in form.errors.get('email'):
                    messages.error(request, error)
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)
            return redirect('users:singup')
    return render(request, 'users/registro.html', {'form': form})

def email_enviado(request):
    return render(request,'users/confirmar_mail.html')

def verificar_email(request,token):
    try:
        perfil = get_object_or_404(PerfilUsuario, token_verificacion=token)
        perfil.email_verificado = True
        perfil.token_verificacion = None
        if request.session.get('token_verificacion',''):
            del request.session['token_verificacion']
        perfil.save()
        messages.success(request,'Usuario confirmado con éxito!')
        return redirect('users:login')
    except:
        return render(request,'users/error_mail.html')

def reenviar_verificacion(request):
    token = request.session.get('token_verificacion','')
    if not token:
        messages.warning(request, "Hubo un problema, intente mas tarde.")
        return redirect('users:email_enviado')
    perfil = get_object_or_404(PerfilUsuario,token_verificacion=token)

    tiene_token = TokenUsers.objects.filter(user=perfil.user,tipo="crear").first()
    if tiene_token:
        if tiene_token.expirado():
            tiene_token.delete()
        else:
            messages.warning(request, "Por favor, esperá unos minutos antes de volver a reenviar el mail.")
            return redirect('users:email_enviado')
        
    user = perfil.user
    token_ticket = TokenUsers.objects.create(user=user,tipo="crear")
    mail_confirm_user_html(user)
    messages.success(request, "Te reenviamos el correo de verificación.")
    return redirect('users:email_enviado')

def recuperar_contraseña(request):
    if request.method == "POST":
        form = EmailUsuarioRecuperacion(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email=email).first()
            if user:
                tiene_token = TokenUsers.objects.filter(user=user,tipo="recuperar").first()
                if tiene_token:
                    if tiene_token.expirado():
                        tiene_token.delete()
                    else:
                        messages.error(request, f"Ya has solicitado esta acción, si el error persiste contactanos.")
                        return redirect('users:recuperar') 
                token = TokenUsers.objects.create(user=user,tipo="recuperar")
                url = f"{settings.SITE_URL}/usuario/restablecer/{token.token}/"
                context = {
                    "email":user.email,
                    "url":url
                }
                enviar_mail_reset_password.delay(context)
                messages.success(request, f"Email enviado con exito!")
                return redirect('users:login')
            else:
                messages.error(request, "No existe un usuario con ese correo")
                return redirect('users:singup')

    form = EmailUsuarioRecuperacion()
    return render(request,'users/recuperar_password.html',{'form':form})

def restablecer_contraseña(request,token):
    token_obj = get_object_or_404(TokenUsers, token=token,tipo="recuperar")

    if token_obj.expirado():
        token_obj.delete()
        messages.error(request, "⏳ El enlace expiró. Solicitá uno nuevo.")
        return redirect('users:login')
    
    if request.method == "POST":
        form = RestablecerContraseña(request.POST)
        if form.is_valid():
            nueva_contraseña = form.cleaned_data['password']
            user = token_obj.user
            user.set_password(nueva_contraseña)
            user.save()
            token_obj.delete()
            messages.success(request, "Contraseña actualizada con éxito.")
            return redirect('users:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return render(request,'users/restablecer_password.html',{'form':form})
    form = RestablecerContraseña()
    return render(request,'users/restablecer_password.html',{'form':form})
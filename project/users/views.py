from django.shortcuts import get_object_or_404, render, redirect
from .forms import RegistrarForm,LoginForm,BuscarPedidoForm,UsuarioForm
from .models import PerfilUsuario
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from payment.models import HistorialCompras
import uuid
from django.contrib.auth.decorators import login_required
from .emails import mail_confirm_user_async
from django.utils import timezone
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RecibirMailSerializer

from core.permissions import BloquearSiMantenimiento

from django.template.loader import render_to_string
from core.throttling import ToggleNotificacionesThrottle

from axes.handlers.proxy import AxesProxyHandler

class RecibirMailView(APIView):
    permission_classes = [BloquearSiMantenimiento]
    throttle_classes = [ToggleNotificacionesThrottle]
    def post(self,request):
        serializer = RecibirMailSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            token = data['token']
            historial = HistorialCompras.objects.filter(token_consulta = token).first()
            historial.recibir_mail = not historial.recibir_mail
            historial.save()
            html = render_to_string('partials/notificacion.html',{
                'pedido':historial
            })

            return Response({'html':html})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
                    messages.success(request,'Pedido asociado con exito!')
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
            perfil.tipo_factura = data['tipo_factura']
            perfil.dni_cuit = data['dni_cuit']
            perfil.razon_social = data['razon_social']
            perfil.nombre = data['nombre']
            perfil.apellido = data['apellido']
            perfil.calle = data['calle']
            perfil.calle_detail = data['calle_detail']
            perfil.cuidad = data['cuidad']
            perfil.provincia = data['provincia']
            perfil.codigo_postal = data['codigo_postal']
            perfil.telefono = data['telefono']
            perfil.save()
            messages.success(request,'Usuario actualizado con exito!')
    form = UsuarioForm(initial={
            'tipo_factura': perfil.tipo_factura,
            'dni_cuit': perfil.dni_cuit,
            'razon_social': perfil.razon_social,
            'nombre': perfil.nombre,
            'apellido': perfil.apellido,
            'calle': perfil.calle,
            'calle_detail': perfil.calle_detail,
            'cuidad': perfil.cuidad,
            'provincia': perfil.provincia,
            'codigo_postal': perfil.codigo_postal,
            'email': request.user.email,
            'telefono': perfil.telefono,
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
    messages.info(request,'Sesion cerrada con exito!')
    return redirect('core:home')

def iniciar_sesion(request):
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

            # * Enviamos el mail de verificación (modo rápido actual)
            mail_confirm_user_async(user)

            return redirect('users:email_enviado',token = user.perfil.token_verificacion)
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

def email_enviado(request,token):
    return render(request,'users/confirmar_mail.html',{'token':token})

def verificar_email(request, token):
    try:
        perfil = get_object_or_404(PerfilUsuario, token_verificacion=token)
        perfil.email_verificado = True
        perfil.token_verificacion = None
        perfil.save()
        messages.success(request,'Usuario confirmado con exito!')
        return redirect('users:login')
    except:
        return render(request,'users/error_mail.html')

def reenviar_verificacion(request, token):
    token = token
    perfil = PerfilUsuario.objects.filter(token_verificacion=token).first()
    
    if perfil.email_verificado:
        return redirect('core:home')

    # ⏱️ Verificamos si ya envió uno recientemente (último intento guardado en sesión)
    ultimo_envio = request.session.get('ultimo_envio_verificacion')
    ahora = timezone.now()

    if ultimo_envio:
        hace_cuanto = ahora - timezone.datetime.fromisoformat(ultimo_envio)
        if hace_cuanto < timedelta(minutes=2):  # Espera mínima entre reintentos
            messages.warning(request, "⏳ Por favor, esperá unos minutos antes de volver a reenviar el mail.")
            return redirect('users:email_enviado',token=token)

    user = perfil.user

    mail_confirm_user_async(user)

    request.session['ultimo_envio_verificacion'] = ahora.isoformat()

    messages.success(request, "📧 Te reenviamos el correo de verificación.")

    return redirect('users:email_enviado',token=token)
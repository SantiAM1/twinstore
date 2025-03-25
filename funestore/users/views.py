from django.shortcuts import render, redirect
from .forms import FacturacionForm,RegistrarForm,LoginForm,BuscarPedidoForm,DatosPersonales,PreferenciasUsuarios
from shipping.forms import DatosEnvioForm
from .models import PerfilUsuario
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from payment.models import HistorialCompras
import uuid
from django.contrib.auth.decorators import login_required
from shipping.models import DatosEnvio


@login_required
def mi_perfil(request):
    if request.method == "POST":
        perfil, create = PerfilUsuario.objects.get_or_create(user = request.user)
        datos_envio_form = DatosEnvioForm(request.POST)
        if datos_envio_form.is_valid():
            DatosEnvio.objects.update_or_create(
            usuario=request.user,
            defaults={
                'calle': datos_envio_form.cleaned_data['calle'],
                'altura': datos_envio_form.cleaned_data['altura'],
                'ciudad': datos_envio_form.cleaned_data['ciudad'],
                'provincia': datos_envio_form.cleaned_data['provincia'],
                'codigo_postal': datos_envio_form.cleaned_data['codigo_postal']
            }
        )
        facturacion_form = FacturacionForm(request.POST)
        if facturacion_form.is_valid():
            perfil.tipo_factura = facturacion_form.cleaned_data['tipo_factura']
            perfil.razon_social = facturacion_form.cleaned_data['razon_social']
            perfil.dni_cuit = facturacion_form.cleaned_data['dni_cuit']
        datos_personales_form = DatosPersonales(request.POST)
        if datos_personales_form.is_valid():
            perfil.nombre = datos_personales_form.cleaned_data['nombre']
            perfil.apellido = datos_personales_form.cleaned_data['apellido']
        preferencias_form = PreferenciasUsuarios(request.POST)
        if preferencias_form.is_valid():
            perfil.preferencias_promociones = preferencias_form.cleaned_data['recibir_promociones']
            perfil.preferencias_estado_pedido = preferencias_form.cleaned_data['recibir_estado_pedido']
        perfil.save()

    usuario = request.user.perfil
    facturacion_form = FacturacionForm(
        initial={
            'tipo_factura':usuario.tipo_factura,
            'razon_social':usuario.razon_social,
            'dni_cuit':usuario.dni_cuit,
            'email':request.user.email
        }
    )
    datos_personales_form = DatosPersonales(
        initial={
            'nombre':usuario.nombre,
            'apellido':usuario.apellido,
            'email':request.user.email
        }
    )
    preferencias_form = PreferenciasUsuarios(
        initial={
            'recibir_promociones':usuario.preferencias_promociones,
            'recibir_estado_pedido':usuario.preferencias_estado_pedido
        }
    )
    direccion_envio = request.user.direcciones_envio.first()
    if direccion_envio:
        direccion_completa = f"{direccion_envio.calle} {direccion_envio.altura}, {direccion_envio.ciudad}, {direccion_envio.provincia or ''}, CP {direccion_envio.codigo_postal}"
    else:
        direccion_completa = ''

    datos_envio_form = DatosEnvioForm(
    initial={
        'direccion_completa': direccion_completa,
        'calle': direccion_envio.calle if direccion_envio else '',
        'altura': direccion_envio.altura if direccion_envio else '',
        'ciudad': direccion_envio.ciudad if direccion_envio else '',
        'provincia': direccion_envio.provincia if direccion_envio else '',
        'codigo_postal': direccion_envio.codigo_postal if direccion_envio else '',
    }
)

    return render(request,'users/perfil.html',{
        'facturacion_form':facturacion_form,
        'datos_personales_form':datos_personales_form,
        'preferencias_form':preferencias_form,
        'datos_envio_form':datos_envio_form
    })

def ver_pedidos(request):
    if request.user.is_authenticated:
        historial = HistorialCompras.objects.filter(usuario=request.user)
        return render(request,'users/pedidos.html',{'historial':historial})
    form = BuscarPedidoForm()
    if request.method == "POST":
        form = BuscarPedidoForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['token']
            historial = HistorialCompras.objects.filter(token_consulta=token)
            if historial:
                return render(request, 'users/ver_pedido.html', {'historial': historial})
            else:
                messages.error(request, "No existe un pedido con ese código.")
                return redirect('users:pedidos')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
                    return redirect('users:pedidos')
    return render(request, 'users/buscar_pedido.html', {'form': form})

def facturacion_view(request):
    form = FacturacionForm()
    if request.method == "POST":
        form = FacturacionForm(request.POST)
        if form.is_valid():
            if request.user.is_authenticated:
                perfil, create = PerfilUsuario.objects.get_or_create(user = request.user)
                perfil.tipo_factura = form.cleaned_data['tipo_factura']
                perfil.razon_social = form.cleaned_data['razon_social']
                perfil.dni_cuit = form.cleaned_data['dni_cuit']
                perfil.save()
                return redirect('cart:ver_carrito')
            request.session['datos_facturacion'] = {
                'tipo_factura':form.cleaned_data['tipo_factura'],
                'razon_social':form.cleaned_data['razon_social'],
                'dni_cuit':form.cleaned_data['dni_cuit'],
                'email':form.cleaned_data['email']
            }
            request.session.modified = True
            return redirect('cart:ver_carrito')
    return render(request, 'users/facturacion.html', {'form': form})

def iniciar_sesion(request):
    form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['email'], password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
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
            user = authenticate(username=form.cleaned_data['email'], password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)

                return redirect('core:home')
            else:
                messages.error(request, "Ocurrió un error inesperado al registrarte. Por favor, intentá ingresar manualmente.")
                return redirect('users:singup')
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

@login_required
def cerrar_sesion(request):
    logout(request)
    return redirect('core:home')
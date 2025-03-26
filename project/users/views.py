from django.shortcuts import render, redirect
from .forms import RegistrarForm,LoginForm,BuscarPedidoForm,PreferenciasUsuarios,UsuarioForm
from .models import PerfilUsuario
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from payment.models import HistorialCompras
import uuid
from django.contrib.auth.decorators import login_required


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
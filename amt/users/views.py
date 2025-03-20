from django.shortcuts import render, redirect
from .forms import FacturacionForm
from .models import PerfilUsuario

def datos_facturacion(request):
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
                'dni_cuit':form.cleaned_data['dni_cuit']
            }
            request.session.modified = True
            return redirect('cart:ver_carrito')
    form = FacturacionForm()
    return render(request,'users/facturacion.html',{"form":form})

def iniciar_sesion(request):
    return render(request,'users/login.html')

def registarse(request):
    return render(request,'users/register.html')
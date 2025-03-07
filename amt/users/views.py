from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistroForm, LoginForm,PerfilForm
from .models import PerfilUsuario

def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            perfil = PerfilUsuario.objects.create(user=user)
            enviar_email_verificacion(user.email, perfil.token_verificacion)

            messages.success(request, "Registro exitoso. Revisa tu email para activar tu cuenta.")
            return redirect("users:login")

    else:
        form = RegistroForm()
    return render(request, "register.html", {"form": form})

def enviar_email_verificacion(email, token):
    subject = "Verificación de Cuenta"
    message = f"Por favor, haz clic en el siguiente enlace para activar tu cuenta: {settings.SITE_URL}/usuario/verificar/{token}/"
    send_mail(subject, message, settings.EMAIL_HOST_USER, [email])

def verificar_email(request, token):
    perfil = get_object_or_404(PerfilUsuario, token_verificacion=token)
    perfil.email_verificado = True
    perfil.user.is_active = True  # Activa la cuenta
    perfil.user.save()
    perfil.save()
    messages.success(request, "Tu cuenta ha sido verificada. Ahora puedes iniciar sesión.")
    return redirect("users:login")

def inicio_sesion(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "No existe una cuenta con este correo electrónico.")
                return render(request, "inicio_sesion.html", {"form": form})

            if not user.is_active:
                messages.error(request, "Debes verificar tu email antes de iniciar sesión.")
                return render(request, "inicio_sesion.html", {"form": form})

            user = authenticate(request, username=user.username, password=password)
            if user:
                login(request, user)
                
                if form.cleaned_data.get("remember_me"):
                    # request.session.set_expiry(1209600)
                    pass

                return redirect("core:home")
            else:
                messages.error(request, "Contraseña incorrecta.")
    
    else:
        form = LoginForm()

    return render(request, "inicio_sesion.html", {"form": form})


@login_required
def perfil(request):
    perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)  # Obtener o crear perfil

    if request.method == "POST":
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "Tus datos han sido actualizados correctamente.")
            return redirect("users:perfil")
    else:
        form = PerfilForm(instance=perfil)

    return render(request, "perfil.html", {"form": form})

def cerrar_sesion(request):
    logout(request)  # Cierra la sesión del usuario
    return redirect("core:home")  # Redirige a la página principal después de cerrar sesión

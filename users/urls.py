from django.urls import path
from .views import iniciar_sesion,registarse,cerrar_sesion,buscar_pedidos,mi_perfil,verificar_email,email_enviado,reenviar_verificacion,users_pedidos,ver_pedido,RecibirMailView,asociar_pedido,arrepentimiento_post,recuperar_contraseña,restablecer_contraseña

app_name = "users"

urlpatterns = [
    path('login/',iniciar_sesion,name="login"),
    path('singup/',registarse,name="singup"),
    path('logout/',cerrar_sesion,name="logout"),
    path('buscar_pedidos/',buscar_pedidos,name="buscar_pedidos"),
    path('ver_pedido/<str:token>',ver_pedido,name="ver_pedidos"),
    path('mispedidos/',users_pedidos,name="mispedidos"),
    path('miperfil/',mi_perfil,name="perfil"),
    path('verificar/<str:token>',verificar_email,name="verificar"),
    path('email_enviado/',email_enviado,name="email_enviado"),
    path('reenviar_mail/',reenviar_verificacion,name="reenviar_mail"),
    path('api/recibir_mail/',RecibirMailView.as_view(),name="recibir_mail"),
    path('asociar_pedido/',asociar_pedido,name="asociar_pedido"),
    path('arrepentimiento/<int:historial_id>/',arrepentimiento_post,name="arrepentimiento_post"),
    path('recuperar/',recuperar_contraseña,name="recuperar"),
    path('restablecer/<str:token>/',restablecer_contraseña,name="restablecer")
]

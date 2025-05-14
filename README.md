# Twinstore
Este proyecto fue reiniciado el 14/05/2025 para eliminar historial sensible. Desarrollado por Santiago Aguirre desde marzo de 2025.

**E-commerce desarrollado con Django y Django REST Framework.**
Plataforma para la venta de productos electrónicos con gestión completa de usuarios, pagos, administración y notificaciones.

---

## Funcionalidades principales

- Catálogo de productos con filtros dinámicos (categorias, subcategorias, marcas, atributos, precio)
- Carrito persistente para usuarios autenticados y anónimos
- Integración con Mercado Pago (Webhooks y pagos multiples)
- Seguridad: Protección CSRF, HTTPS, validación en backend, DOMPurify y endpoints protegidos
- Middleware de Mantenimiento para tareas administrativas seguras
- Sistema de correos automatizados con SendGrid
- Carga masiva de productos vía Excel (importación desde pandas)
- Presupuestos en PDF con WeasyPrint
- Panel de administración personalizado para staff

---

## Tecnologias utilizadas

- **Backend**: Django, Django REST Framework
- **Frontend**: HTML, CSS, JS, SwiperJS, Axios
- **Base de datos**: PostgreSQL
- **Deploy**: Docker, Nginx, Gunicorn, Celery, Redis, DigitalOcean
- **Servicios externos**: Sendgrid, MercadoPago
- **Librerías**: pandas, WeasyPrint

---

## Estructura del proyecto

### `cart/`
App encargada del funcionamiento del carrito de compras:

- Maneja el CRUD de pedidos y la lógica del carrito
- Genera los presupuestos
- Utiliza Axios y Serializers para recopilar datos del cliente
- Crea el 'init_point' de Mercado Pago para el pago
- (Si corresponde) Finaliza la compra: borra el carrito, guarda el historial y los datos de facturación

### `config/`
Contiene la configuración principal del proyecto

- `settings.py`: configuración general del proyecto (apps instaladas, bases de datos, middleware, CORS, emails, etc.)
- `urls.py`: rutas base del proyecto
- `wsgi.py` y `asgi.py`: puntos de entrada para servidores WSGI/ASGI (Gunicorn)
- Recopila las variables de entorno del `.env` para mayor seguridad

### `core/`
App encargada del layout general del sitio y vistas informativas:

- Renderiza páginas estáticas: Home, ¿Quiénes somos?, Políticas, Términos y condiciones, FAQ, Contacto, Punto de retiro
- Administra la carga masiva de productos desde archivos Excel (vía panel staff)
- Utiliza `signals` para actualizar masivamente los precios de productos ante cambios en la divisa

### `payment/`
App encargada de la gestión post-compra y validación de pagos:

- Recibe y procesa Webhooks de Mercado Pago: confirma o anula historiales de compra según el estado del pago
- Muestra los detalles de la compra realizada al usuario
- Recibe y almacena comprobantes de transferencia manual para su posterior validación por parte del staff
- Utiliza `signals` para enviar correos automáticos cuando cambia el estado del historial de compra
- Notifica al staff mediante `signals` cuando un historial requiere revisión (por acción del cliente o respuesta del servidor)
- Gestiona automáticamente las solicitudes de "Arrepentimiento de compra", notificando y ejecutando las acciones correspondientes
- Panel de administración de Historiales personalizado. Gestión de trazabilidad mediante `EstadoPedido` para mayor control entre el servidor y el staff

### `products/`
App encargada de la gestión y visualización de los productos

- Redimensiona automáticamente las imágenes de productos al formato `webp` para optimizar el rendimiento
- Incluye un apartado especial para productos del segmento Gaming
- Implementa filtros dinámicos mediante Axios para una experiencia fluida de navegación
- Se encarga de presentar la búsqueda realizada
- Permite al staff editar productos desde el panel: agregar imágenes, seleccionar portada, modificar nombre y precio, y aplicar descuentos

### `users/`
App encargada de la gestión de usuarios y autenticación:

- Registro e inicio de sesión de usuarios, con verificación de correo antes de activar la cuenta
- Envío de correos automáticos para confirmación de cuenta y recuperación de contraseña
- Protección contra spam en el envío de correos mediante tokens temporales
- Permite a usuarios no registrados buscar pedidos mediante UUID asociado al historial de compra
- Los usuarios registrados acceden a todos sus historiales de compra desde el panel "Mis Pedidos"
- Apartado "Mi Perfil" para completar y modificar los datos de facturación
- Permite asociar pedidos realizados como anónimo cuando el usuario se registra luego de realizar la compra
- Gestiona solicitudes de "Arrepentimiento de compra" iniciadas por el usuario
- Envío automático de correos de confirmación tras completar una compra, incluyendo el detalle de productos (nombre, cantidad, subtotal, total y adicionales)
- Uso de `emails.py` y `tasks.py` para el envío asincrónico de correos utilizando Celery y Redis

---

## Cómo desplegar el proyecto en local

- Cloná el repositorio
```bash
git clone https://github.com/SantiAM1/twinstore.git
cd twinstore
```

- Configurá la base de datos
*Opcion A - PostgreSLQ (Producción)*
Configurá las siguientes variables en tu entorno (.env):
```bash
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
...
```

*Opcion B - SQLite (Desarrollo)*
```bash
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "mydatabase",
    }
}
```
[Documentación](https://docs.djangoproject.com/en/5.2/ref/settings/#databases)

- Levantá los contenedores con Docker:
```bash
docker-compose up -d
```

- Configuración básica del proyecto
```bash
docker compose exec web bash

# Crear usuario administrador
python manage.py createsuperuser

# Importar categorías base
python manage.py importar_categorias

# Generar los permisos del Staff
python manage.py importar_permisos "Gestor de tienda" "Gestor de tienda_permisos.json" 
```

---

## Contacto

Si querés conocer más sobre este proyecto o ponerte en contacto conmigo:

- [LinkedIn](https://www.linkedin.com/in/santiago-aguirre-moretto-87bb46259/)  
- [GitHub](https://github.com/SantiAM1)  
- Email: santiaguirre.lam@gmail.com

---

## Licencia

Este proyecto está licenciado bajo la [MIT License](LICENSE).
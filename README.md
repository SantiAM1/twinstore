# 🛒 Twinstore

**E-commerce desarrollado con Django y Django REST Framework.**
Es un proyecto generalista con funcionalidades completas para la gestión de productos, stock, usuarios, pagos y un panel de administración personalizado para facilitar la gestión del sitio.

## Tecnologías utilizadas

- **Backend**: Django, Django REST Framework
- **Frontend**: HTML, CSS, JS, SwiperJS, Axios
- **Base de datos**: PostgreSQL (Producción), SQLite (Desarrollo)
- **Deploy**: Docker, Nginx, Gunicorn, Celery, Redis
- **Servicios externos**: MercadoPago, Amazon SES
- **Próximos pasos**: Payway, OCA Envíos

## Funcionalidades principales

- Gestión de productos (Con o sin stock)
- Sistema de stock flexible, el administrador puede definir si el sitio funciona con o sin control de stock
- Pagos recibidos por MercadoPago.
- Dashboard de administración personalizado para gestionar productos, usuarios, órdenes y más.
- Sistema de Reseñas para productos.
- Envío de correos electrónicos mediante Amazon SES.
- Modelo Tienda configurable para personalizar el sitio
  - Permite funcionar dos divisas (Ej: **ARS** y **USD**)
  - Define el nombre de la tienda.
  - El sistema de stock (Con o sin stock | Maximo de unidades).
  - Habilitar el modo mantenimiento.

## Funcionalidades técnicas

- Arquitectura RESTful parcial con Django REST Framework.
- Autenticación y autorización de usuarios.
- Queries optimizadas para mejorar el rendimiento (En todo el sitio).
- Manejo de errores y validaciones robustas.
- Cache implementada para mejorar la velocidad de carga.
- Sistema de logs para monitorear la aplicación.
- Tareas asíncronas con Celery y Redis.
- Contenedores Docker para facilitar el despliegue y la escalabilidad.

## Funcionalidades futuras

- Integración con Payway para métodos de pago adicionales.
- Integración con OCA Envíos para gestión de envíos.
- Landing Page completamente personalizable desde el panel de administración.

## Como se ve el proyecto?

https://github.com/user-attachments/assets/bce4e4d3-75f2-4411-8e83-2c117c74bbdb

## Cómo desplegar el proyecto en local

1. Clona el repositorio:

   ```bash
   git clone https://github.com/SantiAM1/twinstore.git
    cd twinstore
   ```

2. Configurá tu entorno virtual e instalá las dependencias:

   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. Configurá las variables de entorno necesarias. Podés basarte en el archivo `.env.example`.

4. Aplicá las migraciones a la base de datos:

   ```bash
   python manage.py migrate
   ```

5. Inicia la tienda.

   ```bash
   python manage.py iniciar_tienda
   python manage.py importar_categorias
   python manage.py importar_permisos "Gestores_permisos.json"
   ```

6. Inicia el servidor:

   ```bash
    python manage.py runserver
   ```

Al iniciar la tienda se genera lo necesario para funcionar (Tienda, Proveedor y Administradores), se crearán dos usuarios, uno administrador y otro como gestor. Podés iniciar sesión con las siguientes credenciales:

- Administrador:
  - Usuario: `superadmin@ts.ar`
  - Contraseña: `superadmin123`
- Gestor:
  - Usuario: `gestor@ts.ar`
  - Contraseña: `admin123`

## Contacto

Si querés conocer más sobre este proyecto o ponerte en contacto conmigo:

- [LinkedIn](https://www.linkedin.com/in/santiago-aguirre-moretto-87bb46259/)
- [GitHub](https://github.com/SantiAM1)
- Email: santiaguirre.lam@gmail.com

## Licencia

Este proyecto está licenciado bajo la [MIT License](LICENSE).

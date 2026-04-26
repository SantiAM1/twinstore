from typing import TypedDict

class DatosEnvio(TypedDict):
    calle_domicilio: str
    altura_domicilio: str
    referencias_domicilio: str
    nombre_reciver: str
    dni_reciver: str
    email_reciver: str
    phone_reciver: str
    metodo_envio: str
    point_id: str | None

class EnvioSeleccionado(TypedDict):
    carrier_id: int
    carrier_logo: str
    carrier_name: str
    fecha_entrega: str
    id_interno_cotizacion: str | None
    logistic_type: str
    precio: float
    requiere_eleccion_sucursal: bool
    service_code: str
    service_name: str
    tags: list[str]

class Facturacion(TypedDict):
    nombre: str
    apellido: str
    dni_cuit: str
    direccion: str
    localidad: str
    provincia: str
    codigo_postal: str
    condicion_iva: str
    razon_social: str

class Cupon(TypedDict):
    codigo: str
    descuento: float

class Pago(TypedDict):
    forma_de_pago: str
    monto_total: float
    monto_transferencia: float | None
    monto_mercadopago: float | None
    es_mixto: bool
    adicional: float | None

class CheckoutData(TypedDict):
    datos_envio: DatosEnvio
    envio_seleccionado: EnvioSeleccionado
    facturacion: Facturacion
    cupon: Cupon | None
    pago: Pago

import base64
import requests
from typing import Dict, Any, Optional
from shipping.models import ShippingConfig
from products.models import Producto,Variante
from cart.types import CarritoDict
from cart.utils import obtener_total

class ZipnovaService:
    BASE_URL = "https://api.zipnova.com.ar/v2"

    def __init__(self, config: ShippingConfig):
        self.config = config
        self.creds:dict = config.credentials

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Determina dinámicamente qué headers enviar según la config de la DB.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # > FEATURE -> Eliminar auth_type
        if self.config.auth_type == 'basic':
            user = self.creds.get('api_key', '')
            secret = self.creds.get('api_secret', '')
            token_str = f"{user}:{secret}"
            b64_token = base64.b64encode(token_str.encode()).decode()
            headers["Authorization"] = f"Basic {b64_token}"

        # !! Quizas no se implemente
        # elif self.config.auth_type == 'oauth':
        #     token = self.creds.get('access_token', '')
        #     headers["Authorization"] = f"Bearer {token}"

        return headers

    # def cotizar(self, cp_destino: str, peso: float, dimensiones: Dict[str, int],obj: Producto | Variante, valor_declarado: float = 10000) -> Dict[str, Any]:
    def cotizar(self, carrito: list[CarritoDict], cuidad: str, estado: str, codigo_postal: str) -> Dict[str, Any]:
        endpoint = f"{self.BASE_URL}/shipments/quote"
        declared_value, _, _ = obtener_total(carrito)

        payload = {
            "account_id": self.creds.get('account_id'),
            "origin_id": self.creds.get('origin_id'),
            "declared_value": float(declared_value),
            "items": [
                {
                    "sku": item['sku'],
                    "weight": 200,
                    "height": 10,
                    "width": 5,
                    "length": 10,
                    "description": f"{item['nombre']}, {item['variante']}",
                    "classification_id": 1
                } for item in carrito
            ],
            "destination": {
                "city": cuidad,
                "state": estado,
                "zipcode": codigo_postal
            }
        }

        try:
            response_raw = requests.post(
                endpoint, 
                json=payload, 
                headers=self._get_auth_headers()
            )

            response_raw.raise_for_status()
            response_dict = response_raw.json()
            
            response_clean = []
            
            for cotizacion in  response_dict.get('all_results', []):
                if cotizacion['selectable'] != True:
                    continue 
                
                opcion = {
                    'carrier_name': cotizacion['carrier']['name'],
                    'carrier_logo': cotizacion['carrier']['logo'],
                    'service_name': cotizacion['service_type']['name'],
                    'service_code': cotizacion['service_type']['code'],
                    'tags': cotizacion['tags'],
                    
                    'precio': cotizacion['amounts']['price_incl_tax'], 
                    'fecha_entrega': cotizacion['delivery_time']['estimated_delivery'], 
                    
                    'carrier_id': cotizacion['carrier']['id'],
                    'logistic_type': cotizacion['logistic_type'],
                    'id_interno_cotizacion': cotizacion['rate']['id']
                }
                
                if cotizacion['service_type']['code'] == 'pickup_point':
                    sucursales = []
                    for punto in cotizacion.get('pickup_points', []):
                        sucursales.append({
                            'point_id': punto['point_id'],
                            'nombre': punto['description'],
                            'direccion': f"{punto['location']['street']} {punto['location']['street_number']}",
                            'lat': punto['location']['geolocation']['lat'],
                            'lng': punto['location']['geolocation']['lng']
                        })
                    opcion['sucursales'] = sucursales
                    opcion['requiere_eleccion_sucursal'] = True
                else:
                    opcion['requiere_eleccion_sucursal'] = False

                response_clean.append(opcion)

            response_clean.sort(key=lambda x: x['precio'])
            return response_clean
        
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión: {e}")
            return {}
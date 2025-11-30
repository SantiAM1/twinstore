from typing import TypedDict, Optional, Dict, Any
from django.db.models import QuerySet

class GridContext(TypedDict):
    productos: QuerySet
    title: str
    categoria: Optional[Any]
    sub_categorias: Optional[QuerySet]
    sub_categoria_obj: Optional[Any]
    marca: Optional[Any]
    evento: Optional[Any]
    marcas: QuerySet
    atributos: Dict[str, Any]
    filtro: str
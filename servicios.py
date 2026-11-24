import time

import requests
from flask import Blueprint

bp = Blueprint("servicios", __name__)

_cache = {"datos": None, "hora": 0}


def obtener_dolar():
    
    try:
        respuesta = requests.get("https://dolarapi.com/v1/dolares/oficial", timeout=5)
        respuesta.raise_for_status()
        datos = respuesta.json()
        return {"compra": datos["compra"], "venta": datos["venta"]}
    except (requests.RequestException, KeyError, ValueError):
        return None


def dolar_cacheado():
    
    ahora = time.time()
    if ahora - _cache["hora"] > 600:
        _cache["datos"] = obtener_dolar()
        _cache["hora"] = ahora
    return _cache["datos"]


@bp.app_context_processor
def inyectar_dolar():
    return {"dolar": dolar_cacheado()}
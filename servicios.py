import requests

def obtener_dolar():
    """Devuelve la cotización del dólar oficial, o None si la API falla."""
    try:
        respuesta = requests.get("https://dolarapi.com/v1/dolares/oficial", timeout=5)
        respuesta.raise_for_status()
        datos = respuesta.json()
        return {"compra": datos["compra"], "venta": datos["venta"]}
    except (requests.RequestException, KeyError, ValueError):
        return None
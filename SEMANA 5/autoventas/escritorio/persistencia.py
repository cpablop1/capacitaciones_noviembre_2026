"""Persistencia local en JSON (RNF-03).

Estructura del archivo:
    {"version": 1, "autos": [...], "clientes": [...], "ventas": [...]}

La escritura es atómica: se escribe a un archivo temporal en la misma carpeta
y luego se reemplaza el original, de modo que un cierre inesperado nunca deja
el archivo a medias. Si el archivo está dañado se respalda y se inicia vacío.
"""

import json
import os
import shutil
import tempfile
from datetime import datetime

VERSION_FORMATO = 1


def datos_vacios():
    return {"version": VERSION_FORMATO, "autos": [], "clientes": [], "ventas": []}


def cargar(ruta):
    """Devuelve (datos, aviso). `aviso` es None o un mensaje para mostrar al usuario."""
    if not os.path.exists(ruta):
        return datos_vacios(), None
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
        if not isinstance(datos, dict):
            raise ValueError("el contenido no es un objeto JSON")
        for clave in ("autos", "clientes", "ventas"):
            if not isinstance(datos.get(clave, []), list):
                raise ValueError(f"«{clave}» no es una lista")
            datos.setdefault(clave, [])
        datos["version"] = VERSION_FORMATO
        return datos, None
    except (OSError, ValueError) as error:  # json.JSONDecodeError hereda de ValueError
        respaldo = _respaldar(ruta)
        aviso = (f"No se pudo leer el archivo de datos ({error}).\n"
                 "Se inició con datos vacíos.")
        if respaldo:
            aviso += f"\nEl archivo original se respaldó como:\n{respaldo}"
        return datos_vacios(), aviso


def guardar(ruta, datos):
    carpeta = os.path.dirname(os.path.abspath(ruta))
    os.makedirs(carpeta, exist_ok=True)
    descriptor, temporal = tempfile.mkstemp(prefix=".autoventas_", suffix=".tmp", dir=carpeta)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
        os.replace(temporal, ruta)
    except BaseException:
        if os.path.exists(temporal):
            os.remove(temporal)
        raise


def _respaldar(ruta):
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = f"{ruta}.danado_{marca}"
    try:
        shutil.copy2(ruta, destino)
        return destino
    except OSError:
        return None

"""Punto de entrada de AutoVentas (versión de escritorio).

Ejecutar desde cualquier carpeta:
    python main.py

Los datos se guardan en datos/autoventas.json, junto a este archivo.
"""

import sys
from pathlib import Path

import persistencia
from interfaz import AplicacionAutoVentas
from logica import AutoVentas

RUTA_DATOS = Path(__file__).resolve().parent / "datos" / "autoventas.json"


def _texto_nitido_en_windows():
    """Evita que Windows escale la ventana como imagen (texto borroso en pantallas HiDPI)."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass


def main():
    _texto_nitido_en_windows()
    datos, aviso = persistencia.cargar(RUTA_DATOS)
    servicio = AutoVentas(datos, al_guardar=lambda d: persistencia.guardar(RUTA_DATOS, d))
    app = AplicacionAutoVentas(servicio, aviso_carga=aviso)
    app.mainloop()


if __name__ == "__main__":
    main()

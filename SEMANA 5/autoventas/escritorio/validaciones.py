"""Validaciones de datos de entrada de AutoVentas (RNF-02).

Funciones puras, sin dependencia de tkinter ni de archivos. Cada función
recibe el texto tal como lo escribió el usuario y devuelve el valor ya
convertido, o lanza ErrorValidacion con un mensaje claro en español.
"""

import re
from datetime import date

ANIO_MINIMO = 1990
DESCUENTO_MAXIMO = 15.0          # porcentaje máximo de descuento (HU-04)
PRECIO_MAXIMO = 10_000_000.0     # tope razonable para evitar errores de digitación
KILOMETRAJE_MAXIMO = 2_000_000

# usuario@dominio.ext — sin espacios, un solo "@" y extensión de 2+ letras.
_PATRON_CORREO = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
# Teléfono: dígitos con espacios, guiones o "+" inicial; entre 8 y 15 dígitos.
_PATRON_TELEFONO = re.compile(r"^\+?[0-9][0-9 -]*$")
# Documento (DPI, pasaporte, NIT...): letras, dígitos y guiones.
_PATRON_DOCUMENTO = re.compile(r"^[A-Za-z0-9-]{5,20}$")
# Nombres de personas: letras (con tildes), espacios, punto, apóstrofo y guion.
_PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]+$")


class ErrorValidacion(ValueError):
    """Error de datos de entrada. `errores` contiene uno o varios mensajes."""

    def __init__(self, errores):
        if isinstance(errores, str):
            errores = [errores]
        self.errores = list(errores)
        super().__init__("\n".join(self.errores))


def anio_actual():
    return date.today().year


def _limpiar(texto):
    return str(texto if texto is not None else "").strip()


def _numero(texto):
    """Convierte '125,000.50' o 'Q 125000' en float. Lanza ValueError si no es número."""
    limpio = _limpiar(texto).upper().removeprefix("Q").replace(",", "").replace(" ", "")
    if not limpio:
        raise ValueError("vacío")
    valor = float(limpio)
    if valor != valor or valor in (float("inf"), float("-inf")):  # NaN o infinito
        raise ValueError("no finito")
    return valor


def texto_obligatorio(texto, campo, minimo=1, maximo=60):
    valor = " ".join(_limpiar(texto).split())  # colapsa espacios repetidos
    if not valor:
        raise ErrorValidacion(f"El campo «{campo}» es obligatorio.")
    if len(valor) < minimo:
        raise ErrorValidacion(f"«{campo}» debe tener al menos {minimo} caracteres.")
    if len(valor) > maximo:
        raise ErrorValidacion(f"«{campo}» no puede superar {maximo} caracteres.")
    return valor


def validar_anio(texto):
    if not _limpiar(texto):
        raise ErrorValidacion("El campo «Año» es obligatorio.")
    try:
        anio = int(_limpiar(texto))
    except ValueError:
        raise ErrorValidacion("El año debe ser un número entero (ejemplo: 2020).") from None
    tope = anio_actual()
    if not ANIO_MINIMO <= anio <= tope:
        raise ErrorValidacion(f"El año debe estar entre {ANIO_MINIMO} y {tope}.")
    return anio


def validar_precio(texto):
    if not _limpiar(texto):
        raise ErrorValidacion("El campo «Precio» es obligatorio.")
    try:
        precio = _numero(texto)
    except ValueError:
        raise ErrorValidacion("El precio debe ser un número (ejemplo: 85000 o 85,000.50).") from None
    if precio <= 0:
        raise ErrorValidacion("El precio debe ser mayor que cero.")
    if precio > PRECIO_MAXIMO:
        raise ErrorValidacion(f"El precio no puede superar Q {PRECIO_MAXIMO:,.2f}.")
    return round(precio, 2)


def validar_kilometraje(texto):
    if not _limpiar(texto):
        raise ErrorValidacion("El campo «Kilometraje» es obligatorio.")
    try:
        km = _numero(texto)
    except ValueError:
        raise ErrorValidacion("El kilometraje debe ser un número entero (ejemplo: 45000).") from None
    if km != int(km):
        raise ErrorValidacion("El kilometraje debe ser un número entero, sin decimales.")
    if km < 0:
        raise ErrorValidacion("El kilometraje no puede ser negativo.")
    if km > KILOMETRAJE_MAXIMO:
        raise ErrorValidacion(f"El kilometraje no puede superar {KILOMETRAJE_MAXIMO:,} km.")
    return int(km)


def validar_nombre_persona(texto):
    nombre = texto_obligatorio(texto, "Nombre", minimo=3, maximo=80)
    if not _PATRON_NOMBRE.match(nombre):
        raise ErrorValidacion("El nombre solo puede contener letras, espacios, puntos y guiones.")
    return nombre


def validar_telefono(texto):
    telefono = texto_obligatorio(texto, "Teléfono", maximo=20)
    digitos = re.sub(r"\D", "", telefono)
    if not _PATRON_TELEFONO.match(telefono) or not 8 <= len(digitos) <= 15:
        raise ErrorValidacion("El teléfono debe tener entre 8 y 15 dígitos (ejemplo: 5555-1234).")
    return telefono


def validar_correo(texto):
    correo = _limpiar(texto)
    if not correo:
        raise ErrorValidacion("El campo «Correo» es obligatorio.")
    if len(correo) > 100 or not _PATRON_CORREO.match(correo) or ".." in correo:
        raise ErrorValidacion("El correo no tiene un formato válido (ejemplo: nombre@dominio.com).")
    return correo.lower()


def validar_documento(texto):
    documento = _limpiar(texto).upper()
    if not documento:
        raise ErrorValidacion("El campo «Documento» es obligatorio.")
    if not _PATRON_DOCUMENTO.match(documento):
        raise ErrorValidacion(
            "El documento debe tener de 5 a 20 caracteres: letras, números o guiones.")
    return documento


def validar_porcentaje_descuento(texto):
    """Descuento expresado en porcentaje, de 0 a 15 (HU-04, CP-04). Vacío = 0."""
    if not _limpiar(texto):
        return 0.0
    try:
        porcentaje = _numero(_limpiar(texto).rstrip("%"))
    except ValueError:
        raise ErrorValidacion("El descuento debe ser un número entre 0 y 15.") from None
    if porcentaje < 0:
        raise ErrorValidacion("El descuento no puede ser negativo.")
    if porcentaje > DESCUENTO_MAXIMO:
        raise ErrorValidacion(f"El descuento no puede superar el {DESCUENTO_MAXIMO:g} %.")
    return porcentaje


def recopilar(validaciones):
    """Ejecuta varias validaciones y reúne todos los errores en uno solo.

    `validaciones` es una lista de (clave, función, argumento). Devuelve un
    dict {clave: valor validado} o lanza ErrorValidacion con todos los mensajes,
    para que el usuario corrija el formulario completo de una sola vez.
    """
    valores, errores = {}, []
    for clave, funcion, argumento in validaciones:
        try:
            valores[clave] = funcion(argumento)
        except ErrorValidacion as error:
            errores.extend(error.errores)
    if errores:
        raise ErrorValidacion(errores)
    return valores

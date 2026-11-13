"""Reglas de negocio de AutoVentas (RNF-04: sin dependencia de la interfaz).

La clase AutoVentas guarda el estado en memoria (autos, clientes y ventas) y
ofrece las operaciones de los requerimientos RF-01 a RF-06. Cada operación que
modifica datos se ejecuta como una transacción: si el guardado falla, los
datos en memoria vuelven a como estaban.

La persistencia se inyecta con `al_guardar` (una función que recibe los datos),
lo que permite probar toda la lógica sin tocar archivos.
"""

import copy
import unicodedata
from contextlib import contextmanager
from datetime import datetime

import validaciones as v
from validaciones import ErrorValidacion

DISPONIBLE = "Disponible"
VENDIDO = "Vendido"
ESTADOS_AUTO = (DISPONIBLE, VENDIDO)
TODOS = "Todos"


class ErrorNegocio(ErrorValidacion):
    """Operación válida en forma pero no permitida por una regla de negocio."""


# --------------------------------------------------------------------------
# Utilidades de formato (compartidas por la interfaz)
# --------------------------------------------------------------------------
def formato_moneda(valor):
    return f"Q {valor:,.2f}"


def formato_km(valor):
    return f"{valor:,} km"


def descripcion_auto(auto):
    return f"{auto['marca']} {auto['modelo']} {auto['anio']}"


def normalizar(texto):
    """Minúsculas y sin tildes, para búsquedas tolerantes ('Peugeót' = 'peugeot')."""
    descompuesto = unicodedata.normalize("NFD", str(texto).casefold())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn").strip()


def coincide(consulta, *campos):
    """True si cada palabra de la consulta aparece en alguno de los campos.

    Ignora mayúsculas, tildes y el orden: 'corolla toyota' encuentra
    'Toyota Corolla 2020'. Una consulta vacía coincide con todo.
    """
    texto = normalizar(" ".join(str(campo) for campo in campos))
    return all(palabra in texto for palabra in normalizar(consulta).split())


def _clave_documento(documento):
    """'1234-56789-0101' y '1234567890101' son el mismo documento."""
    return documento.replace("-", "").upper()


# --------------------------------------------------------------------------
# Servicio principal
# --------------------------------------------------------------------------
class AutoVentas:
    def __init__(self, datos=None, al_guardar=None):
        self.datos = datos if datos is not None else {"autos": [], "clientes": [], "ventas": []}
        for clave in ("autos", "clientes", "ventas"):
            self.datos.setdefault(clave, [])
        self._al_guardar = al_guardar
        self._iniciar_secuencias()

    # ---- infraestructura -------------------------------------------------
    def _iniciar_secuencias(self):
        """Los id nunca se reutilizan, aunque se elimine el último registro."""
        secuencias = self.datos.setdefault("secuencias", {})
        for clave in ("autos", "clientes", "ventas"):
            mayor = max((r["id"] for r in self.datos[clave]), default=0)
            secuencias[clave] = max(secuencias.get(clave, 0), mayor)

    def _nuevo_id(self, coleccion):
        self.datos["secuencias"][coleccion] += 1
        return self.datos["secuencias"][coleccion]

    @contextmanager
    def _transaccion(self):
        respaldo = copy.deepcopy(self.datos)
        try:
            yield
            if self._al_guardar:
                self._al_guardar(self.datos)
        except BaseException:
            self.datos.clear()
            self.datos.update(respaldo)
            raise

    @staticmethod
    def _buscar(coleccion, id_registro, nombre):
        for registro in coleccion:
            if registro["id"] == id_registro:
                return registro
        raise ErrorNegocio(f"No existe {nombre} con id {id_registro}.")

    # ---- autos (RF-01, RF-02) -------------------------------------------
    @property
    def autos(self):
        return self.datos["autos"]

    def obtener_auto(self, id_auto):
        return self._buscar(self.autos, id_auto, "un auto")

    @staticmethod
    def _validar_auto(marca, modelo, anio, precio, kilometraje):
        return v.recopilar([
            ("marca", lambda t: v.texto_obligatorio(t, "Marca", maximo=40), marca),
            ("modelo", lambda t: v.texto_obligatorio(t, "Modelo", maximo=40), modelo),
            ("anio", v.validar_anio, anio),
            ("precio", v.validar_precio, precio),
            ("kilometraje", v.validar_kilometraje, kilometraje),
        ])

    def registrar_auto(self, marca, modelo, anio, precio, kilometraje):
        """HU-01: todos los campos obligatorios; el auto nace 'Disponible'."""
        valores = self._validar_auto(marca, modelo, anio, precio, kilometraje)
        with self._transaccion():
            auto = {"id": self._nuevo_id("autos"), **valores, "estado": DISPONIBLE}
            self.autos.append(auto)
        return auto

    def editar_auto(self, id_auto, marca, modelo, anio, precio, kilometraje):
        auto = self.obtener_auto(id_auto)
        if auto["estado"] == VENDIDO:
            raise ErrorNegocio("No se puede editar un auto vendido: forma parte del historial de ventas.")
        valores = self._validar_auto(marca, modelo, anio, precio, kilometraje)
        with self._transaccion():
            self.obtener_auto(id_auto).update(valores)
        return self.obtener_auto(id_auto)

    def eliminar_auto(self, id_auto):
        auto = self.obtener_auto(id_auto)
        if auto["estado"] == VENDIDO:
            raise ErrorNegocio("No se puede eliminar un auto vendido: forma parte del historial de ventas.")
        with self._transaccion():
            self.autos.remove(self.obtener_auto(id_auto))

    def marcas(self):
        return sorted({a["marca"] for a in self.autos}, key=normalizar)

    def filtrar_autos(self, texto="", marca="", anio="", precio_min="", precio_max="", estado=TODOS):
        """RF-02 / HU-02. Devuelve la lista filtrada (vacía si no hay resultados).

        Lanza ErrorValidacion si algún filtro numérico no es válido.
        """
        errores = []
        anio_filtro = minimo = maximo = None
        if str(anio).strip():
            try:
                anio_filtro = int(str(anio).strip())
            except ValueError:
                errores.append("El filtro de año debe ser un número entero.")
        for etiqueta, crudo in (("mínimo", precio_min), ("máximo", precio_max)):
            if not str(crudo).strip():
                continue
            try:
                valor = v._numero(crudo)
                if valor < 0:
                    raise ValueError
            except ValueError:
                errores.append(f"El precio {etiqueta} debe ser un número mayor o igual a cero.")
                continue
            if etiqueta == "mínimo":
                minimo = valor
            else:
                maximo = valor
        if minimo is not None and maximo is not None and minimo > maximo:
            errores.append("El precio mínimo no puede ser mayor que el precio máximo.")
        if errores:
            raise ErrorValidacion(errores)

        marca_n = normalizar(marca)
        resultado = []
        for auto in self.autos:
            if not coincide(texto, auto["marca"], auto["modelo"]):
                continue
            if marca_n and marca_n not in normalizar(auto["marca"]):
                continue
            if anio_filtro is not None and auto["anio"] != anio_filtro:
                continue
            if minimo is not None and auto["precio"] < minimo:
                continue
            if maximo is not None and auto["precio"] > maximo:
                continue
            if estado and estado != TODOS and auto["estado"] != estado:
                continue
            resultado.append(auto)
        return resultado

    def autos_disponibles(self):
        return [a for a in self.autos if a["estado"] == DISPONIBLE]

    def buscar_autos_disponibles(self, texto=""):
        """Autos que se pueden vender, filtrados por id, marca, modelo o año (para Ventas)."""
        encontrados = [a for a in self.autos_disponibles()
                       if coincide(texto, f"#{a['id']}", a["marca"], a["modelo"], a["anio"])]
        return sorted(encontrados, key=lambda a: (normalizar(a["marca"]), normalizar(a["modelo"]), a["id"]))

    # ---- clientes (RF-03) -----------------------------------------------
    @property
    def clientes(self):
        return self.datos["clientes"]

    def obtener_cliente(self, id_cliente):
        return self._buscar(self.clientes, id_cliente, "un cliente")

    def _validar_cliente(self, nombre, telefono, correo, documento, excluir_id=None):
        valores = v.recopilar([
            ("nombre", v.validar_nombre_persona, nombre),
            ("telefono", v.validar_telefono, telefono),
            ("correo", v.validar_correo, correo),
            ("documento", v.validar_documento, documento),
        ])
        clave = _clave_documento(valores["documento"])
        for cliente in self.clientes:
            if cliente["id"] != excluir_id and _clave_documento(cliente["documento"]) == clave:
                raise ErrorNegocio(
                    f"Ya existe un cliente con el documento {valores['documento']} ({cliente['nombre']}).")
        return valores

    def registrar_cliente(self, nombre, telefono, correo, documento):
        """HU-03: correo con formato válido y documento sin duplicados."""
        valores = self._validar_cliente(nombre, telefono, correo, documento)
        with self._transaccion():
            cliente = {"id": self._nuevo_id("clientes"), **valores}
            self.clientes.append(cliente)
        return cliente

    def editar_cliente(self, id_cliente, nombre, telefono, correo, documento):
        self.obtener_cliente(id_cliente)
        valores = self._validar_cliente(nombre, telefono, correo, documento, excluir_id=id_cliente)
        with self._transaccion():
            self.obtener_cliente(id_cliente).update(valores)
        return self.obtener_cliente(id_cliente)

    def eliminar_cliente(self, id_cliente):
        self.obtener_cliente(id_cliente)
        compras = sum(1 for venta in self.ventas if venta["id_cliente"] == id_cliente)
        if compras:
            raise ErrorNegocio(
                f"No se puede eliminar el cliente: tiene {compras} venta(s) en el historial.")
        with self._transaccion():
            self.clientes.remove(self.obtener_cliente(id_cliente))

    def buscar_clientes(self, texto=""):
        """Clientes ordenados por id (menor a mayor), filtrados por nombre, documento, correo o teléfono."""
        encontrados = [c for c in self.clientes
                       if coincide(texto, c["nombre"], c["documento"], c["correo"], c["telefono"])]
        return sorted(encontrados, key=lambda c: c["id"])

    # ---- ventas (RF-04, RF-05) ------------------------------------------
    @property
    def ventas(self):
        return self.datos["ventas"]

    def calcular_venta(self, id_auto, porcentaje_descuento):
        """Vista previa del total: total = precio − descuento (máximo 15 %)."""
        auto = self.obtener_auto(id_auto)
        porcentaje = v.validar_porcentaje_descuento(porcentaje_descuento)
        descuento = round(auto["precio"] * porcentaje / 100, 2)
        return {
            "precio": auto["precio"],
            "porcentaje_descuento": porcentaje,
            "descuento": descuento,
            "total": round(auto["precio"] - descuento, 2),
        }

    def registrar_venta(self, id_cliente, id_auto, porcentaje_descuento, fecha=None):
        """HU-04: solo autos 'Disponible'; el auto pasa a 'Vendido' al confirmar."""
        errores = []
        if id_cliente is None:
            errores.append("Seleccione un cliente.")
        if id_auto is None:
            errores.append("Seleccione un auto.")
        if errores:
            raise ErrorValidacion(errores)
        self.obtener_cliente(id_cliente)
        auto = self.obtener_auto(id_auto)
        if auto["estado"] != DISPONIBLE:
            raise ErrorNegocio(
                f"El auto {descripcion_auto(auto)} no está disponible (estado: {auto['estado']}).")
        calculo = self.calcular_venta(id_auto, porcentaje_descuento)
        with self._transaccion():
            venta = {
                "id": self._nuevo_id("ventas"),
                "id_auto": id_auto,
                "id_cliente": id_cliente,
                "fecha": (fecha or datetime.now()).strftime("%Y-%m-%d %H:%M"),
                **calculo,
            }
            self.ventas.append(venta)
            self.obtener_auto(id_auto)["estado"] = VENDIDO
        return venta

    def historial_ventas(self):
        """RF-05: ventas de la más reciente a la más antigua, con datos de cliente y auto."""
        historial = []
        for venta in self.ventas:
            auto = next((a for a in self.autos if a["id"] == venta["id_auto"]), None)
            cliente = next((c for c in self.clientes if c["id"] == venta["id_cliente"]), None)
            historial.append({
                **venta,
                "auto": descripcion_auto(auto) if auto else f"Auto #{venta['id_auto']}",
                "cliente": cliente["nombre"] if cliente else f"Cliente #{venta['id_cliente']}",
                "documento": cliente["documento"] if cliente else "",
            })
        historial.sort(key=lambda h: (h["fecha"], h["id"]), reverse=True)
        return historial

    # ---- resumen (RF-06, HU-05) -----------------------------------------
    def resumen(self):
        disponibles = self.autos_disponibles()
        return {
            "autos_disponibles": len(disponibles),
            "autos_vendidos": sum(1 for a in self.autos if a["estado"] == VENDIDO),
            "total_vendido": round(sum(venta["total"] for venta in self.ventas), 2),
            "cantidad_ventas": len(self.ventas),
            "clientes": len(self.clientes),
            "valor_inventario": round(sum(a["precio"] for a in disponibles), 2),
            "descuentos_otorgados": round(sum(venta["descuento"] for venta in self.ventas), 2),
        }

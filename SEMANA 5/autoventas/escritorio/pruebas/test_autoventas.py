"""Pruebas unitarias de AutoVentas (versión de escritorio).

Ejecutar desde la carpeta `escritorio`:
    python -m unittest discover -s pruebas -t . -v

Incluye los casos mínimos del instructivo (CP-01 a CP-06), los criterios de
aceptación de las historias de usuario y pruebas de persistencia.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime

import persistencia
from logica import DISPONIBLE, VENDIDO, AutoVentas, ErrorNegocio, coincide
from validaciones import ErrorValidacion, anio_actual


def servicio_con_datos():
    servicio = AutoVentas()
    servicio.registrar_auto("Toyota", "Corolla", "2020", "150000", "45000")
    servicio.registrar_auto("Honda", "Civic", "2019", "135000", "60000")
    servicio.registrar_auto("Toyota", "Hilux", "2022", "310000", "20000")
    servicio.registrar_cliente("María López", "5555-1234", "maria@correo.com", "1234567890101")
    return servicio


class CasosDePruebaMinimos(unittest.TestCase):
    """Casos de prueba exigidos por el instructivo (sección 6)."""

    def setUp(self):
        self.servicio = servicio_con_datos()

    def test_cp01_auto_con_precio_negativo_es_rechazado(self):
        with self.assertRaises(ErrorValidacion) as contexto:
            self.servicio.registrar_auto("Kia", "Rio", "2021", "-5000", "1000")
        self.assertIn("El precio debe ser mayor que cero.", contexto.exception.errores)
        self.assertEqual(len(self.servicio.autos), 3)

    def test_cp02_cliente_con_correo_invalido_es_rechazado(self):
        with self.assertRaises(ErrorValidacion) as contexto:
            self.servicio.registrar_cliente("Juan Pérez", "5555-0000", "abc", "9876543210101")
        self.assertTrue(any("correo" in e.lower() for e in contexto.exception.errores))
        self.assertEqual(len(self.servicio.clientes), 1)

    def test_cp03_vender_auto_vendido_esta_bloqueado(self):
        self.servicio.registrar_venta(1, 1, "0")
        self.servicio.registrar_cliente("Juan Pérez", "5555-0000", "juan@correo.com", "9876543210101")
        with self.assertRaises(ErrorNegocio) as contexto:
            self.servicio.registrar_venta(2, 1, "0")
        self.assertIn("no está disponible", str(contexto.exception))
        self.assertEqual(len(self.servicio.ventas), 1)

    def test_cp04_descuento_de_20_por_ciento_es_rechazado(self):
        with self.assertRaises(ErrorValidacion) as contexto:
            self.servicio.registrar_venta(1, 1, "20")
        self.assertIn("15", str(contexto.exception))
        self.assertEqual(self.servicio.obtener_auto(1)["estado"], DISPONIBLE)
        self.assertEqual(self.servicio.ventas, [])

    def test_cp05_venta_correcta(self):
        venta = self.servicio.registrar_venta(1, 1, "10")
        self.assertEqual(self.servicio.obtener_auto(1)["estado"], VENDIDO)
        self.assertEqual(venta["descuento"], 15000.00)
        self.assertEqual(venta["total"], 135000.00)  # 150,000 − 10 %
        self.assertEqual(self.servicio.historial_ventas()[0]["id"], venta["id"])

    def test_cp06_filtrar_por_marca_inexistente_no_da_resultados(self):
        self.assertEqual(self.servicio.filtrar_autos(marca="Ferrari"), [])


class HistoriaAutos(unittest.TestCase):
    """HU-01 y RF-01."""

    def setUp(self):
        self.servicio = AutoVentas()

    def test_todos_los_campos_son_obligatorios_y_se_informan_juntos(self):
        with self.assertRaises(ErrorValidacion) as contexto:
            self.servicio.registrar_auto("", " ", "", "", "")
        self.assertEqual(len(contexto.exception.errores), 5)

    def test_anio_fuera_de_rango(self):
        for anio in ("1989", str(anio_actual() + 1), "dos mil"):
            with self.subTest(anio=anio), self.assertRaises(ErrorValidacion):
                self.servicio.registrar_auto("Kia", "Rio", anio, "90000", "100")

    def test_limites_validos_de_anio(self):
        self.servicio.registrar_auto("Kia", "Rio", "1990", "90000", "100")
        self.servicio.registrar_auto("Kia", "Rio", str(anio_actual()), "90000", "100")
        self.assertEqual(len(self.servicio.autos), 2)

    def test_precio_cero_texto_y_kilometraje_negativo(self):
        for precio, km in (("0", "10"), ("abc", "10"), ("1000", "-1"), ("1000", "1.5")):
            with self.subTest(precio=precio, km=km), self.assertRaises(ErrorValidacion):
                self.servicio.registrar_auto("Kia", "Rio", "2020", precio, km)

    def test_auto_nuevo_queda_disponible_y_normalizado(self):
        auto = self.servicio.registrar_auto("  Mazda ", "CX-5", "2021", "Q 215,000.50", "12,000")
        self.assertEqual(auto["estado"], DISPONIBLE)
        self.assertEqual(auto["marca"], "Mazda")
        self.assertEqual(auto["precio"], 215000.50)
        self.assertEqual(auto["kilometraje"], 12000)

    def test_editar_y_eliminar(self):
        auto = self.servicio.registrar_auto("Kia", "Rio", "2020", "90000", "100")
        self.servicio.editar_auto(auto["id"], "Kia", "Rio LX", "2021", "95000", "200")
        self.assertEqual(self.servicio.obtener_auto(auto["id"])["modelo"], "Rio LX")
        self.servicio.eliminar_auto(auto["id"])
        self.assertEqual(self.servicio.autos, [])

    def test_auto_vendido_no_se_edita_ni_elimina(self):
        servicio = servicio_con_datos()
        servicio.registrar_venta(1, 1, "0")
        with self.assertRaises(ErrorNegocio):
            servicio.editar_auto(1, "Toyota", "Corolla", "2020", "1", "1")
        with self.assertRaises(ErrorNegocio):
            servicio.eliminar_auto(1)

    def test_los_id_no_se_reutilizan(self):
        primero = self.servicio.registrar_auto("Kia", "Rio", "2020", "90000", "100")
        self.servicio.eliminar_auto(primero["id"])
        segundo = self.servicio.registrar_auto("Kia", "Rio", "2020", "90000", "100")
        self.assertNotEqual(primero["id"], segundo["id"])


class HistoriaBusqueda(unittest.TestCase):
    """HU-02 y RF-02."""

    def setUp(self):
        self.servicio = servicio_con_datos()

    def ids(self, **filtros):
        return [a["id"] for a in self.servicio.filtrar_autos(**filtros)]

    def test_filtro_por_marca_ignora_mayusculas_y_tildes(self):
        self.assertEqual(self.ids(marca="toyóta"), [1, 3])

    def test_filtro_por_rango_de_precio(self):
        self.assertEqual(self.ids(precio_min="140000", precio_max="200000"), [1])
        self.assertEqual(self.ids(precio_min="300000"), [3])

    def test_filtro_por_anio_y_busqueda_por_modelo(self):
        self.assertEqual(self.ids(anio="2019"), [2])
        self.assertEqual(self.ids(texto="hilux"), [3])

    def test_filtro_por_estado(self):
        self.servicio.registrar_venta(1, 2, "0")
        self.assertEqual(self.ids(estado=VENDIDO), [2])
        self.assertEqual(self.ids(estado=DISPONIBLE), [1, 3])

    def test_rango_invertido_o_no_numerico_es_error(self):
        with self.assertRaises(ErrorValidacion):
            self.servicio.filtrar_autos(precio_min="200000", precio_max="100")
        with self.assertRaises(ErrorValidacion):
            self.servicio.filtrar_autos(precio_min="barato")


class HistoriaClientes(unittest.TestCase):
    """HU-03 y RF-03."""

    def setUp(self):
        self.servicio = servicio_con_datos()

    def test_correos_validos_e_invalidos(self):
        for correo in ("abc", "a@b", "a@@b.com", "a b@c.com", "a@b..com", "@dominio.com"):
            with self.subTest(correo=correo), self.assertRaises(ErrorValidacion):
                self.servicio.registrar_cliente("Ana Ruiz", "55551111", correo, f"DOC{len(correo)}X")
        cliente = self.servicio.registrar_cliente("Ana Ruiz", "55551111", "Ana.Ruiz@Mail.com", "P12345")
        self.assertEqual(cliente["correo"], "ana.ruiz@mail.com")

    def test_documento_duplicado_no_se_permite(self):
        for documento in ("1234567890101", "1234-56789-0101", " 1234567890101 "):
            with self.subTest(documento=documento), self.assertRaises(ErrorNegocio):
                self.servicio.registrar_cliente("Otra Persona", "55550000", "otra@correo.com", documento)

    def test_editar_cliente_conserva_su_propio_documento(self):
        self.servicio.editar_cliente(1, "María López de Paz", "5555-1234", "maria@correo.com",
                                     "1234567890101")
        self.assertEqual(self.servicio.obtener_cliente(1)["nombre"], "María López de Paz")

    def test_cliente_con_ventas_no_se_elimina(self):
        self.servicio.registrar_venta(1, 1, "0")
        with self.assertRaises(ErrorNegocio):
            self.servicio.eliminar_cliente(1)

    def test_telefono_invalido(self):
        for telefono in ("123", "telefono", "5555-12a4"):
            with self.subTest(telefono=telefono), self.assertRaises(ErrorValidacion):
                self.servicio.registrar_cliente("Ana Ruiz", telefono, "ana@correo.com", "P99999")


class HistoriaVentas(unittest.TestCase):
    """HU-04 y RF-04 / RF-05."""

    def setUp(self):
        self.servicio = servicio_con_datos()

    def test_descuento_maximo_15_por_ciento_es_valido(self):
        venta = self.servicio.registrar_venta(1, 2, "15")
        self.assertEqual(venta["descuento"], 20250.00)
        self.assertEqual(venta["total"], 114750.00)

    def test_descuento_vacio_es_cero_y_negativo_es_error(self):
        self.assertEqual(self.servicio.calcular_venta(1, "")["total"], 150000.00)
        with self.assertRaises(ErrorValidacion):
            self.servicio.calcular_venta(1, "-1")

    def test_venta_sin_cliente_o_auto(self):
        with self.assertRaises(ErrorValidacion) as contexto:
            self.servicio.registrar_venta(None, None, "0")
        self.assertEqual(len(contexto.exception.errores), 2)

    def test_historial_ordenado_del_mas_reciente(self):
        self.servicio.registrar_venta(1, 1, "0", fecha=datetime(2026, 11, 1, 10, 0))
        self.servicio.registrar_venta(1, 2, "5", fecha=datetime(2026, 11, 5, 9, 30))
        historial = self.servicio.historial_ventas()
        self.assertEqual([h["auto"] for h in historial], ["Honda Civic 2019", "Toyota Corolla 2020"])
        self.assertEqual(historial[0]["cliente"], "María López")


class BuscadoresDeVenta(unittest.TestCase):
    """Iteración 1: clientes ordenados por id y buscadores de cliente y auto en Ventas."""

    def setUp(self):
        self.servicio = servicio_con_datos()
        self.servicio.registrar_cliente("Carlos Méndez", "4444-9876", "carlos@empresa.gt", "2345678900101")
        self.servicio.registrar_cliente("Ana Ruiz", "3333-4444", "ana@mail.com", "P1234567")

    def test_coincide_por_palabras_sin_orden_ni_tildes(self):
        self.assertTrue(coincide("corolla TOYOTA", "Toyota", "Corolla", 2020))
        self.assertTrue(coincide("mendez", "Carlos Méndez"))
        self.assertTrue(coincide("", "lo que sea"))
        self.assertFalse(coincide("toyota civic", "Toyota", "Corolla"))

    def test_clientes_ordenados_por_id(self):
        self.assertEqual([c["id"] for c in self.servicio.buscar_clientes()], [1, 2, 3])
        self.servicio.editar_cliente(1, "Zoila Zamora", "5555-1234", "z@correo.com", "1234567890101")
        self.assertEqual([c["id"] for c in self.servicio.buscar_clientes()], [1, 2, 3])

    def test_buscar_cliente_por_nombre_documento_telefono_o_correo(self):
        ids = lambda texto: [c["id"] for c in self.servicio.buscar_clientes(texto)]
        self.assertEqual(ids("méndez"), [2])
        self.assertEqual(ids("p1234"), [3])
        self.assertEqual(ids("5555"), [1])
        self.assertEqual(ids("empresa.gt"), [2])
        self.assertEqual(ids("nadie"), [])

    def test_buscar_auto_solo_entre_disponibles(self):
        ids = lambda texto: [a["id"] for a in self.servicio.buscar_autos_disponibles(texto)]
        self.assertEqual(ids(""), [2, 1, 3])  # orden por marca y modelo
        self.assertEqual(ids("toyota 2022"), [3])
        self.assertEqual(ids("#1"), [1])
        self.servicio.registrar_venta(1, 3, "0")
        self.assertEqual(ids("hilux"), [])
        self.assertEqual(ids("toyota"), [1])


class HistoriaResumen(unittest.TestCase):
    """HU-05 y RF-06: los indicadores reflejan cada operación."""

    def test_resumen_se_actualiza_tras_cada_operacion(self):
        servicio = servicio_con_datos()
        inicial = servicio.resumen()
        self.assertEqual((inicial["autos_disponibles"], inicial["autos_vendidos"],
                          inicial["total_vendido"]), (3, 0, 0))
        servicio.registrar_venta(1, 1, "10")
        servicio.registrar_venta(1, 2, "0")
        resumen = servicio.resumen()
        self.assertEqual(resumen["autos_disponibles"], 1)
        self.assertEqual(resumen["autos_vendidos"], 2)
        self.assertEqual(resumen["total_vendido"], 270000.00)
        self.assertEqual(resumen["valor_inventario"], 310000.00)


class Persistencia(unittest.TestCase):
    """RNF-03: los datos sobreviven a un reinicio y un archivo dañado no rompe la app."""

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self.carpeta.name, "autoventas.json")

    def tearDown(self):
        self.carpeta.cleanup()

    def nuevo_servicio(self):
        datos, aviso = persistencia.cargar(self.ruta)
        return AutoVentas(datos, al_guardar=lambda d: persistencia.guardar(self.ruta, d)), aviso

    def test_guardar_y_recargar(self):
        servicio, aviso = self.nuevo_servicio()
        self.assertIsNone(aviso)
        servicio.registrar_auto("Kia", "Rio", "2020", "90000", "100")
        servicio.registrar_cliente("Ana Ruiz", "55551111", "ana@correo.com", "P12345")
        servicio.registrar_venta(1, 1, "5")
        recargado, _ = self.nuevo_servicio()
        self.assertEqual(recargado.obtener_auto(1)["estado"], VENDIDO)
        self.assertEqual(len(recargado.ventas), 1)
        self.assertEqual(recargado.registrar_auto("Kia", "Rio", "2020", "1", "1")["id"], 2)

    def test_archivo_danado_se_respalda(self):
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            archivo.write("{esto no es json")
        servicio, aviso = self.nuevo_servicio()
        self.assertIsNotNone(aviso)
        self.assertEqual(servicio.autos, [])
        respaldos = [n for n in os.listdir(self.carpeta.name) if ".danado_" in n]
        self.assertEqual(len(respaldos), 1)

    def test_si_falla_el_guardado_no_cambian_los_datos(self):
        def falla(_datos):
            raise OSError("disco lleno")
        servicio = servicio_con_datos()
        servicio._al_guardar = falla
        with self.assertRaises(OSError):
            servicio.registrar_venta(1, 1, "0")
        self.assertEqual(servicio.obtener_auto(1)["estado"], DISPONIBLE)
        self.assertEqual(servicio.ventas, [])

    def test_formato_del_archivo(self):
        servicio, _ = self.nuevo_servicio()
        servicio.registrar_auto("Kia", "Rio", "2020", "90000", "100")
        with open(self.ruta, encoding="utf-8") as archivo:
            contenido = json.load(archivo)
        self.assertEqual(set(contenido) >= {"autos", "clientes", "ventas"}, True)
        self.assertEqual(set(contenido["autos"][0]),
                         {"id", "marca", "modelo", "anio", "precio", "kilometraje", "estado"})


if __name__ == "__main__":
    unittest.main()

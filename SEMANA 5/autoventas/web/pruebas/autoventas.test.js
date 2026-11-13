/**
 * Pruebas unitarias de AutoVentas (versión web), con el ejecutor integrado de Node.
 *
 * Ejecutar desde la carpeta `web`:
 *     node --test
 *
 * Son las mismas 37 pruebas de la versión de escritorio (pruebas/test_autoventas.py),
 * traducidas a JavaScript: casos mínimos CP-01 a CP-06, criterios de aceptación
 * de las historias de usuario, buscadores y persistencia (con un almacén falso
 * en lugar de localStorage).
 */
"use strict";

const { describe, test, beforeEach } = require("node:test");
const assert = require("node:assert/strict");

const persistencia = require("../js/persistencia.js");
const { DISPONIBLE, VENDIDO, AutoVentas, ErrorNegocio, coincide } = require("../js/logica.js");
const { ErrorValidacion, anioActual } = require("../js/validaciones.js");

function servicioConDatos() {
  const servicio = new AutoVentas();
  servicio.registrarAuto("Toyota", "Corolla", "2020", "150000", "45000");
  servicio.registrarAuto("Honda", "Civic", "2019", "135000", "60000");
  servicio.registrarAuto("Toyota", "Hilux", "2022", "310000", "20000");
  servicio.registrarCliente("María López", "5555-1234", "maria@correo.com", "1234567890101");
  return servicio;
}

/** Ejecuta `accion` y devuelve el error lanzado, comprobando su tipo. */
function capturar(accion, Tipo = ErrorValidacion) {
  try {
    accion();
  } catch (error) {
    assert.ok(error instanceof Tipo, `se esperaba ${Tipo.name} y se obtuvo ${error && error.name}`);
    return error;
  }
  assert.fail(`se esperaba ${Tipo.name} y no hubo error`);
}

/** Almacén en memoria con la misma interfaz que localStorage. */
class AlmacenFalso {
  constructor() { this.valores = new Map(); }
  getItem(clave) { return this.valores.has(clave) ? this.valores.get(clave) : null; }
  setItem(clave, valor) { this.valores.set(clave, String(valor)); }
  removeItem(clave) { this.valores.delete(clave); }
}

describe("Casos de prueba mínimos (sección 6 del instructivo)", () => {
  let servicio;
  beforeEach(() => { servicio = servicioConDatos(); });

  test("CP-01: auto con precio negativo es rechazado", () => {
    const error = capturar(() => servicio.registrarAuto("Kia", "Rio", "2021", "-5000", "1000"));
    assert.ok(error.errores.includes("El precio debe ser mayor que cero."));
    assert.equal(servicio.autos.length, 3);
  });

  test("CP-02: cliente con correo inválido es rechazado", () => {
    const error = capturar(() => servicio.registrarCliente("Juan Pérez", "5555-0000", "abc", "9876543210101"));
    assert.ok(error.errores.some((e) => e.toLowerCase().includes("correo")));
    assert.equal(error.campos.correo !== undefined, true);
    assert.equal(servicio.clientes.length, 1);
  });

  test("CP-03: vender un auto vendido está bloqueado", () => {
    servicio.registrarVenta(1, 1, "0");
    servicio.registrarCliente("Juan Pérez", "5555-0000", "juan@correo.com", "9876543210101");
    const error = capturar(() => servicio.registrarVenta(2, 1, "0"), ErrorNegocio);
    assert.match(error.message, /no está disponible/);
    assert.equal(servicio.ventas.length, 1);
  });

  test("CP-04: descuento de 20 % es rechazado", () => {
    const error = capturar(() => servicio.registrarVenta(1, 1, "20"));
    assert.match(error.message, /15/);
    assert.equal(servicio.obtenerAuto(1).estado, DISPONIBLE);
    assert.deepEqual(servicio.ventas, []);
  });

  test("CP-05: venta correcta", () => {
    const venta = servicio.registrarVenta(1, 1, "10");
    assert.equal(servicio.obtenerAuto(1).estado, VENDIDO);
    assert.equal(venta.descuento, 15000);
    assert.equal(venta.total, 135000); // 150,000 − 10 %
    assert.equal(servicio.historialVentas()[0].id, venta.id);
  });

  test("CP-06: filtrar por una marca inexistente no da resultados", () => {
    assert.deepEqual(servicio.filtrarAutos({ marca: "Ferrari" }), []);
  });
});

describe("HU-01 Autos (RF-01)", () => {
  let servicio;
  beforeEach(() => { servicio = new AutoVentas(); });

  test("todos los campos son obligatorios y se informan juntos", () => {
    const error = capturar(() => servicio.registrarAuto("", " ", "", "", ""));
    assert.equal(error.errores.length, 5);
    assert.deepEqual(Object.keys(error.campos).sort(), ["anio", "kilometraje", "marca", "modelo", "precio"]);
  });

  test("año fuera de rango", () => {
    for (const anio of ["1989", String(anioActual() + 1), "dos mil"]) {
      capturar(() => servicio.registrarAuto("Kia", "Rio", anio, "90000", "100"));
    }
  });

  test("límites válidos de año", () => {
    servicio.registrarAuto("Kia", "Rio", "1990", "90000", "100");
    servicio.registrarAuto("Kia", "Rio", String(anioActual()), "90000", "100");
    assert.equal(servicio.autos.length, 2);
  });

  test("precio cero o texto y kilometraje negativo o decimal", () => {
    for (const [precio, km] of [["0", "10"], ["abc", "10"], ["1000", "-1"], ["1000", "1.5"], ["0x10", "10"]]) {
      capturar(() => servicio.registrarAuto("Kia", "Rio", "2020", precio, km));
    }
  });

  test("auto nuevo queda disponible y normalizado", () => {
    const auto = servicio.registrarAuto("  Mazda ", "CX-5", "2021", "Q 215,000.50", "12,000");
    assert.equal(auto.estado, DISPONIBLE);
    assert.equal(auto.marca, "Mazda");
    assert.equal(auto.precio, 215000.5);
    assert.equal(auto.kilometraje, 12000);
  });

  test("editar y eliminar", () => {
    const auto = servicio.registrarAuto("Kia", "Rio", "2020", "90000", "100");
    servicio.editarAuto(auto.id, "Kia", "Rio LX", "2021", "95000", "200");
    assert.equal(servicio.obtenerAuto(auto.id).modelo, "Rio LX");
    servicio.eliminarAuto(auto.id);
    assert.deepEqual(servicio.autos, []);
  });

  test("auto vendido no se edita ni elimina", () => {
    const conDatos = servicioConDatos();
    conDatos.registrarVenta(1, 1, "0");
    capturar(() => conDatos.editarAuto(1, "Toyota", "Corolla", "2020", "1", "1"), ErrorNegocio);
    capturar(() => conDatos.eliminarAuto(1), ErrorNegocio);
  });

  test("los id no se reutilizan", () => {
    const primero = servicio.registrarAuto("Kia", "Rio", "2020", "90000", "100");
    servicio.eliminarAuto(primero.id);
    const segundo = servicio.registrarAuto("Kia", "Rio", "2020", "90000", "100");
    assert.notEqual(primero.id, segundo.id);
  });
});

describe("HU-02 Búsqueda (RF-02)", () => {
  let servicio;
  const ids = (filtros) => servicio.filtrarAutos(filtros).map((a) => a.id);
  beforeEach(() => { servicio = servicioConDatos(); });

  test("filtro por marca ignora mayúsculas y tildes", () => {
    assert.deepEqual(ids({ marca: "toyóta" }), [1, 3]);
  });

  test("filtro por rango de precio", () => {
    assert.deepEqual(ids({ precioMin: "140000", precioMax: "200000" }), [1]);
    assert.deepEqual(ids({ precioMin: "300000" }), [3]);
  });

  test("filtro por año y búsqueda por modelo", () => {
    assert.deepEqual(ids({ anio: "2019" }), [2]);
    assert.deepEqual(ids({ texto: "hilux" }), [3]);
  });

  test("filtro por estado", () => {
    servicio.registrarVenta(1, 2, "0");
    assert.deepEqual(ids({ estado: VENDIDO }), [2]);
    assert.deepEqual(ids({ estado: DISPONIBLE }), [1, 3]);
  });

  test("rango invertido o no numérico es error", () => {
    capturar(() => servicio.filtrarAutos({ precioMin: "200000", precioMax: "100" }));
    capturar(() => servicio.filtrarAutos({ precioMin: "barato" }));
  });
});

describe("HU-03 Clientes (RF-03)", () => {
  let servicio;
  beforeEach(() => { servicio = servicioConDatos(); });

  test("correos válidos e inválidos", () => {
    for (const correo of ["abc", "a@b", "a@@b.com", "a b@c.com", "a@b..com", "@dominio.com"]) {
      capturar(() => servicio.registrarCliente("Ana Ruiz", "55551111", correo, `DOC${correo.length}X`));
    }
    const cliente = servicio.registrarCliente("Ana Ruiz", "55551111", "Ana.Ruiz@Mail.com", "P12345");
    assert.equal(cliente.correo, "ana.ruiz@mail.com");
  });

  test("documento duplicado no se permite", () => {
    for (const documento of ["1234567890101", "1234-56789-0101", " 1234567890101 "]) {
      const error = capturar(() => servicio.registrarCliente("Otra Persona", "55550000", "otra@correo.com", documento), ErrorNegocio);
      assert.ok(error.campos.documento);
    }
  });

  test("editar cliente conserva su propio documento", () => {
    servicio.editarCliente(1, "María López de Paz", "5555-1234", "maria@correo.com", "1234567890101");
    assert.equal(servicio.obtenerCliente(1).nombre, "María López de Paz");
  });

  test("cliente con ventas no se elimina", () => {
    servicio.registrarVenta(1, 1, "0");
    capturar(() => servicio.eliminarCliente(1), ErrorNegocio);
  });

  test("teléfono inválido", () => {
    for (const telefono of ["123", "telefono", "5555-12a4"]) {
      capturar(() => servicio.registrarCliente("Ana Ruiz", telefono, "ana@correo.com", "P99999"));
    }
  });
});

describe("HU-04 Ventas (RF-04, RF-05)", () => {
  let servicio;
  beforeEach(() => { servicio = servicioConDatos(); });

  test("descuento máximo de 15 % es válido", () => {
    const venta = servicio.registrarVenta(1, 2, "15");
    assert.equal(venta.descuento, 20250);
    assert.equal(venta.total, 114750);
  });

  test("descuento vacío es cero y negativo es error", () => {
    assert.equal(servicio.calcularVenta(1, "").total, 150000);
    capturar(() => servicio.calcularVenta(1, "-1"));
  });

  test("venta sin cliente o auto", () => {
    const error = capturar(() => servicio.registrarVenta(null, null, "0"));
    assert.equal(error.errores.length, 2);
  });

  test("historial ordenado de la más reciente a la más antigua", () => {
    servicio.registrarVenta(1, 1, "0", new Date(2026, 10, 1, 10, 0));
    servicio.registrarVenta(1, 2, "5", new Date(2026, 10, 5, 9, 30));
    const historial = servicio.historialVentas();
    assert.deepEqual(historial.map((h) => h.auto), ["Honda Civic 2019", "Toyota Corolla 2020"]);
    assert.equal(historial[0].cliente, "María López");
    assert.equal(historial[0].fecha, "2026-11-05 09:30");
  });
});

describe("Buscadores de venta (iteración 1)", () => {
  let servicio;
  beforeEach(() => {
    servicio = servicioConDatos();
    servicio.registrarCliente("Carlos Méndez", "4444-9876", "carlos@empresa.gt", "2345678900101");
    servicio.registrarCliente("Ana Ruiz", "3333-4444", "ana@mail.com", "P1234567");
  });

  test("coincide por palabras sin orden ni tildes", () => {
    assert.equal(coincide("corolla TOYOTA", "Toyota", "Corolla", 2020), true);
    assert.equal(coincide("mendez", "Carlos Méndez"), true);
    assert.equal(coincide("", "lo que sea"), true);
    assert.equal(coincide("toyota civic", "Toyota", "Corolla"), false);
  });

  test("clientes ordenados por id", () => {
    assert.deepEqual(servicio.buscarClientes().map((c) => c.id), [1, 2, 3]);
    servicio.editarCliente(1, "Zoila Zamora", "5555-1234", "z@correo.com", "1234567890101");
    assert.deepEqual(servicio.buscarClientes().map((c) => c.id), [1, 2, 3]);
  });

  test("buscar cliente por nombre, documento, teléfono o correo", () => {
    const ids = (texto) => servicio.buscarClientes(texto).map((c) => c.id);
    assert.deepEqual(ids("méndez"), [2]);
    assert.deepEqual(ids("p1234"), [3]);
    assert.deepEqual(ids("5555"), [1]);
    assert.deepEqual(ids("empresa.gt"), [2]);
    assert.deepEqual(ids("nadie"), []);
  });

  test("buscar auto solo entre disponibles", () => {
    const ids = (texto) => servicio.buscarAutosDisponibles(texto).map((a) => a.id);
    assert.deepEqual(ids(""), [2, 1, 3]); // orden por marca y modelo
    assert.deepEqual(ids("toyota 2022"), [3]);
    assert.deepEqual(ids("#1"), [1]);
    servicio.registrarVenta(1, 3, "0");
    assert.deepEqual(ids("hilux"), []);
    assert.deepEqual(ids("toyota"), [1]);
  });
});

describe("HU-05 Resumen (RF-06)", () => {
  test("el resumen se actualiza tras cada operación", () => {
    const servicio = servicioConDatos();
    const inicial = servicio.resumen();
    assert.deepEqual([inicial.autos_disponibles, inicial.autos_vendidos, inicial.total_vendido], [3, 0, 0]);
    servicio.registrarVenta(1, 1, "10");
    servicio.registrarVenta(1, 2, "0");
    const resumen = servicio.resumen();
    assert.equal(resumen.autos_disponibles, 1);
    assert.equal(resumen.autos_vendidos, 2);
    assert.equal(resumen.total_vendido, 270000);
    assert.equal(resumen.valor_inventario, 310000);
  });
});

describe("RNF-03 Persistencia en localStorage", () => {
  let almacen;
  const nuevoServicio = () => {
    const { datos, aviso } = persistencia.cargar(almacen);
    return { servicio: new AutoVentas(datos, (d) => persistencia.guardar(d, almacen)), aviso };
  };
  beforeEach(() => { almacen = new AlmacenFalso(); });

  test("guardar y recargar", () => {
    const { servicio, aviso } = nuevoServicio();
    assert.equal(aviso, null);
    servicio.registrarAuto("Kia", "Rio", "2020", "90000", "100");
    servicio.registrarCliente("Ana Ruiz", "55551111", "ana@correo.com", "P12345");
    servicio.registrarVenta(1, 1, "5");
    const { servicio: recargado } = nuevoServicio();
    assert.equal(recargado.obtenerAuto(1).estado, VENDIDO);
    assert.equal(recargado.ventas.length, 1);
    assert.equal(recargado.registrarAuto("Kia", "Rio", "2020", "1", "1").id, 2);
  });

  test("datos dañados se respaldan", () => {
    almacen.setItem(persistencia.CLAVE, "{esto no es json");
    const { servicio, aviso } = nuevoServicio();
    assert.ok(aviso);
    assert.deepEqual(servicio.autos, []);
    const respaldos = [...almacen.valores.keys()].filter((k) => k.includes(".danado_"));
    assert.equal(respaldos.length, 1);
  });

  test("si falla el guardado no cambian los datos", () => {
    const servicio = servicioConDatos();
    servicio.alGuardar = () => { throw new Error("QuotaExceededError"); };
    assert.throws(() => servicio.registrarVenta(1, 1, "0"), /QuotaExceededError/);
    assert.equal(servicio.obtenerAuto(1).estado, DISPONIBLE);
    assert.deepEqual(servicio.ventas, []);
  });

  test("formato de los datos igual al JSON de escritorio", () => {
    const { servicio } = nuevoServicio();
    servicio.registrarAuto("Kia", "Rio", "2020", "90000", "100");
    const contenido = JSON.parse(almacen.getItem(persistencia.CLAVE));
    for (const clave of ["autos", "clientes", "ventas"]) assert.ok(clave in contenido);
    assert.deepEqual(Object.keys(contenido.autos[0]).sort(),
      ["anio", "estado", "id", "kilometraje", "marca", "modelo", "precio"]);
  });
});

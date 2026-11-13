/**
 * Persistencia local en localStorage (RNF-03).
 *
 * Equivalente a persistencia.py de la versión de escritorio. Guarda el mismo
 * objeto JSON: {"version": 1, "autos": [...], "clientes": [...], "ventas": [...]}.
 *
 * - Si el contenido guardado está dañado, se respalda en otra clave y se inicia vacío.
 * - Si el navegador bloquea localStorage (modo privado estricto, cookies
 *   deshabilitadas), la aplicación funciona igual pero avisa que no guardará.
 * - El almacén se puede inyectar, lo que permite probar este módulo en Node.
 */
(function (raiz) {
  "use strict";

  const CLAVE = "autoventas.datos";
  const VERSION_FORMATO = 1;

  const datosVacios = () => ({ version: VERSION_FORMATO, autos: [], clientes: [], ventas: [] });

  /** Devuelve localStorage si se puede usar, o null si el navegador lo bloquea. */
  function almacenDelNavegador() {
    try {
      const almacen = raiz.localStorage;
      const prueba = "__autoventas_prueba__";
      almacen.setItem(prueba, "1");
      almacen.removeItem(prueba);
      return almacen;
    } catch (error) {
      return null;
    }
  }

  /** Convierte el texto guardado en datos válidos o lanza un error que explica el problema. */
  function interpretar(texto) {
    const datos = JSON.parse(texto);
    if (!datos || typeof datos !== "object" || Array.isArray(datos)) {
      throw new TypeError("el contenido no es un objeto JSON");
    }
    for (const clave of ["autos", "clientes", "ventas"]) {
      if (datos[clave] === undefined) datos[clave] = [];
      if (!Array.isArray(datos[clave])) throw new TypeError(`«${clave}» no es una lista`);
    }
    datos.version = VERSION_FORMATO;
    return datos;
  }

  /** Devuelve {datos, aviso, almacen}. `aviso` es null o un mensaje para el usuario. */
  function cargar(almacen = almacenDelNavegador(), clave = CLAVE) {
    if (!almacen) {
      return {
        datos: datosVacios(),
        almacen: null,
        aviso: "Este navegador no permite guardar datos (almacenamiento local bloqueado). " +
          "Puede usar la aplicación, pero los cambios se perderán al cerrar la página.",
      };
    }
    const texto = almacen.getItem(clave);
    if (texto === null) return { datos: datosVacios(), aviso: null, almacen };
    try {
      return { datos: interpretar(texto), aviso: null, almacen };
    } catch (error) {
      const respaldo = `${clave}.danado_${Date.now()}`;
      let aviso = `No se pudieron leer los datos guardados (${error.message}). Se inició con datos vacíos.`;
      try {
        almacen.setItem(respaldo, texto);
        aviso += ` El contenido original se respaldó en la clave «${respaldo}».`;
      } catch (e) { /* sin espacio para el respaldo: se informa sin él */ }
      return { datos: datosVacios(), aviso, almacen };
    }
  }

  /** Guarda los datos. Lanza un error si el navegador lo impide (por ejemplo, sin espacio). */
  function guardar(datos, almacen, clave = CLAVE) {
    if (!almacen) return; // modo sin almacenamiento: ya se avisó al cargar
    almacen.setItem(clave, JSON.stringify(datos));
  }

  const api = { CLAVE, datosVacios, almacenDelNavegador, cargar, guardar, interpretar };
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  } else {
    raiz.AV = raiz.AV || {};
    raiz.AV.persistencia = api;
  }
})(typeof window !== "undefined" ? window : globalThis);

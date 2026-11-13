/**
 * Validaciones de datos de entrada de AutoVentas (RNF-02).
 *
 * Traducción directa de validaciones.py de la versión de escritorio: mismas
 * reglas y mismos mensajes. Funciones puras, sin acceso al DOM ni a
 * localStorage. Cada función recibe el texto tal como lo escribió el usuario y
 * devuelve el valor ya convertido, o lanza ErrorValidacion.
 *
 * Funciona en el navegador (window.AV.validaciones) y en Node (require).
 */
(function (raiz) {
  "use strict";

  const ANIO_MINIMO = 1990;
  const DESCUENTO_MAXIMO = 15; // porcentaje máximo de descuento (HU-04)
  const PRECIO_MAXIMO = 10000000; // tope razonable para evitar errores de digitación
  const KILOMETRAJE_MAXIMO = 2000000;

  // usuario@dominio.ext — sin espacios, un solo "@" y extensión de 2+ letras.
  const PATRON_CORREO = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
  // Teléfono: dígitos con espacios, guiones o "+" inicial; entre 8 y 15 dígitos.
  const PATRON_TELEFONO = /^\+?[0-9][0-9 -]*$/;
  // Documento (DPI, pasaporte, NIT...): letras, dígitos y guiones.
  const PATRON_DOCUMENTO = /^[A-Za-z0-9-]{5,20}$/;
  // Nombres de personas: letras (con tildes), espacios, punto, apóstrofo y guion.
  const PATRON_NOMBRE = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]+$/;
  // Número decimal simple: "85000", "85000.50", ".5" (sin notación científica ni hexadecimal).
  const PATRON_NUMERO = /^[+-]?(\d+(\.\d*)?|\.\d+)$/;

  /** Error de datos de entrada. `errores`: lista de mensajes; `campos`: {campo: mensaje}. */
  class ErrorValidacion extends Error {
    constructor(errores, campos = {}) {
      const lista = Array.isArray(errores) ? errores : [errores];
      super(lista.join("\n"));
      this.name = "ErrorValidacion";
      this.errores = lista;
      this.campos = campos;
    }
  }

  const anioActual = () => new Date().getFullYear();
  const limpiar = (texto) => String(texto ?? "").trim();
  const redondear = (valor) => Math.round((valor + Number.EPSILON) * 100) / 100;

  /** Convierte "125,000.50" o "Q 125000" en número. Lanza RangeError si no es número. */
  function numero(texto) {
    let limpio = limpiar(texto).toUpperCase();
    if (limpio.startsWith("Q")) limpio = limpio.slice(1);
    limpio = limpio.replace(/[,\s]/g, "");
    if (!PATRON_NUMERO.test(limpio)) throw new RangeError("no es un número");
    return Number(limpio);
  }

  function textoObligatorio(texto, campo, minimo = 1, maximo = 60) {
    const valor = limpiar(texto).split(/\s+/).filter(Boolean).join(" "); // colapsa espacios
    if (!valor) throw new ErrorValidacion(`El campo «${campo}» es obligatorio.`);
    if (valor.length < minimo) throw new ErrorValidacion(`«${campo}» debe tener al menos ${minimo} caracteres.`);
    if (valor.length > maximo) throw new ErrorValidacion(`«${campo}» no puede superar ${maximo} caracteres.`);
    return valor;
  }

  function validarAnio(texto) {
    if (!limpiar(texto)) throw new ErrorValidacion("El campo «Año» es obligatorio.");
    if (!/^[+-]?\d+$/.test(limpiar(texto))) {
      throw new ErrorValidacion("El año debe ser un número entero (ejemplo: 2020).");
    }
    const anio = Number(limpiar(texto));
    const tope = anioActual();
    if (anio < ANIO_MINIMO || anio > tope) {
      throw new ErrorValidacion(`El año debe estar entre ${ANIO_MINIMO} y ${tope}.`);
    }
    return anio;
  }

  function validarPrecio(texto) {
    if (!limpiar(texto)) throw new ErrorValidacion("El campo «Precio» es obligatorio.");
    let precio;
    try {
      precio = numero(texto);
    } catch (e) {
      throw new ErrorValidacion("El precio debe ser un número (ejemplo: 85000 o 85,000.50).");
    }
    if (precio <= 0) throw new ErrorValidacion("El precio debe ser mayor que cero.");
    if (precio > PRECIO_MAXIMO) {
      throw new ErrorValidacion(`El precio no puede superar ${formatoMoneda(PRECIO_MAXIMO)}.`);
    }
    return redondear(precio);
  }

  function validarKilometraje(texto) {
    if (!limpiar(texto)) throw new ErrorValidacion("El campo «Kilometraje» es obligatorio.");
    let km;
    try {
      km = numero(texto);
    } catch (e) {
      throw new ErrorValidacion("El kilometraje debe ser un número entero (ejemplo: 45000).");
    }
    if (!Number.isInteger(km)) throw new ErrorValidacion("El kilometraje debe ser un número entero, sin decimales.");
    if (km < 0) throw new ErrorValidacion("El kilometraje no puede ser negativo.");
    if (km > KILOMETRAJE_MAXIMO) {
      throw new ErrorValidacion(`El kilometraje no puede superar ${KILOMETRAJE_MAXIMO.toLocaleString("en-US")} km.`);
    }
    return km;
  }

  function validarNombrePersona(texto) {
    const nombre = textoObligatorio(texto, "Nombre", 3, 80);
    if (!PATRON_NOMBRE.test(nombre)) {
      throw new ErrorValidacion("El nombre solo puede contener letras, espacios, puntos y guiones.");
    }
    return nombre;
  }

  function validarTelefono(texto) {
    const telefono = textoObligatorio(texto, "Teléfono", 1, 20);
    const digitos = telefono.replace(/\D/g, "");
    if (!PATRON_TELEFONO.test(telefono) || digitos.length < 8 || digitos.length > 15) {
      throw new ErrorValidacion("El teléfono debe tener entre 8 y 15 dígitos (ejemplo: 5555-1234).");
    }
    return telefono;
  }

  function validarCorreo(texto) {
    const correo = limpiar(texto);
    if (!correo) throw new ErrorValidacion("El campo «Correo» es obligatorio.");
    if (correo.length > 100 || !PATRON_CORREO.test(correo) || correo.includes("..")) {
      throw new ErrorValidacion("El correo no tiene un formato válido (ejemplo: nombre@dominio.com).");
    }
    return correo.toLowerCase();
  }

  function validarDocumento(texto) {
    const documento = limpiar(texto).toUpperCase();
    if (!documento) throw new ErrorValidacion("El campo «Documento» es obligatorio.");
    if (!PATRON_DOCUMENTO.test(documento)) {
      throw new ErrorValidacion("El documento debe tener de 5 a 20 caracteres: letras, números o guiones.");
    }
    return documento;
  }

  /** Descuento expresado en porcentaje, de 0 a 15 (HU-04, CP-04). Vacío = 0. */
  function validarPorcentajeDescuento(texto) {
    const limpio = limpiar(texto).replace(/%$/, "");
    if (!limpio) return 0;
    let porcentaje;
    try {
      porcentaje = numero(limpio);
    } catch (e) {
      throw new ErrorValidacion("El descuento debe ser un número entre 0 y 15.");
    }
    if (porcentaje < 0) throw new ErrorValidacion("El descuento no puede ser negativo.");
    if (porcentaje > DESCUENTO_MAXIMO) {
      throw new ErrorValidacion(`El descuento no puede superar el ${DESCUENTO_MAXIMO} %.`);
    }
    return porcentaje;
  }

  /**
   * Ejecuta varias validaciones y reúne todos los errores en uno solo, para que
   * el usuario corrija el formulario completo de una vez.
   * `validaciones`: lista de [clave, funcion, argumento]. Devuelve {clave: valor}.
   */
  function recopilar(validaciones) {
    const valores = {};
    const errores = [];
    const campos = {};
    for (const [clave, funcion, argumento] of validaciones) {
      try {
        valores[clave] = funcion(argumento);
      } catch (error) {
        if (!(error instanceof ErrorValidacion)) throw error;
        errores.push(...error.errores);
        campos[clave] = error.errores[0];
      }
    }
    if (errores.length) throw new ErrorValidacion(errores, campos);
    return valores;
  }

  // ---- formato (compartido por lógica e interfaz) ----
  const FORMATO_DINERO = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  function formatoMoneda(valor) {
    return `Q ${FORMATO_DINERO.format(valor)}`;
  }

  const api = {
    ANIO_MINIMO, DESCUENTO_MAXIMO, PRECIO_MAXIMO, KILOMETRAJE_MAXIMO,
    ErrorValidacion, anioActual, numero, redondear, formatoMoneda,
    textoObligatorio, validarAnio, validarPrecio, validarKilometraje, validarNombrePersona,
    validarTelefono, validarCorreo, validarDocumento, validarPorcentajeDescuento, recopilar,
  };
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  } else {
    raiz.AV = raiz.AV || {};
    raiz.AV.validaciones = api;
  }
})(typeof window !== "undefined" ? window : globalThis);

/**
 * Reglas de negocio de AutoVentas (RNF-04: sin dependencia del DOM).
 *
 * Traducción de logica.py de la versión de escritorio. La clase AutoVentas
 * guarda el estado en memoria y ofrece las operaciones de RF-01 a RF-06. Cada
 * operación que modifica datos es una transacción: si el guardado falla, los
 * datos en memoria vuelven a como estaban.
 *
 * El formato de los datos es idéntico al JSON de la versión de escritorio
 * (mismos nombres de campo), así que ambas versiones comparten el modelo.
 * La persistencia se inyecta con `alGuardar`, lo que permite probar la lógica
 * sin navegador.
 */
(function (raiz) {
  "use strict";

  const v = typeof module === "object" && module.exports ? require("./validaciones.js") : raiz.AV.validaciones;
  const { ErrorValidacion, formatoMoneda, redondear } = v;

  const DISPONIBLE = "Disponible";
  const VENDIDO = "Vendido";
  const ESTADOS_AUTO = [DISPONIBLE, VENDIDO];
  const TODOS = "Todos";
  const COLECCIONES = ["autos", "clientes", "ventas"];

  /** Operación válida en forma pero no permitida por una regla de negocio. */
  class ErrorNegocio extends ErrorValidacion {
    constructor(errores, campos = {}) {
      super(errores, campos);
      this.name = "ErrorNegocio";
    }
  }

  // ---- utilidades de formato y búsqueda (compartidas con la interfaz) ----
  const formatoKm = (valor) => `${valor.toLocaleString("en-US")} km`;
  const descripcionAuto = (auto) => `${auto.marca} ${auto.modelo} ${auto.anio}`;

  /** Minúsculas y sin tildes, para búsquedas tolerantes ("Peugeót" = "peugeot"). */
  function normalizar(texto) {
    return String(texto ?? "").normalize("NFD").replace(/\p{M}/gu, "").toLowerCase().trim();
  }

  /**
   * true si cada palabra de la consulta aparece en alguno de los campos.
   * Ignora mayúsculas, tildes y el orden: "corolla toyota" encuentra
   * "Toyota Corolla 2020". Una consulta vacía coincide con todo.
   */
  function coincide(consulta, ...campos) {
    const texto = normalizar(campos.join(" "));
    return normalizar(consulta).split(/\s+/).filter(Boolean).every((palabra) => texto.includes(palabra));
  }

  /** "1234-56789-0101" y "1234567890101" son el mismo documento. */
  const claveDocumento = (documento) => documento.replace(/-/g, "").toUpperCase();
  const compararTexto = (a, b) => normalizar(a).localeCompare(normalizar(b), "es");

  function fechaActual(fecha = new Date()) {
    const dos = (n) => String(n).padStart(2, "0");
    return `${fecha.getFullYear()}-${dos(fecha.getMonth() + 1)}-${dos(fecha.getDate())} ` +
      `${dos(fecha.getHours())}:${dos(fecha.getMinutes())}`;
  }

  class AutoVentas {
    constructor(datos = null, alGuardar = null) {
      this.datos = datos || { autos: [], clientes: [], ventas: [] };
      for (const clave of COLECCIONES) {
        if (!Array.isArray(this.datos[clave])) this.datos[clave] = [];
      }
      this.alGuardar = alGuardar;
      this._iniciarSecuencias();
    }

    // ---- infraestructura --------------------------------------------
    /** Los id nunca se reutilizan, aunque se elimine el último registro. */
    _iniciarSecuencias() {
      const secuencias = (this.datos.secuencias = this.datos.secuencias || {});
      for (const clave of COLECCIONES) {
        const mayor = this.datos[clave].reduce((max, r) => Math.max(max, r.id), 0);
        secuencias[clave] = Math.max(secuencias[clave] || 0, mayor);
      }
    }

    _nuevoId(coleccion) {
      this.datos.secuencias[coleccion] += 1;
      return this.datos.secuencias[coleccion];
    }

    _transaccion(cambio) {
      const respaldo = structuredClone(this.datos);
      try {
        const resultado = cambio();
        if (this.alGuardar) this.alGuardar(this.datos);
        return resultado;
      } catch (error) {
        for (const clave of Object.keys(this.datos)) delete this.datos[clave];
        Object.assign(this.datos, respaldo);
        throw error;
      }
    }

    /** Reemplaza todos los datos (por ejemplo, si otra pestaña del navegador los cambió). */
    reemplazarDatos(datos) {
      for (const clave of Object.keys(this.datos)) delete this.datos[clave];
      Object.assign(this.datos, datos);
      for (const clave of COLECCIONES) {
        if (!Array.isArray(this.datos[clave])) this.datos[clave] = [];
      }
      this._iniciarSecuencias();
    }

    static _buscar(coleccion, id, nombre) {
      const registro = coleccion.find((r) => r.id === id);
      if (!registro) throw new ErrorNegocio(`No existe ${nombre} con id ${id}.`);
      return registro;
    }

    // ---- autos (RF-01, RF-02) ----------------------------------------
    get autos() { return this.datos.autos; }

    obtenerAuto(id) { return AutoVentas._buscar(this.autos, id, "un auto"); }

    static _validarAuto(marca, modelo, anio, precio, kilometraje) {
      return v.recopilar([
        ["marca", (t) => v.textoObligatorio(t, "Marca", 1, 40), marca],
        ["modelo", (t) => v.textoObligatorio(t, "Modelo", 1, 40), modelo],
        ["anio", v.validarAnio, anio],
        ["precio", v.validarPrecio, precio],
        ["kilometraje", v.validarKilometraje, kilometraje],
      ]);
    }

    /** HU-01: todos los campos obligatorios; el auto nace "Disponible". */
    registrarAuto(marca, modelo, anio, precio, kilometraje) {
      const valores = AutoVentas._validarAuto(marca, modelo, anio, precio, kilometraje);
      return this._transaccion(() => {
        const auto = { id: this._nuevoId("autos"), ...valores, estado: DISPONIBLE };
        this.autos.push(auto);
        return auto;
      });
    }

    editarAuto(id, marca, modelo, anio, precio, kilometraje) {
      const auto = this.obtenerAuto(id);
      if (auto.estado === VENDIDO) {
        throw new ErrorNegocio("No se puede editar un auto vendido: forma parte del historial de ventas.");
      }
      const valores = AutoVentas._validarAuto(marca, modelo, anio, precio, kilometraje);
      this._transaccion(() => Object.assign(this.obtenerAuto(id), valores));
      return this.obtenerAuto(id);
    }

    eliminarAuto(id) {
      const auto = this.obtenerAuto(id);
      if (auto.estado === VENDIDO) {
        throw new ErrorNegocio("No se puede eliminar un auto vendido: forma parte del historial de ventas.");
      }
      this._transaccion(() => {
        this.datos.autos = this.autos.filter((a) => a.id !== id);
      });
    }

    marcas() {
      return [...new Set(this.autos.map((a) => a.marca))].sort(compararTexto);
    }

    /**
     * RF-02 / HU-02. Devuelve la lista filtrada (vacía si no hay resultados).
     * Lanza ErrorValidacion si algún filtro numérico no es válido.
     */
    filtrarAutos({ texto = "", marca = "", anio = "", precioMin = "", precioMax = "", estado = TODOS } = {}) {
      const errores = [];
      const campos = {};
      let anioFiltro = null;
      let minimo = null;
      let maximo = null;
      if (String(anio).trim()) {
        if (/^[+-]?\d+$/.test(String(anio).trim())) anioFiltro = Number(String(anio).trim());
        else { errores.push("El filtro de año debe ser un número entero."); campos.anio = errores.at(-1); }
      }
      for (const [etiqueta, crudo, clave] of [["mínimo", precioMin, "precioMin"], ["máximo", precioMax, "precioMax"]]) {
        if (!String(crudo).trim()) continue;
        let valor;
        try {
          valor = v.numero(crudo);
          if (valor < 0) throw new RangeError();
        } catch (e) {
          errores.push(`El precio ${etiqueta} debe ser un número mayor o igual a cero.`);
          campos[clave] = errores.at(-1);
          continue;
        }
        if (etiqueta === "mínimo") minimo = valor; else maximo = valor;
      }
      if (minimo !== null && maximo !== null && minimo > maximo) {
        errores.push("El precio mínimo no puede ser mayor que el precio máximo.");
        campos.precioMin = errores.at(-1);
      }
      if (errores.length) throw new ErrorValidacion(errores, campos);

      const marcaN = normalizar(marca);
      return this.autos.filter((auto) =>
        coincide(texto, auto.marca, auto.modelo) &&
        (!marcaN || normalizar(auto.marca).includes(marcaN)) &&
        (anioFiltro === null || auto.anio === anioFiltro) &&
        (minimo === null || auto.precio >= minimo) &&
        (maximo === null || auto.precio <= maximo) &&
        (!estado || estado === TODOS || auto.estado === estado));
    }

    autosDisponibles() {
      return this.autos.filter((a) => a.estado === DISPONIBLE);
    }

    /** Autos que se pueden vender, filtrados por id, marca, modelo o año (para Ventas). */
    buscarAutosDisponibles(texto = "") {
      return this.autosDisponibles()
        .filter((a) => coincide(texto, `#${a.id}`, a.marca, a.modelo, a.anio))
        .sort((a, b) => compararTexto(a.marca, b.marca) || compararTexto(a.modelo, b.modelo) || a.id - b.id);
    }

    // ---- clientes (RF-03) --------------------------------------------
    get clientes() { return this.datos.clientes; }

    obtenerCliente(id) { return AutoVentas._buscar(this.clientes, id, "un cliente"); }

    _validarCliente(nombre, telefono, correo, documento, excluirId = null) {
      const valores = v.recopilar([
        ["nombre", v.validarNombrePersona, nombre],
        ["telefono", v.validarTelefono, telefono],
        ["correo", v.validarCorreo, correo],
        ["documento", v.validarDocumento, documento],
      ]);
      const clave = claveDocumento(valores.documento);
      const repetido = this.clientes.find((c) => c.id !== excluirId && claveDocumento(c.documento) === clave);
      if (repetido) {
        const mensaje = `Ya existe un cliente con el documento ${valores.documento} (${repetido.nombre}).`;
        throw new ErrorNegocio(mensaje, { documento: mensaje });
      }
      return valores;
    }

    /** HU-03: correo con formato válido y documento sin duplicados. */
    registrarCliente(nombre, telefono, correo, documento) {
      const valores = this._validarCliente(nombre, telefono, correo, documento);
      return this._transaccion(() => {
        const cliente = { id: this._nuevoId("clientes"), ...valores };
        this.clientes.push(cliente);
        return cliente;
      });
    }

    editarCliente(id, nombre, telefono, correo, documento) {
      this.obtenerCliente(id);
      const valores = this._validarCliente(nombre, telefono, correo, documento, id);
      this._transaccion(() => Object.assign(this.obtenerCliente(id), valores));
      return this.obtenerCliente(id);
    }

    eliminarCliente(id) {
      this.obtenerCliente(id);
      const compras = this.ventas.filter((venta) => venta.id_cliente === id).length;
      if (compras) {
        throw new ErrorNegocio(`No se puede eliminar el cliente: tiene ${compras} venta(s) en el historial.`);
      }
      this._transaccion(() => {
        this.datos.clientes = this.clientes.filter((c) => c.id !== id);
      });
    }

    /** Clientes ordenados por id (menor a mayor), filtrados por nombre, documento, correo o teléfono. */
    buscarClientes(texto = "") {
      return this.clientes
        .filter((c) => coincide(texto, c.nombre, c.documento, c.correo, c.telefono))
        .sort((a, b) => a.id - b.id);
    }

    comprasPorCliente() {
      const compras = {};
      for (const venta of this.ventas) compras[venta.id_cliente] = (compras[venta.id_cliente] || 0) + 1;
      return compras;
    }

    // ---- ventas (RF-04, RF-05) ---------------------------------------
    get ventas() { return this.datos.ventas; }

    /** Vista previa del total: total = precio − descuento (máximo 15 %). */
    calcularVenta(idAuto, porcentajeDescuento) {
      const auto = this.obtenerAuto(idAuto);
      const porcentaje = v.validarPorcentajeDescuento(porcentajeDescuento);
      const descuento = redondear(auto.precio * porcentaje / 100);
      return {
        precio: auto.precio,
        porcentaje_descuento: porcentaje,
        descuento,
        total: redondear(auto.precio - descuento),
      };
    }

    /** HU-04: solo autos "Disponible"; el auto pasa a "Vendido" al confirmar. */
    registrarVenta(idCliente, idAuto, porcentajeDescuento, fecha = null) {
      const errores = [];
      if (idCliente === null || idCliente === undefined) errores.push("Seleccione un cliente.");
      if (idAuto === null || idAuto === undefined) errores.push("Seleccione un auto.");
      if (errores.length) throw new ErrorValidacion(errores);
      this.obtenerCliente(idCliente);
      const auto = this.obtenerAuto(idAuto);
      if (auto.estado !== DISPONIBLE) {
        throw new ErrorNegocio(`El auto ${descripcionAuto(auto)} no está disponible (estado: ${auto.estado}).`);
      }
      const calculo = this.calcularVenta(idAuto, porcentajeDescuento);
      return this._transaccion(() => {
        const venta = {
          id: this._nuevoId("ventas"),
          id_auto: idAuto,
          id_cliente: idCliente,
          fecha: fechaActual(fecha || new Date()),
          ...calculo,
        };
        this.ventas.push(venta);
        this.obtenerAuto(idAuto).estado = VENDIDO;
        return venta;
      });
    }

    /** RF-05: ventas de la más reciente a la más antigua, con datos de cliente y auto. */
    historialVentas() {
      return this.ventas.map((venta) => {
        const auto = this.autos.find((a) => a.id === venta.id_auto);
        const cliente = this.clientes.find((c) => c.id === venta.id_cliente);
        return {
          ...venta,
          auto: auto ? descripcionAuto(auto) : `Auto #${venta.id_auto}`,
          cliente: cliente ? cliente.nombre : `Cliente #${venta.id_cliente}`,
          documento: cliente ? cliente.documento : "",
        };
      }).sort((a, b) => b.fecha.localeCompare(a.fecha) || b.id - a.id);
    }

    // ---- resumen (RF-06, HU-05) --------------------------------------
    resumen() {
      const disponibles = this.autosDisponibles();
      const suma = (lista, campo) => redondear(lista.reduce((total, r) => total + r[campo], 0));
      return {
        autos_disponibles: disponibles.length,
        autos_vendidos: this.autos.filter((a) => a.estado === VENDIDO).length,
        total_vendido: suma(this.ventas, "total"),
        cantidad_ventas: this.ventas.length,
        clientes: this.clientes.length,
        valor_inventario: suma(disponibles, "precio"),
        descuentos_otorgados: suma(this.ventas, "descuento"),
      };
    }

    /** Conteo de autos disponibles y vendidos por marca, ordenado por marca. */
    inventarioPorMarca() {
      const conteo = new Map();
      for (const auto of this.autos) {
        const fila = conteo.get(auto.marca) || { marca: auto.marca, disponibles: 0, vendidos: 0 };
        if (auto.estado === DISPONIBLE) fila.disponibles += 1; else fila.vendidos += 1;
        conteo.set(auto.marca, fila);
      }
      return [...conteo.values()].sort((a, b) => compararTexto(a.marca, b.marca));
    }
  }

  const api = {
    DISPONIBLE, VENDIDO, ESTADOS_AUTO, TODOS, ErrorNegocio, ErrorValidacion, AutoVentas,
    formatoMoneda, formatoKm, descripcionAuto, normalizar, coincide, fechaActual,
  };
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  } else {
    raiz.AV = raiz.AV || {};
    raiz.AV.logica = api;
  }
})(typeof window !== "undefined" ? window : globalThis);

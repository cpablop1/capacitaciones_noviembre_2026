/**
 * Interfaz web de AutoVentas (RNF-01): cuatro secciones equivalentes a las
 * pestañas de la versión de escritorio — Inventario · Clientes · Ventas · Resumen.
 *
 * Igual que interfaz.py, esta capa no contiene reglas de negocio: lee lo que
 * escribe el usuario, llama al servicio AutoVentas (logica.js) y muestra el
 * resultado o los errores. Tras cada operación se refrescan todas las
 * secciones (HU-05).
 *
 * Seguridad básica: los datos del usuario se insertan siempre con textContent
 * (nunca con innerHTML), de modo que un texto como "<script>" se muestra tal
 * cual y no se ejecuta.
 */
(function (raiz) {
  "use strict";

  const { DISPONIBLE, VENDIDO, ErrorNegocio, ErrorValidacion, formatoMoneda, formatoKm, descripcionAuto } = raiz.AV.logica;
  const SECCIONES = ["inventario", "clientes", "ventas", "resumen"];
  const $ = (id) => document.getElementById(id);
  const pantallaAngosta = () => raiz.matchMedia("(max-width: 1099px)").matches;

  /** Crea un elemento de forma segura: los textos se agregan como nodos de texto. */
  function el(etiqueta, propiedades = {}, ...hijos) {
    const nodo = document.createElement(etiqueta);
    for (const [clave, valor] of Object.entries(propiedades)) {
      if (valor === undefined || valor === null || valor === false) continue;
      if (clave === "clase") nodo.className = valor;
      else if (clave === "texto") nodo.textContent = valor;
      else nodo.setAttribute(clave, valor === true ? "" : valor);
    }
    for (const hijo of hijos.flat()) {
      if (hijo === null || hijo === undefined) continue;
      nodo.append(hijo instanceof Node ? hijo : document.createTextNode(String(hijo)));
    }
    return nodo;
  }

  const etiquetaEstado = (estado) =>
    el("span", { clase: `etiqueta-estado ${estado === VENDIDO ? "vendido" : "disponible"}`, texto: estado });

  /**
   * Llena el cuerpo de una tabla. `filas`: [{id, celdas, clase}]. Cada celda
   * recibe data-label con su encabezado, que en teléfonos se muestra a la izquierda.
   */
  function llenarTabla(tabla, filas, mensajeVacio, { idSeleccionado = null, alSeleccionar = null } = {}) {
    const encabezados = [...tabla.tHead.rows[0].cells].map((celda) => ({
      texto: celda.textContent.trim(), clase: celda.className || null,
    }));
    const nuevas = filas.map(({ id, celdas, clase }) => {
      const clases = [clase, alSeleccionar && "seleccionable", id === idSeleccionado && "seleccionada"];
      const tr = el("tr", { clase: clases.filter(Boolean).join(" ") || null, "data-id": id,
        "aria-current": id === idSeleccionado ? "true" : null });
      celdas.forEach((contenido, i) =>
        tr.append(el("td", { clase: encabezados[i].clase, "data-label": encabezados[i].texto }, contenido)));
      if (alSeleccionar) {
        tr.tabIndex = 0;
        tr.addEventListener("click", () => alSeleccionar(id));
        tr.addEventListener("keydown", (evento) => {
          if (evento.key === "Enter" || evento.key === " ") { evento.preventDefault(); alSeleccionar(id); }
        });
      }
      return tr;
    });
    if (!nuevas.length) {
      nuevas.push(el("tr", {}, el("td", { clase: "vacio", colspan: encabezados.length, texto: mensajeVacio })));
    }
    tabla.tBodies[0].replaceChildren(...nuevas);
  }

  // ------------------------------------------------------------------------
  // Diálogo de confirmación / aviso (equivalente a messagebox)
  // ------------------------------------------------------------------------
  class Dialogo {
    constructor() {
      this.nodo = $("dialogo");
      this.titulo = $("dialogo-titulo");
      this.cuerpo = $("dialogo-cuerpo");
      this.aceptar = $("dialogo-aceptar");
      this.cancelar = $("dialogo-cancelar");
    }

    /** Muestra el diálogo y resuelve true si el usuario pulsa Aceptar. */
    abrir({ titulo, cuerpo, aceptar = "Aceptar", cancelar = "Cancelar", soloAceptar = false, peligro = false }) {
      if (this.nodo.open) this.nodo.close();
      this.titulo.textContent = titulo;
      const partes = Array.isArray(cuerpo) ? cuerpo : [cuerpo];
      this.cuerpo.replaceChildren(...partes.map((p) => (typeof p === "string" ? el("p", { texto: p }) : p)));
      this.aceptar.textContent = aceptar;
      this.aceptar.className = `btn ${peligro && !soloAceptar ? "peligro" : "primario"}`;
      this.cancelar.textContent = cancelar;
      this.cancelar.hidden = soloAceptar;
      this.nodo.classList.toggle("peligro", peligro);
      this.nodo.returnValue = "";
      return new Promise((resolver) => {
        this.nodo.addEventListener("close", () => resolver(this.nodo.returnValue === "aceptar"), { once: true });
        this.nodo.showModal();
        (soloAceptar || !peligro ? this.aceptar : this.cancelar).focus();
      });
    }

    /** Aviso con un botón. `mensajes`: texto o lista de textos (más de uno se muestra como lista). */
    aviso(titulo, mensajes, { peligro = false } = {}) {
      const lista = Array.isArray(mensajes) ? mensajes : [mensajes];
      const cuerpo = lista.length > 1
        ? [el("p", { texto: "Corrija lo siguiente:" }), el("ul", {}, lista.map((m) => el("li", { texto: m })))]
        : lista;
      return this.abrir({ titulo, cuerpo, soloAceptar: true, peligro });
    }
  }

  // ------------------------------------------------------------------------
  // Errores dentro de un formulario: resumen arriba + mensaje bajo cada campo
  // ------------------------------------------------------------------------
  class ErroresFormulario {
    constructor(formulario, prefijo) {
      this.formulario = formulario;
      this.prefijo = prefijo;
      this.resumen = $(`errores-${prefijo}`);
      // Al corregir un campo se quita su marca de error.
      formulario.addEventListener("input", (evento) => {
        if (evento.target.getAttribute("aria-invalid") === "true") {
          evento.target.removeAttribute("aria-invalid");
          const mensaje = $(`error-${evento.target.id}`);
          if (mensaje) mensaje.textContent = "";
        }
      });
    }

    limpiar() {
      this.resumen.hidden = true;
      this.resumen.replaceChildren();
      for (const campo of this.formulario.querySelectorAll("[aria-invalid]")) campo.removeAttribute("aria-invalid");
      for (const mensaje of this.formulario.querySelectorAll(".error-campo")) mensaje.textContent = "";
    }

    mostrar(error, titulo) {
      this.limpiar();
      const contenido = error.errores.length === 1
        ? el("span", { texto: error.errores[0] })
        : el("ul", {}, error.errores.map((m) => el("li", { texto: m })));
      this.resumen.replaceChildren(el("strong", { texto: titulo }), contenido);
      this.resumen.hidden = false;
      let primero = null;
      for (const [campo, mensaje] of Object.entries(error.campos || {})) {
        const entrada = $(`${this.prefijo}-${campo}`);
        if (!entrada) continue;
        entrada.setAttribute("aria-invalid", "true");
        const destino = $(`error-${this.prefijo}-${campo}`);
        if (destino) destino.textContent = mensaje;
        primero = primero || entrada;
      }
      if (primero) primero.focus();
      else this.resumen.scrollIntoView({ block: "nearest" });
    }
  }

  // ------------------------------------------------------------------------
  // Buscador con lista filtrada (equivalente a SelectorBuscable de escritorio)
  // ------------------------------------------------------------------------
  class SelectorBuscable {
    /**
     * `buscar(texto)` devuelve los registros que coinciden (la lógica decide qué
     * coincide); `formatear(registro)` da el texto de cada opción. Al escribir se
     * filtra la lista; con clic, Enter (elige la opción marcada o la primera) o
     * las flechas ↑ ↓ se elige.
     */
    constructor(contenedor, { buscar, formatear, plural, alCambiar }) {
      this.entrada = contenedor.querySelector(".selector-entrada");
      this.lista = contenedor.querySelector(".selector-opciones");
      this.info = contenedor.querySelector(".selector-info");
      this.elegido = contenedor.querySelector(".selector-elegido");
      Object.assign(this, { buscar, formatear, plural, alCambiar });
      this.idSeleccionado = null;
      this.idsVisibles = [];
      this.indiceActivo = -1;

      this.entrada.addEventListener("input", () => { this.indiceActivo = -1; this.refrescar(); });
      this.entrada.addEventListener("keydown", (evento) => this._teclado(evento));
      this.lista.addEventListener("click", (evento) => {
        const opcion = evento.target.closest("li[data-id]");
        if (opcion) this.seleccionar(Number(opcion.dataset.id));
      });
    }

    _teclado(evento) {
      if (evento.key === "ArrowDown" || evento.key === "ArrowUp") {
        evento.preventDefault();
        if (!this.idsVisibles.length) return;
        const paso = evento.key === "ArrowDown" ? 1 : -1;
        const inicio = this.indiceActivo === -1 ? (paso > 0 ? -1 : this.idsVisibles.length) : this.indiceActivo;
        this.indiceActivo = Math.min(Math.max(inicio + paso, 0), this.idsVisibles.length - 1);
        this._marcarActiva();
      } else if (evento.key === "Enter") {
        evento.preventDefault();
        const indice = this.indiceActivo >= 0 ? this.indiceActivo : 0;
        if (this.idsVisibles.length) this.seleccionar(this.idsVisibles[indice]);
      } else if (evento.key === "Escape" && this.entrada.value) {
        evento.preventDefault();
        this.entrada.value = "";
        this.refrescar();
      }
    }

    _idOpcion(id) { return `${this.lista.id}-op-${id}`; }

    _marcarActiva() {
      [...this.lista.children].forEach((li, i) => li.classList.toggle("activa", i === this.indiceActivo));
      const activa = this.lista.children[this.indiceActivo];
      if (activa && activa.dataset.id) {
        this.entrada.setAttribute("aria-activedescendant", activa.id);
        activa.scrollIntoView({ block: "nearest" });
      } else {
        this.entrada.removeAttribute("aria-activedescendant");
      }
    }

    refrescar() {
      const texto = this.entrada.value;
      const encontrados = this.buscar(texto);
      const todos = texto.trim() ? this.buscar("") : encontrados;
      if (this.idSeleccionado !== null && !todos.some((r) => r.id === this.idSeleccionado)) {
        this._fijar(null); // el registro ya no existe o ya no está disponible
      }
      this.idsVisibles = encontrados.map((r) => r.id);
      if (this.indiceActivo >= this.idsVisibles.length) this.indiceActivo = -1;
      this.lista.replaceChildren(...encontrados.map((r) => el("li", {
        id: this._idOpcion(r.id), role: "option", "data-id": r.id,
        "aria-selected": String(r.id === this.idSeleccionado),
      }, el("span", { clase: "id", texto: `#${r.id}` }), this.formatear(r))));
      this._marcarActiva();

      if (!todos.length) {
        this.info.textContent = `No hay ${this.plural}.`;
        this.info.classList.remove("error");
      } else if (!encontrados.length) {
        this.info.textContent = `Sin resultados para «${texto.trim()}».`;
        this.info.classList.add("error");
      } else {
        this.info.textContent = `Mostrando ${encontrados.length} de ${todos.length} ${this.plural}.`;
        this.info.classList.remove("error");
      }
      const registro = todos.find((r) => r.id === this.idSeleccionado);
      this.elegido.textContent = registro ? `✔ #${registro.id}  ${this.formatear(registro)}` : "Ninguno seleccionado.";
      this.elegido.classList.toggle("elegido", Boolean(registro));
    }

    _fijar(id) {
      const cambio = id !== this.idSeleccionado;
      this.idSeleccionado = id;
      if (cambio && this.alCambiar) this.alCambiar();
    }

    seleccionar(id) {
      this._fijar(id);
      this.indiceActivo = this.idsVisibles.indexOf(id);
      this.refrescar();
    }

    limpiar() {
      this.entrada.value = "";
      this.indiceActivo = -1;
      this._fijar(null);
      this.refrescar();
    }
  }

  // ------------------------------------------------------------------------
  // Sección Inventario (RF-01, RF-02, HU-01, HU-02)
  // ------------------------------------------------------------------------
  class SeccionInventario {
    constructor(app) {
      this.app = app;
      this.s = app.servicio;
      this.idEdicion = null;
      this.formulario = $("form-auto");
      this.errores = new ErroresFormulario(this.formulario, "auto");
      this.campos = ["marca", "modelo", "anio", "precio", "kilometraje"].map((c) => $(`auto-${c}`));
      this.tabla = $("tabla-autos");
      this.filtros = {
        texto: $("filtro-texto"), marca: $("filtro-marca"), anio: $("filtro-anio"),
        precioMin: $("filtro-precio-min"), precioMax: $("filtro-precio-max"), estado: $("filtro-estado"),
      };

      this.formulario.addEventListener("submit", (evento) => { evento.preventDefault(); this.guardar(); });
      this.formulario.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape") this.limpiarFormulario();
      });
      $("btn-limpiar-auto").addEventListener("click", () => this.limpiarFormulario());
      $("btn-eliminar-auto").addEventListener("click", () => this.eliminar());
      $("btn-vender-auto").addEventListener("click", () => this.idEdicion !== null && app.venderAuto(this.idEdicion));
      const formFiltros = $("filtros-autos");
      formFiltros.addEventListener("input", () => this.refrescarTabla());
      formFiltros.addEventListener("change", () => this.refrescarTabla());
      formFiltros.addEventListener("submit", (evento) => evento.preventDefault());
      formFiltros.addEventListener("reset", () => setTimeout(() => this.refrescarTabla(), 0));
      $("ayuda-auto-anio").textContent = `1990 – ${raiz.AV.validaciones.anioActual()}`;
    }

    refrescar() {
      $("lista-marcas").replaceChildren(...this.s.marcas().map((m) => el("option", { value: m })));
      if (this.idEdicion !== null && !this.s.autos.some((a) => a.id === this.idEdicion)) {
        this.limpiarFormulario({ enfocar: false });
      }
      this.actualizarModo();
      this.refrescarTabla();
    }

    refrescarTabla() {
      const f = this.filtros;
      for (const entrada of Object.values(f)) entrada.removeAttribute("aria-invalid");
      const info = $("info-autos");
      let autos;
      try {
        autos = this.s.filtrarAutos({
          texto: f.texto.value, marca: f.marca.value, anio: f.anio.value,
          precioMin: f.precioMin.value, precioMax: f.precioMax.value, estado: f.estado.value,
        });
      } catch (error) {
        if (!(error instanceof ErrorValidacion)) throw error;
        for (const campo of Object.keys(error.campos)) f[campo] && f[campo].setAttribute("aria-invalid", "true");
        info.textContent = `Filtros no válidos: ${error.errores.join(" ")}`;
        info.classList.add("error");
        llenarTabla(this.tabla, [], "Corrija los filtros para ver resultados.");
        return;
      }
      const total = this.s.autos.length;
      const filas = autos.map((a) => ({
        id: a.id,
        clase: a.estado === VENDIDO ? "vendido" : null,
        celdas: [a.id, a.marca, a.modelo, a.anio, formatoMoneda(a.precio), formatoKm(a.kilometraje), etiquetaEstado(a.estado)],
      }));
      llenarTabla(this.tabla, filas,
        total ? "Sin resultados: ningún auto coincide con los filtros aplicados."
          : "Aún no hay autos registrados. Use el formulario para agregar el primero.",
        { idSeleccionado: this.idEdicion, alSeleccionar: (id) => this.seleccionar(id) });
      info.textContent = autos.length ? `Mostrando ${autos.length} de ${total} auto(s).`
        : total ? "Sin resultados." : "Inventario vacío.";
      info.classList.toggle("error", !autos.length && total > 0);
    }

    seleccionar(id) {
      const auto = this.s.obtenerAuto(id);
      this.idEdicion = id;
      const valores = [auto.marca, auto.modelo, auto.anio, auto.precio.toFixed(2), auto.kilometraje];
      this.campos.forEach((campo, i) => { campo.value = valores[i]; });
      this.errores.limpiar();
      this.actualizarModo();
      this.refrescarTabla();
      if (pantallaAngosta()) this.formulario.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    actualizarModo() {
      const auto = this.idEdicion === null ? null : this.s.autos.find((a) => a.id === this.idEdicion);
      const estado = $("auto-estado");
      const vendido = Boolean(auto && auto.estado === VENDIDO);
      $("titulo-form-auto").textContent = auto ? `Auto #${auto.id}` : "Nuevo auto";
      $("btn-guardar-auto").textContent = auto ? "Actualizar auto" : "Guardar auto";
      $("btn-guardar-auto").disabled = vendido;
      $("btn-eliminar-auto").disabled = !auto || vendido;
      $("btn-vender-auto").disabled = !auto;
      estado.textContent = !auto ? `${DISPONIBLE} (se asigna al guardar)` : vendido ? "Vendido — solo lectura" : DISPONIBLE;
      estado.classList.toggle("disponible", Boolean(auto) && !vendido);
      for (const campo of this.campos) campo.disabled = vendido;
    }

    limpiarFormulario({ enfocar = true } = {}) {
      this.idEdicion = null;
      this.formulario.reset();
      this.errores.limpiar();
      this.actualizarModo();
      this.refrescarTabla();
      if (enfocar) this.campos[0].focus();
    }

    guardar() {
      if ($("btn-guardar-auto").disabled) return;
      const datos = this.campos.map((campo) => campo.value);
      const nuevo = this.idEdicion === null;
      const auto = this.app.ejecutar(
        () => (nuevo ? this.s.registrarAuto(...datos) : this.s.editarAuto(this.idEdicion, ...datos)),
        this.errores);
      if (!auto) return;
      this.limpiarFormulario();
      this.app.notificarCambio();
      const visible = Boolean(this.tabla.querySelector(`tr[data-id="${auto.id}"]`));
      this.app.aviso(`Auto #${auto.id} ${descripcionAuto(auto)} ${nuevo ? "registrado" : "actualizado"} ` +
        `con estado «${auto.estado}»${visible ? "" : " (no se muestra por los filtros activos)"}.`);
    }

    async eliminar() {
      if (this.idEdicion === null) return;
      const auto = this.s.obtenerAuto(this.idEdicion);
      const confirmado = await this.app.dialogo.abrir({
        titulo: "Eliminar auto",
        cuerpo: [`¿Eliminar el auto #${auto.id} ${descripcionAuto(auto)}?`, "Esta acción no se puede deshacer."],
        aceptar: "Eliminar", peligro: true,
      });
      if (!confirmado) return;
      if (this.app.ejecutar(() => { this.s.eliminarAuto(auto.id); return true; })) {
        this.limpiarFormulario();
        this.app.notificarCambio();
        this.app.aviso(`Auto #${auto.id} ${descripcionAuto(auto)} eliminado.`);
      }
    }
  }

  // ------------------------------------------------------------------------
  // Sección Clientes (RF-03, HU-03)
  // ------------------------------------------------------------------------
  class SeccionClientes {
    constructor(app) {
      this.app = app;
      this.s = app.servicio;
      this.idEdicion = null;
      this.formulario = $("form-cliente");
      this.errores = new ErroresFormulario(this.formulario, "cliente");
      this.campos = ["nombre", "telefono", "correo", "documento"].map((c) => $(`cliente-${c}`));
      this.tabla = $("tabla-clientes");
      this.buscar = $("buscar-clientes");

      this.formulario.addEventListener("submit", (evento) => { evento.preventDefault(); this.guardar(); });
      this.formulario.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape") this.limpiarFormulario();
      });
      $("btn-limpiar-cliente").addEventListener("click", () => this.limpiarFormulario());
      $("btn-eliminar-cliente").addEventListener("click", () => this.eliminar());
      this.buscar.addEventListener("input", () => this.refrescarTabla());
    }

    refrescar() {
      if (this.idEdicion !== null && !this.s.clientes.some((c) => c.id === this.idEdicion)) {
        this.limpiarFormulario({ enfocar: false });
      }
      this.actualizarModo();
      this.refrescarTabla();
    }

    refrescarTabla() {
      const compras = this.s.comprasPorCliente();
      const clientes = this.s.buscarClientes(this.buscar.value); // ya vienen ordenados por id
      const total = this.s.clientes.length;
      llenarTabla(this.tabla, clientes.map((c) => ({
        id: c.id, celdas: [c.id, c.nombre, c.documento, c.telefono, c.correo, compras[c.id] || 0],
      })), total ? "Sin resultados para la búsqueda." : "Aún no hay clientes registrados.",
      { idSeleccionado: this.idEdicion, alSeleccionar: (id) => this.seleccionar(id) });
      $("info-clientes").textContent = `Mostrando ${clientes.length} de ${total} cliente(s).`;
    }

    seleccionar(id) {
      const cliente = this.s.obtenerCliente(id);
      this.idEdicion = id;
      const valores = [cliente.nombre, cliente.telefono, cliente.correo, cliente.documento];
      this.campos.forEach((campo, i) => { campo.value = valores[i]; });
      this.errores.limpiar();
      this.actualizarModo();
      this.refrescarTabla();
      if (pantallaAngosta()) this.formulario.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    actualizarModo() {
      const editando = this.idEdicion !== null;
      $("titulo-form-cliente").textContent = editando ? `Cliente #${this.idEdicion}` : "Nuevo cliente";
      $("btn-guardar-cliente").textContent = editando ? "Actualizar cliente" : "Guardar cliente";
      $("btn-eliminar-cliente").disabled = !editando;
    }

    limpiarFormulario({ enfocar = true } = {}) {
      this.idEdicion = null;
      this.formulario.reset();
      this.errores.limpiar();
      this.actualizarModo();
      this.refrescarTabla();
      if (enfocar) this.campos[0].focus();
    }

    guardar() {
      const datos = this.campos.map((campo) => campo.value);
      const nuevo = this.idEdicion === null;
      const cliente = this.app.ejecutar(
        () => (nuevo ? this.s.registrarCliente(...datos) : this.s.editarCliente(this.idEdicion, ...datos)),
        this.errores);
      if (!cliente) return;
      this.limpiarFormulario();
      this.app.notificarCambio();
      this.app.aviso(`Cliente ${cliente.nombre} (${cliente.documento}) ${nuevo ? "registrado" : "actualizado"}.`);
    }

    async eliminar() {
      if (this.idEdicion === null) return;
      const cliente = this.s.obtenerCliente(this.idEdicion);
      const confirmado = await this.app.dialogo.abrir({
        titulo: "Eliminar cliente",
        cuerpo: [`¿Eliminar al cliente ${cliente.nombre}?`, "Esta acción no se puede deshacer."],
        aceptar: "Eliminar", peligro: true,
      });
      if (!confirmado) return;
      if (this.app.ejecutar(() => { this.s.eliminarCliente(cliente.id); return true; })) {
        this.limpiarFormulario();
        this.app.notificarCambio();
        this.app.aviso(`Cliente ${cliente.nombre} eliminado.`);
      }
    }
  }

  // ------------------------------------------------------------------------
  // Sección Ventas (RF-04, RF-05, HU-04)
  // ------------------------------------------------------------------------
  class SeccionVentas {
    constructor(app) {
      this.app = app;
      this.s = app.servicio;
      this.descuento = $("venta-descuento");
      this.selCliente = new SelectorBuscable($("selector-cliente"), {
        buscar: (texto) => this.s.buscarClientes(texto),
        formatear: (c) => `${c.nombre} — ${c.documento}`,
        plural: "clientes",
        alCambiar: () => this.actualizarDetalle(),
      });
      this.selAuto = new SelectorBuscable($("selector-auto"), {
        buscar: (texto) => this.s.buscarAutosDisponibles(texto),
        formatear: (a) => `${descripcionAuto(a)} — ${formatoMoneda(a.precio)}`,
        plural: "autos disponibles",
        alCambiar: () => this.actualizarDetalle(),
      });
      this.descuento.addEventListener("input", () => this.actualizarDetalle());
      this.descuento.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter") { evento.preventDefault(); this.registrar(); }
      });
      $("btn-registrar-venta").addEventListener("click", () => this.registrar());
    }

    refrescar() {
      this.selCliente.refrescar();
      this.selAuto.refrescar();
      this.actualizarDetalle();
      const historial = this.s.historialVentas();
      llenarTabla($("tabla-ventas"), historial.map((h) => ({
        id: h.id,
        celdas: [h.id, h.fecha, h.cliente, h.documento, h.auto, formatoMoneda(h.precio),
          `${h.porcentaje_descuento} %`, formatoMoneda(h.descuento), formatoMoneda(h.total)],
      })), "Aún no hay ventas registradas.");
      const total = historial.reduce((suma, h) => suma + h.total, 0);
      $("info-ventas").textContent = `${historial.length} venta(s) — total vendido ${formatoMoneda(total)}`;
    }

    preseleccionarAuto(id) {
      this.selAuto.entrada.value = "";
      this.selAuto.seleccionar(id);
      this.selCliente.entrada.focus();
    }

    actualizarDetalle() {
      const precio = $("venta-precio");
      const monto = $("venta-monto-descuento");
      const total = $("venta-total");
      const mensaje = $("venta-error");
      mensaje.textContent = "";
      this.descuento.removeAttribute("aria-invalid");
      const idAuto = this.selAuto.idSeleccionado;
      if (idAuto === null) {
        precio.textContent = monto.textContent = total.textContent = "—";
        return;
      }
      try {
        const calculo = this.s.calcularVenta(idAuto, this.descuento.value);
        precio.textContent = formatoMoneda(calculo.precio);
        monto.textContent = `− ${formatoMoneda(calculo.descuento)} (${calculo.porcentaje_descuento} %)`;
        total.textContent = formatoMoneda(calculo.total);
      } catch (error) {
        if (!(error instanceof ErrorValidacion)) throw error;
        precio.textContent = formatoMoneda(this.s.obtenerAuto(idAuto).precio);
        monto.textContent = total.textContent = "—";
        mensaje.textContent = error.errores[0];
        this.descuento.setAttribute("aria-invalid", "true");
      }
    }

    async registrar() {
      const idCliente = this.selCliente.idSeleccionado;
      const idAuto = this.selAuto.idSeleccionado;
      const faltan = [];
      if (idCliente === null) faltan.push("Seleccione un cliente.");
      if (idAuto === null) faltan.push("Seleccione un auto disponible.");
      if (faltan.length) {
        this.app.dialogo.aviso("Datos no válidos", faltan, { peligro: true });
        return;
      }
      const calculo = this.app.ejecutar(() => this.s.calcularVenta(idAuto, this.descuento.value));
      if (!calculo) return;
      const cliente = this.s.obtenerCliente(idCliente);
      const auto = this.s.obtenerAuto(idAuto);
      const detalle = el("dl", {},
        el("dt", { texto: "Cliente" }), el("dd", { texto: `${cliente.nombre} (${cliente.documento})` }),
        el("dt", { texto: "Auto" }), el("dd", { texto: `#${auto.id} ${descripcionAuto(auto)}` }),
        el("dt", { texto: "Precio" }), el("dd", { texto: formatoMoneda(calculo.precio) }),
        el("dt", { texto: "Descuento" }),
        el("dd", { texto: `− ${formatoMoneda(calculo.descuento)} (${calculo.porcentaje_descuento} %)` }),
        el("dt", { texto: "Total" }), el("dd", { clase: "total", texto: formatoMoneda(calculo.total) }));
      const confirmado = await this.app.dialogo.abrir({
        titulo: "Confirmar venta",
        cuerpo: [detalle, "Al confirmar, el auto pasará a estado «Vendido». ¿Continuar?"],
        aceptar: "Registrar venta",
      });
      if (!confirmado) return;
      const venta = this.app.ejecutar(() => this.s.registrarVenta(idCliente, idAuto, this.descuento.value));
      if (!venta) return;
      this.selAuto.limpiar();
      this.descuento.value = "0";
      this.app.notificarCambio();
      this.app.aviso(`Venta No. ${venta.id} registrada: ${descripcionAuto(auto)} a ${cliente.nombre} ` +
        `por ${formatoMoneda(venta.total)}. El auto ahora está «Vendido».`);
    }
  }

  // ------------------------------------------------------------------------
  // Sección Resumen (RF-06, HU-05)
  // ------------------------------------------------------------------------
  class SeccionResumen {
    constructor(app) { this.s = app.servicio; }

    refrescar() {
      const resumen = this.s.resumen();
      const dinero = new Set(["total_vendido", "valor_inventario"]);
      for (const clave of ["autos_disponibles", "autos_vendidos", "total_vendido", "cantidad_ventas", "clientes", "valor_inventario"]) {
        $(`kpi-${clave}`).textContent = dinero.has(clave) ? formatoMoneda(resumen[clave]) : resumen[clave];
      }
      llenarTabla($("tabla-ultimas"), this.s.historialVentas().slice(0, 5).map((h) => ({
        id: h.id, celdas: [h.fecha, h.cliente, h.auto, formatoMoneda(h.total)],
      })), "Aún no hay ventas registradas.");
      llenarTabla($("tabla-marcas"), this.s.inventarioPorMarca().map((m, i) => ({
        id: i, celdas: [m.marca, m.disponibles, m.vendidos],
      })), "Sin autos en inventario.");
    }
  }

  // ------------------------------------------------------------------------
  // Aplicación: navegación entre secciones, mensajes y manejo de errores
  // ------------------------------------------------------------------------
  class Aplicacion {
    constructor(servicio, { aviso = null } = {}) {
      this.servicio = servicio;
      this.dialogo = new Dialogo();
      this.inventario = new SeccionInventario(this);
      this.clientes = new SeccionClientes(this);
      this.ventas = new SeccionVentas(this);
      this.resumen = new SeccionResumen(this);
      this.secciones = [this.inventario, this.clientes, this.ventas, this.resumen];
      this._iniciarNavegacion();
      this.notificarCambio();
      if (aviso) this.dialogo.aviso("Datos", aviso);
    }

    _iniciarNavegacion() {
      this.pestanas = [...document.querySelectorAll(".pestanas [role=tab]")];
      for (const pestana of this.pestanas) {
        pestana.addEventListener("click", () => this.mostrarSeccion(pestana.dataset.seccion));
        pestana.addEventListener("keydown", (evento) => {
          const indice = this.pestanas.indexOf(pestana);
          const destino = { ArrowRight: indice + 1, ArrowLeft: indice - 1, Home: 0, End: this.pestanas.length - 1 }[evento.key];
          if (destino === undefined) return;
          evento.preventDefault();
          const siguiente = this.pestanas[(destino + this.pestanas.length) % this.pestanas.length];
          siguiente.focus();
          this.mostrarSeccion(siguiente.dataset.seccion);
        });
      }
      raiz.addEventListener("hashchange", () => this.mostrarSeccion(location.hash.slice(1), { cambiarDireccion: false }));
      this.mostrarSeccion(location.hash.slice(1), { cambiarDireccion: false });
    }

    /** Muestra una sección y oculta las demás. La dirección (#ventas) permite volver o compartir el enlace. */
    mostrarSeccion(nombre, { cambiarDireccion = true } = {}) {
      const actual = SECCIONES.includes(nombre) ? nombre : "inventario";
      for (const pestana of this.pestanas) {
        const activa = pestana.dataset.seccion === actual;
        pestana.setAttribute("aria-selected", String(activa));
        pestana.tabIndex = activa ? 0 : -1;
      }
      for (const id of SECCIONES) $(id).hidden = id !== actual;
      if (cambiarDireccion && location.hash !== `#${actual}`) history.replaceState(null, "", `#${actual}`);
    }

    /** Refresca todas las secciones para que reflejen el último cambio (HU-05). */
    notificarCambio() {
      for (const seccion of this.secciones) seccion.refrescar();
    }

    /**
     * Mensaje breve de confirmación en la esquina (equivalente a la barra de
     * estado de escritorio). Los errores no usan este aviso: ya se muestran en
     * el formulario o en un diálogo. Máximo dos a la vez; se cierran a los 5 s
     * o con un clic, para no tapar el contenido.
     */
    aviso(texto) {
      const contenedor = $("avisos");
      const nodo = el("div", { clase: "aviso", role: "status", title: "Clic para cerrar", texto });
      nodo.addEventListener("click", () => nodo.remove());
      contenedor.append(nodo);
      while (contenedor.children.length > 2) contenedor.firstElementChild.remove();
      setTimeout(() => nodo.remove(), 5000);
    }

    /**
     * Ejecuta una operación del servicio y muestra sus errores: dentro del
     * formulario si se indica uno, o en un diálogo. Devuelve null si falló.
     */
    ejecutar(accion, errores = null) {
      try {
        return accion();
      } catch (error) {
        if (error instanceof ErrorValidacion) {
          const titulo = error instanceof ErrorNegocio ? "Operación bloqueada" : "Datos no válidos";
          if (errores) errores.mostrar(error, titulo);
          else this.dialogo.aviso(titulo, error.errores, { peligro: true });
        } else {
          console.error(error);
          this.dialogo.aviso("Error al guardar", [
            "No se pudieron guardar los datos en este navegador.",
            `Detalle: ${error && error.message ? error.message : error}`,
            "La operación se canceló; no se perdió información.",
          ], { peligro: true });
        }
        return null;
      }
    }

    /** Desde Inventario: lleva el auto a Ventas, o bloquea si ya fue vendido (CP-03). */
    venderAuto(id) {
      const auto = this.servicio.obtenerAuto(id);
      if (auto.estado !== DISPONIBLE) {
        const mensaje = `El auto #${auto.id} ${descripcionAuto(auto)} no está disponible ` +
          `(estado: ${auto.estado}). Solo se pueden vender autos «Disponible».`;
        this.dialogo.aviso("Operación bloqueada", mensaje, { peligro: true });
        return;
      }
      this.mostrarSeccion("ventas");
      this.ventas.preseleccionarAuto(id);
    }
  }

  raiz.AV = raiz.AV || {};
  raiz.AV.interfaz = { Aplicacion, SelectorBuscable, llenarTabla, el };
})(window);

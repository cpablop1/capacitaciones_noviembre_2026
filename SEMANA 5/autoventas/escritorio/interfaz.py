"""Interfaz gráfica de AutoVentas con tkinter (RNF-01).

Ventana con cuatro pestañas (ttk.Notebook): Inventario · Clientes · Ventas ·
Resumen. La interfaz no contiene reglas de negocio: solo lee lo que escribe el
usuario, llama al servicio AutoVentas (logica.py) y muestra el resultado o los
errores. Tras cada operación se refrescan todas las pestañas (HU-05).
"""

import tkinter as tk
from tkinter import messagebox, ttk

from logica import (DISPONIBLE, ESTADOS_AUTO, TODOS, VENDIDO, ErrorNegocio, descripcion_auto,
                    formato_km, formato_moneda)
from validaciones import DESCUENTO_MAXIMO, ErrorValidacion, anio_actual

# ---- Paleta y tipografía -------------------------------------------------
FONDO = "#EEF2F7"
TARJETA = "#FFFFFF"
ENCABEZADO = "#0F172A"
TEXTO = "#1E293B"
TEXTO_SUAVE = "#64748B"
BORDE = "#D8E0EA"
PRIMARIO = "#2563EB"
PRIMARIO_OSCURO = "#1D4ED8"
PELIGRO = "#DC2626"
PELIGRO_OSCURO = "#B91C1C"
EXITO = "#15803D"
ADVERTENCIA = "#B45309"
FILA_PAR = "#F6F8FB"
SELECCION = "#DBEAFE"

FUENTE = ("Segoe UI", 10)
FUENTE_NEGRITA = ("Segoe UI", 10, "bold")
FUENTE_TITULO = ("Segoe UI", 18, "bold")
FUENTE_SUBTITULO = ("Segoe UI", 12, "bold")
FUENTE_KPI = ("Segoe UI", 22, "bold")
FUENTE_TOTAL = ("Segoe UI", 16, "bold")

# Factor de escala de la pantalla (1.0 = 96 ppp; 1.25 con escalado de Windows al 125 %).
# Las fuentes en puntos escalan solas; los anchos en píxeles se multiplican por este factor.
_escala = 1.0


def px(valor):
    return int(round(valor * _escala))


def aplicar_estilos(raiz):
    global _escala
    _escala = max(1.0, raiz.winfo_fpixels("1i") / 96)
    raiz.configure(background=FONDO)
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    estilo.configure(".", font=FUENTE, background=FONDO, foreground=TEXTO)
    estilo.configure("TFrame", background=FONDO)
    estilo.configure("Tarjeta.TFrame", background=TARJETA, relief="solid", borderwidth=1,
                     bordercolor=BORDE)
    estilo.configure("Interior.TFrame", background=TARJETA)
    estilo.configure("TLabel", background=TARJETA, foreground=TEXTO)
    estilo.configure("Fondo.TLabel", background=FONDO)
    estilo.configure("Titulo.TLabel", background=TARJETA, font=FUENTE_SUBTITULO)
    estilo.configure("Suave.TLabel", background=TARJETA, foreground=TEXTO_SUAVE)
    estilo.configure("Error.TLabel", background=TARJETA, foreground=PELIGRO)
    estilo.configure("Exito.TLabel", background=TARJETA, foreground=EXITO)
    estilo.configure("Total.TLabel", background=TARJETA, foreground=PRIMARIO, font=FUENTE_TOTAL)
    estilo.configure("Vacio.TLabel", background=TARJETA, foreground=TEXTO_SUAVE,
                     font=("Segoe UI", 11, "italic"), padding=12)
    estilo.configure("KpiValor.TLabel", background=TARJETA, font=FUENTE_KPI)
    estilo.configure("KpiTitulo.TLabel", background=TARJETA, foreground=TEXTO_SUAVE,
                     font=FUENTE_NEGRITA)
    estilo.configure("Barra.TLabel", background=TARJETA, foreground=TEXTO_SUAVE, padding=(14, 6))
    estilo.configure("BarraExito.TLabel", background=TARJETA, foreground=EXITO, padding=(14, 6))
    estilo.configure("BarraError.TLabel", background=TARJETA, foreground=PELIGRO, padding=(14, 6))

    estilo.configure("TEntry", fieldbackground="white", bordercolor=BORDE, padding=5)
    estilo.configure("TSpinbox", fieldbackground="white", bordercolor=BORDE, padding=5)
    estilo.configure("TCombobox", fieldbackground="white", bordercolor=BORDE, padding=5)
    estilo.map("TCombobox", fieldbackground=[("readonly", "white")],
               selectbackground=[("readonly", "white")], selectforeground=[("readonly", TEXTO)])
    estilo.map("TEntry", fieldbackground=[("readonly", FILA_PAR), ("disabled", FILA_PAR)])

    estilo.configure("TButton", padding=(12, 7), background="#E2E8F0", bordercolor=BORDE,
                     focusthickness=0)
    estilo.map("TButton", background=[("disabled", "#F1F5F9"), ("active", "#CBD5E1")],
               foreground=[("disabled", "#94A3B8")])
    estilo.configure("Primario.TButton", background=PRIMARIO, foreground="white",
                     font=FUENTE_NEGRITA, bordercolor=PRIMARIO)
    estilo.map("Primario.TButton", background=[("disabled", "#93C5FD"), ("active", PRIMARIO_OSCURO)],
               foreground=[("disabled", "white")])
    estilo.configure("Peligro.TButton", background=TARJETA, foreground=PELIGRO, bordercolor=PELIGRO)
    estilo.map("Peligro.TButton", background=[("disabled", TARJETA), ("active", "#FEE2E2")],
               foreground=[("disabled", "#FCA5A5"), ("active", PELIGRO_OSCURO)],
               bordercolor=[("disabled", "#FECACA")])

    estilo.configure("TNotebook", background=FONDO, borderwidth=0, tabmargins=(14, 8, 14, 0))
    estilo.configure("TNotebook.Tab", padding=(20, 9), font=FUENTE_NEGRITA, background="#DCE3EC",
                     foreground=TEXTO_SUAVE, borderwidth=0)
    estilo.map("TNotebook.Tab", background=[("selected", TARJETA)],
               foreground=[("selected", PRIMARIO)], expand=[("selected", (0, 2, 0, 0))])

    estilo.configure("Treeview", background=TARJETA, fieldbackground=TARJETA, rowheight=px(28),
                     bordercolor=BORDE, borderwidth=0)
    estilo.map("Treeview", background=[("selected", SELECCION)], foreground=[("selected", TEXTO)])
    estilo.configure("Treeview.Heading", font=FUENTE_NEGRITA, background="#F1F5F9",
                     foreground=TEXTO, padding=(6, 6), relief="flat")
    estilo.map("Treeview.Heading", background=[("active", "#E2E8F0")])


def mostrar_errores(error, titulo="Datos no válidos"):
    if len(error.errores) == 1:
        messagebox.showerror(titulo, error.errores[0])
    else:
        lista = "\n".join(f"• {mensaje}" for mensaje in error.errores)
        messagebox.showerror(titulo, f"Corrija lo siguiente:\n\n{lista}")


# --------------------------------------------------------------------------
# Componentes reutilizables
# --------------------------------------------------------------------------
class Tabla:
    """Treeview con barra de desplazamiento, filas alternadas y mensaje cuando está vacía."""

    def __init__(self, padre, columnas, alto=12):
        self.marco = ttk.Frame(padre, style="Interior.TFrame")
        self.tree = ttk.Treeview(self.marco, columns=[c[0] for c in columnas], show="headings",
                                 height=alto, selectmode="browse")
        for clave, titulo, ancho, alineacion in columnas:
            self.tree.heading(clave, text=titulo, anchor=alineacion)
            self.tree.column(clave, width=px(ancho), minwidth=px(45), anchor=alineacion, stretch=True)
        barra = ttk.Scrollbar(self.marco, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=barra.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        self.marco.rowconfigure(0, weight=1)
        self.marco.columnconfigure(0, weight=1)
        self.tree.tag_configure("par", background=FILA_PAR)
        self.tree.tag_configure("vendido", foreground=TEXTO_SUAVE)
        self.tree.tag_configure("disponible", foreground=EXITO)
        self._vacio = ttk.Label(self.marco, style="Vacio.TLabel", anchor="center", justify="center")

    def llenar(self, filas, mensaje_vacio=""):
        """`filas`: lista de (id, valores, etiquetas)."""
        self.tree.delete(*self.tree.get_children())
        for indice, (iid, valores, etiquetas) in enumerate(filas):
            tags = tuple(etiquetas) + (("par",) if indice % 2 else ())
            self.tree.insert("", "end", iid=str(iid), values=valores, tags=tags)
        if filas:
            self._vacio.place_forget()
        else:
            self._vacio.configure(text=mensaje_vacio)
            self._vacio.place(relx=0.5, rely=0.55, anchor="center")

    def seleccionado(self):
        seleccion = self.tree.selection()
        return int(seleccion[0]) if seleccion else None

    def mostrar(self, iid):
        if self.tree.exists(str(iid)):
            self.tree.see(str(iid))
            return True
        return False


class SelectorBuscable(ttk.Frame):
    """Cuadro de búsqueda con una lista filtrada debajo, para elegir un registro.

    `buscar(texto)` devuelve los registros que coinciden (la lógica decide qué
    coincide); `formatear(registro)` da el texto de cada fila. Al escribir se
    filtra la lista; con clic, Enter (elige el primero) o las flechas se elige.
    """

    def __init__(self, padre, buscar, formatear, plural, al_cambiar=None, alto=6):
        super().__init__(padre, style="Interior.TFrame")
        self._buscar, self._formatear, self._plural = buscar, formatear, plural
        self._al_cambiar = al_cambiar
        self._ids_visibles = []
        self.id_seleccionado = None
        self.columnconfigure(0, weight=1)

        self.v_texto = tk.StringVar()
        self.entrada = ttk.Entry(self, textvariable=self.v_texto)
        self.entrada.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.lista = tk.Listbox(self, height=alto, activestyle="none", exportselection=False,
                                font=FUENTE, relief="flat", borderwidth=0, highlightthickness=1,
                                highlightbackground=BORDE, highlightcolor=PRIMARIO,
                                background="white", foreground=TEXTO,
                                selectbackground=SELECCION, selectforeground=TEXTO)
        barra = ttk.Scrollbar(self, orient="vertical", command=self.lista.yview)
        self.lista.configure(yscrollcommand=barra.set)
        self.lista.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        barra.grid(row=1, column=1, sticky="ns", pady=(4, 0))
        self.lbl_info = ttk.Label(self, style="Suave.TLabel")
        self.lbl_info.grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 0))
        self.lbl_elegido = ttk.Label(self, style="Suave.TLabel")
        self.lbl_elegido.grid(row=3, column=0, columnspan=2, sticky="w")

        self.v_texto.trace_add("write", lambda *_: self.refrescar())
        self.lista.bind("<<ListboxSelect>>", self._al_elegir)
        self.entrada.bind("<Return>", self._elegir_primero)
        self.entrada.bind("<Down>", self._bajar_a_lista)
        self.entrada.bind("<Escape>", lambda _e: self.v_texto.set(""))

    def refrescar(self):
        texto = self.v_texto.get()
        encontrados = self._buscar(texto)
        todos = self._buscar("") if texto.strip() else encontrados
        if self.id_seleccionado is not None and all(r["id"] != self.id_seleccionado for r in todos):
            self._fijar(None)  # el registro ya no existe o ya no está disponible

        self.lista.delete(0, "end")
        self._ids_visibles = [r["id"] for r in encontrados]
        for registro in encontrados:
            self.lista.insert("end", "  " + self._formatear(registro))
        if self.id_seleccionado in self._ids_visibles:
            indice = self._ids_visibles.index(self.id_seleccionado)
            self.lista.selection_set(indice)
            self.lista.see(indice)

        if not todos:
            self.lbl_info.configure(text=f"No hay {self._plural}.", style="Suave.TLabel")
        elif not encontrados:
            self.lbl_info.configure(text=f"Sin resultados para «{texto.strip()}».", style="Error.TLabel")
        else:
            self.lbl_info.configure(text=f"Mostrando {len(encontrados)} de {len(todos)} {self._plural}.",
                                    style="Suave.TLabel")
        self._mostrar_elegido(todos)

    def _mostrar_elegido(self, todos):
        registro = next((r for r in todos if r["id"] == self.id_seleccionado), None)
        if registro is None:
            self.lbl_elegido.configure(text="Ninguno seleccionado.", style="Suave.TLabel")
        else:
            self.lbl_elegido.configure(text="✔ " + self._formatear(registro), style="Exito.TLabel")

    def _fijar(self, id_registro):
        cambio = id_registro != self.id_seleccionado
        self.id_seleccionado = id_registro
        if cambio and self._al_cambiar:
            self._al_cambiar()

    def _al_elegir(self, _evento=None):
        seleccion = self.lista.curselection()
        if seleccion:
            self._fijar(self._ids_visibles[seleccion[0]])
            self._mostrar_elegido(self._buscar(""))

    def _elegir_primero(self, _evento=None):
        if self._ids_visibles:
            self.seleccionar(self._ids_visibles[0])
        return "break"

    def _bajar_a_lista(self, _evento=None):
        if self._ids_visibles:
            self.lista.focus_set()
            if not self.lista.curselection():
                self.lista.selection_set(0)
                self._al_elegir()
        return "break"

    def seleccionar(self, id_registro):
        self._fijar(id_registro)
        self.refrescar()

    def limpiar(self):
        self._fijar(None)
        self.v_texto.set("")  # dispara refrescar()


def tarjeta(padre, titulo=None, padding=16):
    marco = ttk.Frame(padre, style="Tarjeta.TFrame", padding=padding)
    if titulo:
        ttk.Label(marco, text=titulo, style="Titulo.TLabel").pack(anchor="w", pady=(0, 10))
    return marco


def campo(padre, etiqueta, widget_factory, fila, ayuda=None):
    """Etiqueta encima del control, en la columna 0 de un grid."""
    ttk.Label(padre, text=etiqueta, font=FUENTE_NEGRITA).grid(row=fila * 2, column=0, sticky="w",
                                                              pady=(8, 2))
    widget = widget_factory(padre)
    widget.grid(row=fila * 2 + 1, column=0, sticky="ew")
    if ayuda:
        ttk.Label(padre, text=ayuda, style="Suave.TLabel").grid(row=fila * 2, column=0, sticky="e",
                                                                pady=(8, 2))
    return widget


# --------------------------------------------------------------------------
# Pestaña Inventario (RF-01, RF-02, HU-01, HU-02)
# --------------------------------------------------------------------------
class PestanaInventario(ttk.Frame):
    COLUMNAS = [("id", "ID", 50, "center"), ("marca", "Marca", 120, "w"),
                ("modelo", "Modelo", 140, "w"), ("anio", "Año", 70, "center"),
                ("precio", "Precio", 120, "e"), ("km", "Kilometraje", 120, "e"),
                ("estado", "Estado", 110, "center")]

    def __init__(self, padre, app):
        super().__init__(padre, padding=14)
        self.app = app
        self.servicio = app.servicio
        self.id_edicion = None
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._crear_formulario()
        self._crear_listado()
        self._actualizar_modo()

    # ---- construcción --------------------------------------------------
    def _crear_formulario(self):
        caja = tarjeta(self)
        caja.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        self.lbl_titulo = ttk.Label(caja, style="Titulo.TLabel")
        self.lbl_titulo.pack(anchor="w")
        formulario = ttk.Frame(caja, style="Interior.TFrame")
        formulario.pack(fill="x")
        formulario.columnconfigure(0, weight=1, minsize=250)

        self.v_marca, self.v_modelo = tk.StringVar(), tk.StringVar()
        self.v_anio, self.v_precio, self.v_km = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.cmb_marca = campo(formulario, "Marca *",
                               lambda p: ttk.Combobox(p, textvariable=self.v_marca), 0)
        self.ent_modelo = campo(formulario, "Modelo *",
                                lambda p: ttk.Entry(p, textvariable=self.v_modelo), 1)
        self.ent_anio = campo(formulario, "Año *", lambda p: ttk.Entry(p, textvariable=self.v_anio), 2,
                              ayuda=f"1990 – {anio_actual()}")
        self.ent_precio = campo(formulario, "Precio (Q) *",
                                lambda p: ttk.Entry(p, textvariable=self.v_precio), 3, ayuda="mayor a 0")
        self.ent_km = campo(formulario, "Kilometraje *",
                            lambda p: ttk.Entry(p, textvariable=self.v_km), 4)
        ttk.Label(formulario, text="Estado", font=FUENTE_NEGRITA).grid(row=10, column=0, sticky="w",
                                                                     pady=(8, 2))
        self.lbl_estado = ttk.Label(formulario)
        self.lbl_estado.grid(row=11, column=0, sticky="w")
        self.controles = [self.cmb_marca, self.ent_modelo, self.ent_anio, self.ent_precio, self.ent_km]
        for control in self.controles:
            control.bind("<Return>", lambda _e: self.guardar())
            control.bind("<Escape>", lambda _e: self.limpiar_formulario())

        botones = ttk.Frame(caja, style="Interior.TFrame")
        botones.pack(fill="x", pady=(18, 0))
        botones.columnconfigure((0, 1), weight=1)
        self.btn_guardar = ttk.Button(botones, style="Primario.TButton", command=self.guardar)
        self.btn_guardar.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Button(botones, text="Nuevo / Limpiar", command=self.limpiar_formulario).grid(
            row=1, column=0, sticky="ew", pady=(8, 0), padx=(0, 4))
        self.btn_eliminar = ttk.Button(botones, text="Eliminar", style="Peligro.TButton",
                                       command=self.eliminar)
        self.btn_eliminar.grid(row=1, column=1, sticky="ew", pady=(8, 0), padx=(4, 0))
        self.btn_vender = ttk.Button(botones, text="Vender este auto →", command=self.vender)
        self.btn_vender.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(caja, text="* Campos obligatorios. Seleccione un auto\nde la lista para editarlo.",
                  style="Suave.TLabel", justify="left").pack(anchor="w", pady=(14, 0))

    def _crear_listado(self):
        caja = tarjeta(self, "Inventario de autos")
        caja.grid(row=0, column=1, sticky="nsew")

        filtros = ttk.Frame(caja, style="Interior.TFrame")
        filtros.pack(fill="x")
        filtros.columnconfigure((0, 1, 2, 3), weight=1, uniform="filtro")
        self.v_buscar, self.v_f_marca, self.v_f_anio = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.v_f_min, self.v_f_max = tk.StringVar(), tk.StringVar()
        self.v_f_estado = tk.StringVar(value=TODOS)
        self.cmb_f_marca = ttk.Combobox(filtros, textvariable=self.v_f_marca, width=12)
        # (fila, columna, ancho en columnas, etiqueta, control)
        definicion = [
            (0, 0, 2, "Buscar (marca o modelo)", ttk.Entry(filtros, textvariable=self.v_buscar)),
            (0, 2, 1, "Marca", self.cmb_f_marca),
            (0, 3, 1, "Año", ttk.Entry(filtros, textvariable=self.v_f_anio, width=8)),
            (2, 0, 1, "Precio mín. (Q)", ttk.Entry(filtros, textvariable=self.v_f_min, width=10)),
            (2, 1, 1, "Precio máx. (Q)", ttk.Entry(filtros, textvariable=self.v_f_max, width=10)),
            (2, 2, 1, "Estado", ttk.Combobox(filtros, textvariable=self.v_f_estado, width=10,
                                             state="readonly", values=(TODOS,) + ESTADOS_AUTO)),
        ]
        for fila, columna, ancho, etiqueta, control in definicion:
            ttk.Label(filtros, text=etiqueta, style="Suave.TLabel").grid(
                row=fila, column=columna, columnspan=ancho, sticky="w", padx=(0, 8),
                pady=(6 if fila else 0, 0))
            control.grid(row=fila + 1, column=columna, columnspan=ancho, sticky="ew", padx=(0, 8))
        ttk.Button(filtros, text="Limpiar filtros", command=self.limpiar_filtros).grid(
            row=3, column=3, sticky="ew")
        for variable in (self.v_buscar, self.v_f_marca, self.v_f_anio, self.v_f_min, self.v_f_max,
                         self.v_f_estado):
            variable.trace_add("write", lambda *_: self.refrescar())

        self.lbl_info = ttk.Label(caja, style="Suave.TLabel")
        self.lbl_info.pack(anchor="w", pady=(12, 6))
        self.tabla = Tabla(caja, self.COLUMNAS, alto=10)
        self.tabla.marco.pack(fill="both", expand=True)
        self.tabla.tree.bind("<<TreeviewSelect>>", self._al_seleccionar)

    # ---- comportamiento ----------------------------------------------
    def refrescar(self):
        self.cmb_marca.configure(values=self.servicio.marcas())
        self.cmb_f_marca.configure(values=[""] + self.servicio.marcas())
        if self.id_edicion is not None and not any(a["id"] == self.id_edicion
                                                   for a in self.servicio.autos):
            self.limpiar_formulario()
        self._actualizar_modo()
        try:
            autos = self.servicio.filtrar_autos(self.v_buscar.get(), self.v_f_marca.get(),
                                                self.v_f_anio.get(), self.v_f_min.get(),
                                                self.v_f_max.get(), self.v_f_estado.get())
        except ErrorValidacion as error:
            self.lbl_info.configure(text="Filtros no válidos: " + " ".join(error.errores),
                                    style="Error.TLabel")
            self.tabla.llenar([], "Corrija los filtros para ver resultados.")
            return
        total = len(self.servicio.autos)
        filas = [(a["id"], (a["id"], a["marca"], a["modelo"], a["anio"], formato_moneda(a["precio"]),
                            formato_km(a["kilometraje"]), a["estado"]),
                  ("vendido",) if a["estado"] == VENDIDO else ("disponible",)) for a in autos]
        if total == 0:
            mensaje = "Aún no hay autos registrados.\nUse el formulario de la izquierda para agregar el primero."
        else:
            mensaje = "Sin resultados: ningún auto coincide con los filtros aplicados."
        self.tabla.llenar(filas, mensaje)
        if autos:
            texto = f"Mostrando {len(autos)} de {total} auto(s)."
            self.lbl_info.configure(text=texto, style="Suave.TLabel")
        else:
            self.lbl_info.configure(text="Sin resultados." if total else "Inventario vacío.",
                                    style="Error.TLabel" if total else "Suave.TLabel")

    def _al_seleccionar(self, _evento=None):
        id_auto = self.tabla.seleccionado()
        if id_auto is None:
            return
        auto = self.servicio.obtener_auto(id_auto)
        self.id_edicion = id_auto
        self.v_marca.set(auto["marca"])
        self.v_modelo.set(auto["modelo"])
        self.v_anio.set(str(auto["anio"]))
        self.v_precio.set(f"{auto['precio']:.2f}")
        self.v_km.set(str(auto["kilometraje"]))
        self._actualizar_modo()

    def _actualizar_modo(self):
        auto = None
        if self.id_edicion is not None:
            auto = next((a for a in self.servicio.autos if a["id"] == self.id_edicion), None)
        if auto is None:
            self.lbl_titulo.configure(text="Nuevo auto")
            self.btn_guardar.configure(text="Guardar auto", state="normal")
            self.btn_eliminar.configure(state="disabled")
            self.btn_vender.configure(state="disabled")
            self.lbl_estado.configure(text=f"{DISPONIBLE} (se asigna al guardar)", style="Suave.TLabel")
            estado_controles = "normal"
        else:
            vendido = auto["estado"] == VENDIDO
            self.lbl_titulo.configure(text=f"Auto #{auto['id']}")
            self.btn_guardar.configure(text="Actualizar auto", state="disabled" if vendido else "normal")
            self.btn_eliminar.configure(state="disabled" if vendido else "normal")
            self.btn_vender.configure(state="normal")
            self.lbl_estado.configure(
                text="Vendido — solo lectura" if vendido else DISPONIBLE,
                style="Suave.TLabel" if vendido else "Exito.TLabel")
            estado_controles = "disabled" if vendido else "normal"
        for control in self.controles:
            control.configure(state=estado_controles)

    def limpiar_formulario(self):
        self.id_edicion = None
        for variable in (self.v_marca, self.v_modelo, self.v_anio, self.v_precio, self.v_km):
            variable.set("")
        self.tabla.tree.selection_remove(self.tabla.tree.selection())
        self._actualizar_modo()
        self.cmb_marca.focus_set()

    def limpiar_filtros(self):
        for variable in (self.v_buscar, self.v_f_marca, self.v_f_anio, self.v_f_min, self.v_f_max):
            variable.set("")
        self.v_f_estado.set(TODOS)

    def guardar(self):
        if str(self.btn_guardar.cget("state")) == "disabled":
            return
        datos = (self.v_marca.get(), self.v_modelo.get(), self.v_anio.get(), self.v_precio.get(),
                 self.v_km.get())
        if self.id_edicion is None:
            auto = self.app.ejecutar(lambda: self.servicio.registrar_auto(*datos))
            accion = "registrado"
        else:
            auto = self.app.ejecutar(lambda: self.servicio.editar_auto(self.id_edicion, *datos))
            accion = "actualizado"
        if auto is None:
            return
        self.limpiar_formulario()
        self.app.notificar_cambio()
        visible = self.tabla.mostrar(auto["id"])
        nota = "" if visible else " (no se muestra por los filtros activos)"
        self.app.mensaje(f"Auto #{auto['id']} {descripcion_auto(auto)} {accion} "
                         f"con estado «{auto['estado']}»{nota}.")

    def eliminar(self):
        if self.id_edicion is None:
            return
        auto = self.servicio.obtener_auto(self.id_edicion)
        if not messagebox.askyesno("Eliminar auto",
                                   f"¿Eliminar el auto #{auto['id']} {descripcion_auto(auto)}?\n\n"
                                   "Esta acción no se puede deshacer.", icon="warning"):
            return
        if self.app.ejecutar(lambda: self.servicio.eliminar_auto(auto["id"]) or True):
            self.limpiar_formulario()
            self.app.notificar_cambio()
            self.app.mensaje(f"Auto #{auto['id']} {descripcion_auto(auto)} eliminado.")

    def vender(self):
        if self.id_edicion is not None:
            self.app.vender_auto(self.id_edicion)


# --------------------------------------------------------------------------
# Pestaña Clientes (RF-03, HU-03)
# --------------------------------------------------------------------------
class PestanaClientes(ttk.Frame):
    COLUMNAS = [("id", "ID", 50, "center"), ("nombre", "Nombre", 190, "w"),
                ("documento", "Documento", 130, "w"), ("telefono", "Teléfono", 110, "w"),
                ("correo", "Correo", 200, "w"), ("compras", "Compras", 80, "center")]

    def __init__(self, padre, app):
        super().__init__(padre, padding=14)
        self.app = app
        self.servicio = app.servicio
        self.id_edicion = None
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._crear_formulario()
        self._crear_listado()
        self._actualizar_modo()

    def _crear_formulario(self):
        caja = tarjeta(self)
        caja.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        self.lbl_titulo = ttk.Label(caja, style="Titulo.TLabel")
        self.lbl_titulo.pack(anchor="w")
        formulario = ttk.Frame(caja, style="Interior.TFrame")
        formulario.pack(fill="x")
        formulario.columnconfigure(0, weight=1, minsize=250)
        self.v_nombre, self.v_telefono = tk.StringVar(), tk.StringVar()
        self.v_correo, self.v_documento = tk.StringVar(), tk.StringVar()
        self.controles = [
            campo(formulario, "Nombre completo *", lambda p: ttk.Entry(p, textvariable=self.v_nombre), 0),
            campo(formulario, "Teléfono *", lambda p: ttk.Entry(p, textvariable=self.v_telefono), 1,
                  ayuda="8 a 15 dígitos"),
            campo(formulario, "Correo *", lambda p: ttk.Entry(p, textvariable=self.v_correo), 2,
                  ayuda="nombre@dominio.com"),
            campo(formulario, "Documento (DPI / pasaporte) *",
                  lambda p: ttk.Entry(p, textvariable=self.v_documento), 3),
        ]
        for control in self.controles:
            control.bind("<Return>", lambda _e: self.guardar())
            control.bind("<Escape>", lambda _e: self.limpiar_formulario())

        botones = ttk.Frame(caja, style="Interior.TFrame")
        botones.pack(fill="x", pady=(18, 0))
        botones.columnconfigure((0, 1), weight=1)
        self.btn_guardar = ttk.Button(botones, style="Primario.TButton", command=self.guardar)
        self.btn_guardar.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Button(botones, text="Nuevo / Limpiar", command=self.limpiar_formulario).grid(
            row=1, column=0, sticky="ew", pady=(8, 0), padx=(0, 4))
        self.btn_eliminar = ttk.Button(botones, text="Eliminar", style="Peligro.TButton",
                                       command=self.eliminar)
        self.btn_eliminar.grid(row=1, column=1, sticky="ew", pady=(8, 0), padx=(4, 0))
        ttk.Label(caja, text="* Campos obligatorios. El documento no\npuede repetirse entre clientes.",
                  style="Suave.TLabel", justify="left").pack(anchor="w", pady=(14, 0))

    def _crear_listado(self):
        caja = tarjeta(self, "Clientes registrados")
        caja.grid(row=0, column=1, sticky="nsew")
        barra = ttk.Frame(caja, style="Interior.TFrame")
        barra.pack(fill="x")
        ttk.Label(barra, text="Buscar (nombre, documento, correo o teléfono)",
                  style="Suave.TLabel").pack(anchor="w")
        self.v_buscar = tk.StringVar()
        ttk.Entry(barra, textvariable=self.v_buscar, width=40).pack(anchor="w")
        self.v_buscar.trace_add("write", lambda *_: self.refrescar())
        self.lbl_info = ttk.Label(caja, style="Suave.TLabel")
        self.lbl_info.pack(anchor="w", pady=(12, 6))
        self.tabla = Tabla(caja, self.COLUMNAS, alto=10)
        self.tabla.marco.pack(fill="both", expand=True)
        self.tabla.tree.bind("<<TreeviewSelect>>", self._al_seleccionar)

    def refrescar(self):
        if self.id_edicion is not None and not any(c["id"] == self.id_edicion
                                                   for c in self.servicio.clientes):
            self.limpiar_formulario()
        compras = {}
        for venta in self.servicio.ventas:
            compras[venta["id_cliente"]] = compras.get(venta["id_cliente"], 0) + 1
        clientes = self.servicio.buscar_clientes(self.v_buscar.get())  # ya vienen ordenados por id
        filas = [(c["id"], (c["id"], c["nombre"], c["documento"], c["telefono"], c["correo"],
                            compras.get(c["id"], 0)), ()) for c in clientes]
        total = len(self.servicio.clientes)
        self.tabla.llenar(filas, "Sin resultados para la búsqueda." if total else
                          "Aún no hay clientes registrados.")
        self.lbl_info.configure(text=f"Mostrando {len(clientes)} de {total} cliente(s).")

    def _al_seleccionar(self, _evento=None):
        id_cliente = self.tabla.seleccionado()
        if id_cliente is None:
            return
        cliente = self.servicio.obtener_cliente(id_cliente)
        self.id_edicion = id_cliente
        self.v_nombre.set(cliente["nombre"])
        self.v_telefono.set(cliente["telefono"])
        self.v_correo.set(cliente["correo"])
        self.v_documento.set(cliente["documento"])
        self._actualizar_modo()

    def _actualizar_modo(self):
        if self.id_edicion is None:
            self.lbl_titulo.configure(text="Nuevo cliente")
            self.btn_guardar.configure(text="Guardar cliente")
            self.btn_eliminar.configure(state="disabled")
        else:
            self.lbl_titulo.configure(text=f"Cliente #{self.id_edicion}")
            self.btn_guardar.configure(text="Actualizar cliente")
            self.btn_eliminar.configure(state="normal")

    def limpiar_formulario(self):
        self.id_edicion = None
        for variable in (self.v_nombre, self.v_telefono, self.v_correo, self.v_documento):
            variable.set("")
        self.tabla.tree.selection_remove(self.tabla.tree.selection())
        self._actualizar_modo()
        self.controles[0].focus_set()

    def guardar(self):
        datos = (self.v_nombre.get(), self.v_telefono.get(), self.v_correo.get(),
                 self.v_documento.get())
        if self.id_edicion is None:
            cliente = self.app.ejecutar(lambda: self.servicio.registrar_cliente(*datos))
            accion = "registrado"
        else:
            cliente = self.app.ejecutar(lambda: self.servicio.editar_cliente(self.id_edicion, *datos))
            accion = "actualizado"
        if cliente is None:
            return
        self.limpiar_formulario()
        self.app.notificar_cambio()
        self.tabla.mostrar(cliente["id"])
        self.app.mensaje(f"Cliente {cliente['nombre']} ({cliente['documento']}) {accion}.")

    def eliminar(self):
        if self.id_edicion is None:
            return
        cliente = self.servicio.obtener_cliente(self.id_edicion)
        if not messagebox.askyesno("Eliminar cliente",
                                   f"¿Eliminar al cliente {cliente['nombre']}?\n\n"
                                   "Esta acción no se puede deshacer.", icon="warning"):
            return
        if self.app.ejecutar(lambda: self.servicio.eliminar_cliente(cliente["id"]) or True):
            self.limpiar_formulario()
            self.app.notificar_cambio()
            self.app.mensaje(f"Cliente {cliente['nombre']} eliminado.")


# --------------------------------------------------------------------------
# Pestaña Ventas (RF-04, RF-05, HU-04)
# --------------------------------------------------------------------------
class PestanaVentas(ttk.Frame):
    COLUMNAS = [("id", "No.", 50, "center"), ("fecha", "Fecha", 130, "center"),
                ("cliente", "Cliente", 170, "w"), ("documento", "Documento", 120, "w"),
                ("auto", "Auto", 190, "w"), ("precio", "Precio", 110, "e"),
                ("pct", "Desc. %", 70, "center"), ("descuento", "Descuento", 100, "e"),
                ("total", "Total", 120, "e")]

    def __init__(self, padre, app):
        super().__init__(padre, padding=14)
        self.app = app
        self.servicio = app.servicio
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._crear_formulario()
        self._crear_historial()

    def _crear_formulario(self):
        caja = tarjeta(self, "Registrar venta")
        caja.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        cuerpo = ttk.Frame(caja, style="Interior.TFrame")
        cuerpo.pack(fill="x")
        cuerpo.columnconfigure((0, 1, 2), weight=1, uniform="venta")

        # Columnas 1 y 2: buscadores de cliente y de auto (RF-04)
        busqueda = (
            (0, "1. Cliente *", "nombre, documento, teléfono o correo",
             dict(buscar=self.servicio.buscar_clientes, plural="clientes",
                  formatear=lambda c: f"#{c['id']}  {c['nombre']} — {c['documento']}")),
            (1, "2. Auto disponible *", "marca, modelo, año o #id",
             dict(buscar=self.servicio.buscar_autos_disponibles, plural="autos disponibles",
                  formatear=lambda a: f"#{a['id']}  {descripcion_auto(a)} — {formato_moneda(a['precio'])}")),
        )
        selectores = []
        for columna, titulo, pista, opciones in busqueda:
            marco = ttk.Frame(cuerpo, style="Interior.TFrame")
            marco.grid(row=0, column=columna, sticky="nsew", padx=(0, 18))
            marco.columnconfigure(0, weight=1)
            ttk.Label(marco, text=titulo, font=FUENTE_NEGRITA).grid(row=0, column=0, sticky="w")
            ttk.Label(marco, text=f"Buscar por {pista}", style="Suave.TLabel").grid(
                row=1, column=0, sticky="w", pady=(0, 4))
            selector = SelectorBuscable(marco, al_cambiar=self._actualizar_detalle, **opciones)
            selector.grid(row=2, column=0, sticky="nsew")
            selectores.append(selector)
        self.sel_cliente, self.sel_auto = selectores

        # Columna 3: descuento y detalle del cálculo
        derecha = ttk.Frame(cuerpo, style="Tarjeta.TFrame", padding=16)
        derecha.grid(row=0, column=2, sticky="nsew")
        derecha.columnconfigure(1, weight=1)
        ttk.Label(derecha, text="3. Detalle", style="Titulo.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self.v_descuento = tk.StringVar(value="0")
        ttk.Label(derecha, text="Descuento (%)", style="Suave.TLabel").grid(row=1, column=0, sticky="w")
        caja_desc = ttk.Frame(derecha, style="Interior.TFrame")
        caja_desc.grid(row=1, column=1, sticky="e")
        self.spn_descuento = ttk.Spinbox(caja_desc, textvariable=self.v_descuento, from_=0,
                                         to=DESCUENTO_MAXIMO, increment=1, width=7, justify="right")
        self.spn_descuento.pack(side="left")
        ttk.Label(caja_desc, text=f"  máx. {DESCUENTO_MAXIMO:g} %", style="Suave.TLabel").pack(side="left")
        self.lbl_precio, self.lbl_monto_desc, self.lbl_total = (ttk.Label(derecha) for _ in range(3))
        for fila, (texto, etiqueta) in enumerate((("Precio del auto", self.lbl_precio),
                                                  ("Descuento", self.lbl_monto_desc)), start=2):
            ttk.Label(derecha, text=texto, style="Suave.TLabel").grid(row=fila, column=0, sticky="w",
                                                                     pady=(8, 0))
            etiqueta.grid(row=fila, column=1, sticky="e", pady=(8, 0))
        ttk.Separator(derecha).grid(row=4, column=0, columnspan=2, sticky="ew", pady=8)
        ttk.Label(derecha, text="Total a pagar", font=FUENTE_NEGRITA).grid(row=5, column=0, sticky="w")
        self.lbl_total.configure(style="Total.TLabel")
        self.lbl_total.grid(row=5, column=1, sticky="e")
        self.lbl_error = ttk.Label(derecha, style="Error.TLabel", wraplength=px(300))
        self.lbl_error.grid(row=6, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.btn_vender = ttk.Button(derecha, text="Registrar venta", style="Primario.TButton",
                                     command=self.registrar)
        self.btn_vender.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.v_descuento.trace_add("write", lambda *_: self._actualizar_detalle())
        self.spn_descuento.bind("<Return>", lambda _e: self.registrar())

    def _crear_historial(self):
        caja = tarjeta(self, "Historial de ventas")
        caja.grid(row=1, column=0, sticky="nsew")
        self.lbl_info = ttk.Label(caja, style="Suave.TLabel")
        self.lbl_info.pack(anchor="w", pady=(0, 6))
        self.tabla = Tabla(caja, self.COLUMNAS, alto=6)
        self.tabla.marco.pack(fill="both", expand=True)

    # ---- comportamiento ----------------------------------------------
    def refrescar(self):
        self.sel_cliente.refrescar()
        self.sel_auto.refrescar()
        self._actualizar_detalle()

        historial = self.servicio.historial_ventas()
        filas = [(h["id"], (h["id"], h["fecha"], h["cliente"], h["documento"], h["auto"],
                            formato_moneda(h["precio"]), f"{h['porcentaje_descuento']:g} %",
                            formato_moneda(h["descuento"]), formato_moneda(h["total"])), ())
                 for h in historial]
        self.tabla.llenar(filas, "Aún no hay ventas registradas.")
        total = sum(h["total"] for h in historial)
        self.lbl_info.configure(text=f"{len(historial)} venta(s) — total vendido {formato_moneda(total)}")

    def preseleccionar_auto(self, id_auto):
        self.sel_auto.v_texto.set("")
        self.sel_auto.seleccionar(id_auto)
        self.sel_cliente.entrada.focus_set()

    def _actualizar_detalle(self):
        if not hasattr(self, "lbl_total"):  # aún se está construyendo el formulario
            return
        id_auto = self.sel_auto.id_seleccionado
        self.lbl_error.configure(text="")
        if id_auto is None:
            for etiqueta in (self.lbl_precio, self.lbl_monto_desc, self.lbl_total):
                etiqueta.configure(text="—")
            return
        try:
            calculo = self.servicio.calcular_venta(id_auto, self.v_descuento.get())
        except ErrorValidacion as error:
            self.lbl_precio.configure(text=formato_moneda(self.servicio.obtener_auto(id_auto)["precio"]))
            self.lbl_monto_desc.configure(text="—")
            self.lbl_total.configure(text="—")
            self.lbl_error.configure(text=error.errores[0])
            return
        self.lbl_precio.configure(text=formato_moneda(calculo["precio"]))
        self.lbl_monto_desc.configure(
            text=f"− {formato_moneda(calculo['descuento'])}  ({calculo['porcentaje_descuento']:g} %)")
        self.lbl_total.configure(text=formato_moneda(calculo["total"]))

    def registrar(self):
        id_cliente = self.sel_cliente.id_seleccionado
        id_auto = self.sel_auto.id_seleccionado
        errores = []
        if id_cliente is None:
            errores.append("Seleccione un cliente.")
        if id_auto is None:
            errores.append("Seleccione un auto disponible.")
        if errores:
            mostrar_errores(ErrorValidacion(errores))
            return
        calculo = self.app.ejecutar(lambda: self.servicio.calcular_venta(id_auto, self.v_descuento.get()))
        if calculo is None:
            return
        cliente = self.servicio.obtener_cliente(id_cliente)
        auto = self.servicio.obtener_auto(id_auto)
        confirmar = messagebox.askyesno(
            "Confirmar venta",
            f"Cliente: {cliente['nombre']} ({cliente['documento']})\n"
            f"Auto: #{auto['id']} {descripcion_auto(auto)}\n\n"
            f"Precio:      {formato_moneda(calculo['precio'])}\n"
            f"Descuento: − {formato_moneda(calculo['descuento'])} ({calculo['porcentaje_descuento']:g} %)\n"
            f"Total:         {formato_moneda(calculo['total'])}\n\n"
            "Al confirmar, el auto pasará a estado «Vendido». ¿Continuar?")
        if not confirmar:
            return
        venta = self.app.ejecutar(lambda: self.servicio.registrar_venta(
            id_cliente, id_auto, self.v_descuento.get()))
        if venta is None:
            return
        self.sel_auto.limpiar()
        self.v_descuento.set("0")
        self.app.notificar_cambio()
        self.app.mensaje(f"Venta No. {venta['id']} registrada: {descripcion_auto(auto)} a "
                         f"{cliente['nombre']} por {formato_moneda(venta['total'])}. "
                         "El auto ahora está «Vendido».")


# --------------------------------------------------------------------------
# Pestaña Resumen (RF-06, HU-05)
# --------------------------------------------------------------------------
class PestanaResumen(ttk.Frame):
    INDICADORES = [
        ("autos_disponibles", "Autos disponibles", EXITO, str),
        ("autos_vendidos", "Autos vendidos", ADVERTENCIA, str),
        ("total_vendido", "Total vendido", PRIMARIO, formato_moneda),
        ("cantidad_ventas", "Ventas realizadas", TEXTO, str),
        ("clientes", "Clientes registrados", TEXTO, str),
        ("valor_inventario", "Valor del inventario disponible", TEXTO, formato_moneda),
    ]

    def __init__(self, padre, app):
        super().__init__(padre, padding=14)
        self.app = app
        self.servicio = app.servicio
        self.valores = {}
        self.columnconfigure((0, 1, 2), weight=1, uniform="kpi")
        self.rowconfigure(2, weight=1)
        for indice, (clave, titulo, color, _formato) in enumerate(self.INDICADORES):
            caja = tarjeta(self, padding=(18, 14))
            caja.grid(row=indice // 3, column=indice % 3, sticky="nsew",
                      padx=(0 if indice % 3 == 0 else 7, 0 if indice % 3 == 2 else 7), pady=(0, 14))
            ttk.Label(caja, text=titulo, style="KpiTitulo.TLabel").pack(anchor="w")
            etiqueta = ttk.Label(caja, style="KpiValor.TLabel", foreground=color)
            etiqueta.pack(anchor="w", pady=(4, 0))
            self.valores[clave] = etiqueta

        ultimas = tarjeta(self, "Últimas ventas")
        ultimas.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=(0, 7))
        self.tabla_ventas = Tabla(ultimas, [("fecha", "Fecha", 130, "center"),
                                            ("cliente", "Cliente", 160, "w"),
                                            ("auto", "Auto", 180, "w"),
                                            ("total", "Total", 120, "e")], alto=6)
        self.tabla_ventas.marco.pack(fill="both", expand=True)

        marcas = tarjeta(self, "Inventario por marca")
        marcas.grid(row=2, column=2, sticky="nsew", padx=(7, 0))
        self.tabla_marcas = Tabla(marcas, [("marca", "Marca", 120, "w"),
                                           ("disp", "Disp.", 60, "center"),
                                           ("vend", "Vend.", 60, "center")], alto=6)
        self.tabla_marcas.marco.pack(fill="both", expand=True)

    def refrescar(self):
        resumen = self.servicio.resumen()
        for clave, _titulo, _color, formato in self.INDICADORES:
            self.valores[clave].configure(text=formato(resumen[clave]))

        ultimas = self.servicio.historial_ventas()[:5]
        self.tabla_ventas.llenar([(h["id"], (h["fecha"], h["cliente"], h["auto"],
                                             formato_moneda(h["total"])), ()) for h in ultimas],
                                 "Aún no hay ventas registradas.")
        conteo = {}
        for auto in self.servicio.autos:
            fila = conteo.setdefault(auto["marca"], [0, 0])
            fila[0 if auto["estado"] == DISPONIBLE else 1] += 1
        filas = [(indice, (marca, d, s), ()) for indice, (marca, (d, s))
                 in enumerate(sorted(conteo.items(), key=lambda par: par[0].casefold()))]
        self.tabla_marcas.llenar(filas, "Sin autos en inventario.")


# --------------------------------------------------------------------------
# Ventana principal
# --------------------------------------------------------------------------
class AplicacionAutoVentas(tk.Tk):
    def __init__(self, servicio, aviso_carga=None):
        super().__init__()
        self.servicio = servicio
        self.title("AutoVentas — Sistema de venta de autos")
        self._limpiar_barra = None
        aplicar_estilos(self)

        encabezado = tk.Frame(self, background=ENCABEZADO, padx=22, pady=14)
        encabezado.pack(fill="x")
        tk.Label(encabezado, text="AutoVentas", font=FUENTE_TITULO, fg="white",
                 bg=ENCABEZADO).pack(side="left")
        tk.Label(encabezado, text="  Sistema de gestión y venta de automóviles", font=FUENTE,
                 fg="#94A3B8", bg=ENCABEZADO).pack(side="left", pady=(6, 0))

        self.barra_estado = ttk.Label(self, style="Barra.TLabel", text="Listo.")
        self.barra_estado.pack(side="bottom", fill="x")

        self.cuaderno = ttk.Notebook(self)
        self.cuaderno.pack(fill="both", expand=True)
        self.inventario = PestanaInventario(self.cuaderno, self)
        self.clientes = PestanaClientes(self.cuaderno, self)
        self.ventas = PestanaVentas(self.cuaderno, self)
        self.resumen = PestanaResumen(self.cuaderno, self)
        for pestana, titulo in ((self.inventario, "Inventario"), (self.clientes, "Clientes"),
                                (self.ventas, "Ventas"), (self.resumen, "Resumen")):
            self.cuaderno.add(pestana, text=titulo)
        self.pestanas = (self.inventario, self.clientes, self.ventas, self.resumen)

        self.notificar_cambio()
        self._ajustar_tamano()
        if aviso_carga:
            self.after(300, lambda: messagebox.showwarning("Datos", aviso_carga))

    def _ajustar_tamano(self):
        """Tamaño según el contenido y la pantalla, centrado (funciona con cualquier escalado)."""
        self.update_idletasks()
        pantalla_x, pantalla_y = self.winfo_screenwidth(), self.winfo_screenheight()
        req_x, req_y = self.winfo_reqwidth(), self.winfo_reqheight()
        ancho = min(max(req_x, px(1220)), int(pantalla_x * 0.95))
        alto = min(max(req_y, px(760)), int(pantalla_y * 0.88))
        self.minsize(min(req_x, ancho), min(req_y, alto))
        self.geometry(f"{ancho}x{alto}+{(pantalla_x - ancho) // 2}+{max(0, (pantalla_y - alto) // 2 - 30)}")
        if req_x > ancho or req_y > alto:
            self.state("zoomed")  # pantalla pequeña: usar toda la pantalla

    def notificar_cambio(self):
        """Refresca todas las pestañas para que todo refleje el último cambio (HU-05)."""
        for pestana in self.pestanas:
            pestana.refrescar()

    def mensaje(self, texto, error=False):
        self.barra_estado.configure(text=texto, style="BarraError.TLabel" if error else "BarraExito.TLabel")
        if self._limpiar_barra:
            self.after_cancel(self._limpiar_barra)
        self._limpiar_barra = self.after(
            10000, lambda: self.barra_estado.configure(text="Listo.", style="Barra.TLabel"))

    def ejecutar(self, accion):
        """Ejecuta una operación del servicio y muestra sus errores. Devuelve None si falló."""
        try:
            return accion()
        except ErrorValidacion as error:
            titulo = "Operación bloqueada" if isinstance(error, ErrorNegocio) else "Datos no válidos"
            mostrar_errores(error, titulo)
            self.mensaje(error.errores[0], error=True)
        except OSError as error:
            messagebox.showerror("Error al guardar",
                                 f"No se pudieron guardar los datos en disco:\n{error}\n\n"
                                 "La operación se canceló; no se perdió información.")
            self.mensaje("No se pudo guardar en disco; la operación se canceló.", error=True)
        return None

    def vender_auto(self, id_auto):
        """Desde Inventario: lleva el auto a la pestaña Ventas, o bloquea si ya fue vendido (CP-03)."""
        auto = self.servicio.obtener_auto(id_auto)
        if auto["estado"] != DISPONIBLE:
            mensaje = (f"El auto #{auto['id']} {descripcion_auto(auto)} no está disponible "
                       f"(estado: {auto['estado']}). Solo se pueden vender autos «Disponible».")
            messagebox.showerror("Operación bloqueada", mensaje)
            self.mensaje(mensaje, error=True)
            return
        self.cuaderno.select(self.ventas)
        self.ventas.preseleccionar_auto(id_auto)

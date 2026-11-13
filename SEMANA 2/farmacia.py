"""Control de inventario de una farmacia con interfaz gráfica (tkinter).



Campos del producto: nombre, existencia, descripción, fecha de ingreso,

precio (Q) y fecha de caducidad.

Incluye búsqueda por nombre, rangos de fechas de ingreso y caducidad,
ordenamiento y exportación a Excel (.xlsx).

Los datos se guardan automáticamente en "inventario_farmacia.json" (junto a

este programa) cada vez que se guarda, modifica o elimina un producto.



Estructura:

  - Funciones de lógica (validar, buscar, cargar y guardar datos), sin

    dependencia de tkinter, para que sean fáciles de probar.

  - Clase AppInventario con la interfaz gráfica.

"""



import json

import os

import re

import tempfile

import tkinter as tk

from datetime import date, datetime

from tkinter import ttk, messagebox, filedialog



# ---------------------------------------------------------------------------

# Constantes

# ---------------------------------------------------------------------------

RUTA_DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)),

                          "inventario_farmacia.json")

FORMATO_FECHA = "%d/%m/%Y"

MONEDA = "Q"

DIAS_ALERTA = 30             # productos que vencen dentro de este plazo se resaltan

MAX_NOMBRE = 80

MAX_DESCRIPCION = 200

MAX_EXISTENCIA = 1_000_000

MAX_PRECIO = 1_000_000

CLAVES = {"id", "nombre", "existencia", "descripcion", "ingreso", "precio", "caducidad"}



PALETAS = {

    "Claro": dict(

        bg="#eef3f8", card="#ffffff", fg="#1f2933", muted="#6b7785",

        campo="#ffffff", borde="#d5dee8", boton="#e8edf3", boton_hover="#d9e1ea",

        acento="#1f8a70", acento_hover="#176f5a",

        peligro="#c62828", peligro_hover="#a81f1f",

        encabezado="#e3eaf2", sel="#cfe6dd",

        vencido="#c62828", por_vencer="#b36b00",

    ),

    "Oscuro": dict(

        bg="#12171d", card="#1c232c", fg="#e6edf3", muted="#9aa7b4",

        campo="#27303b", borde="#3a4553", boton="#2a3340", boton_hover="#364255",

        acento="#2aa889", acento_hover="#35c0a0",

        peligro="#d33a3a", peligro_hover="#e04848",

        encabezado="#27303b", sel="#25483f",

        vencido="#ff7b72", por_vencer="#e3b341",

    ),

}





# ---------------------------------------------------------------------------

# Validaciones y lógica

# ---------------------------------------------------------------------------

def parsear_fecha(texto, campo):

    """Convierte DD/MM/AAAA en date. Lanza ValueError con un mensaje claro."""

    texto = texto.strip()

    if not texto:

        raise ValueError(f"{campo} es obligatoria.")

    try:

        return datetime.strptime(texto, FORMATO_FECHA).date()

    except ValueError:

        raise ValueError(

            f"{campo} debe ser una fecha real con formato DD/MM/AAAA "

            "(ejemplo: 25/12/2026).")





def validar_existencia(texto):

    """Entero mayor o igual a cero."""

    texto = texto.strip()

    if not texto:

        raise ValueError("La existencia es obligatoria.")

    if not (texto.isascii() and texto.isdigit()):

        raise ValueError("La existencia debe ser un número entero mayor o igual a 0.")

    valor = int(texto)

    if valor > MAX_EXISTENCIA:

        raise ValueError(f"La existencia no puede superar {MAX_EXISTENCIA:,} unidades.")

    return valor





def validar_precio(texto):

    """Número mayor que cero con hasta 2 decimales (acepta coma o punto)."""

    texto = texto.strip().replace(",", ".")

    if not texto:

        raise ValueError("El precio es obligatorio.")

    if not re.fullmatch(r"\d+(\.\d{1,2})?", texto):

        raise ValueError("El precio debe ser un número con hasta 2 decimales "

                         "(ejemplo: 25.50).")

    valor = float(texto)

    if valor <= 0:

        raise ValueError("El precio debe ser mayor que cero.")

    if valor > MAX_PRECIO:

        raise ValueError(f"El precio no puede superar {MONEDA} {MAX_PRECIO:,}.")

    return round(valor, 2)





def validar_producto(nombre, existencia, descripcion, ingreso, precio, caducidad,

                     hoy=None):

    """Valida todos los campos del formulario y devuelve un dict (sin id)."""

    hoy = hoy or date.today()



    nombre = nombre.strip()

    if not nombre:

        raise ValueError("El nombre del producto es obligatorio.")

    if len(nombre) > MAX_NOMBRE:

        raise ValueError(f"El nombre no puede superar los {MAX_NOMBRE} caracteres.")



    cantidad = validar_existencia(existencia)



    descripcion = descripcion.strip()

    if not descripcion:

        raise ValueError("La descripción es obligatoria.")

    if len(descripcion) > MAX_DESCRIPCION:

        raise ValueError(

            f"La descripción no puede superar los {MAX_DESCRIPCION} caracteres.")



    f_ingreso = parsear_fecha(ingreso, "La fecha de ingreso")

    if f_ingreso > hoy:

        raise ValueError("La fecha de ingreso no puede ser posterior a hoy.")



    valor = validar_precio(precio)



    f_caducidad = parsear_fecha(caducidad, "La fecha de caducidad")

    if f_caducidad < f_ingreso:

        raise ValueError(

            "La fecha de caducidad no puede ser anterior a la fecha de ingreso.")



    return {

        "nombre": nombre,

        "existencia": cantidad,

        "descripcion": descripcion,

        "ingreso": f_ingreso.isoformat(),

        "precio": valor,

        "caducidad": f_caducidad.isoformat(),

    }





def siguiente_id(productos):

    return max((p["id"] for p in productos), default=0) + 1





def buscar_producto(productos, id_producto):

    for p in productos:

        if p["id"] == id_producto:

            return p

    return None





def hay_duplicado(productos, datos, excluir_id=None):

    """Mismo nombre y misma fecha de caducidad = mismo lote ya registrado."""

    nombre = datos["nombre"].casefold()

    for p in productos:

        if p["id"] == excluir_id:

            continue

        if p["nombre"].casefold() == nombre and p["caducidad"] == datos["caducidad"]:

            return True

    return False





def agregar_producto(productos, datos):

    if hay_duplicado(productos, datos):

        raise ValueError("Ya existe un producto con el mismo nombre y la misma "

                         "fecha de caducidad. Use «Modificar» para cambiar su "

                         "existencia.")

    producto = dict(datos, id=siguiente_id(productos))

    productos.append(producto)

    return producto





def modificar_producto(productos, id_producto, datos):

    producto = buscar_producto(productos, id_producto)

    if producto is None:

        raise ValueError("El producto seleccionado ya no existe.")

    if hay_duplicado(productos, datos, excluir_id=id_producto):

        raise ValueError("Ya existe otro producto con el mismo nombre y la misma "

                         "fecha de caducidad.")

    producto.update(datos)

    return producto





def eliminar_producto(productos, id_producto):

    producto = buscar_producto(productos, id_producto)

    if producto is None:

        raise ValueError("El producto seleccionado ya no existe.")

    productos.remove(producto)





def estado_caducidad(caducidad_iso, hoy=None):

    """'vencido', 'por_vencer' (dentro de DIAS_ALERTA días) o 'ok'."""

    hoy = hoy or date.today()

    dias = (date.fromisoformat(caducidad_iso) - hoy).days

    if dias < 0:

        return "vencido"

    if dias <= DIAS_ALERTA:

        return "por_vencer"

    return "ok"





def ordenar(productos, criterio="nombre", descendente=False):
    """Ordena por nombre, fecha de ingreso o fecha de caducidad."""
    claves = {
        "nombre": lambda p: p["nombre"].casefold(),
        "ingreso": lambda p: p["ingreso"],
        "caducidad": lambda p: p["caducidad"],
    }
    return sorted(productos, key=claves[criterio], reverse=descendente)





def formato_fecha(iso):

    return date.fromisoformat(iso).strftime(FORMATO_FECHA)





def formato_precio(valor):

    return f"{MONEDA} {valor:,.2f}"





# ---------------------------------------------------------------------------

# Persistencia (archivo JSON)

# ---------------------------------------------------------------------------

def cargar_datos(ruta):

    """Devuelve (productos, tema, aviso). Si no hay archivo, empieza vacío.



    Si el archivo está dañado se renombra a '.corrupto' (para no perderlo ni

    sobrescribirlo) y se empieza con un inventario vacío, con un aviso.

    """

    if not os.path.exists(ruta):

        return [], "Claro", None

    try:

        with open(ruta, encoding="utf-8") as archivo:

            datos = json.load(archivo)

        productos = datos["productos"]

        for p in productos:

            if not CLAVES.issubset(p):

                raise KeyError("faltan campos")

            date.fromisoformat(p["ingreso"])

            date.fromisoformat(p["caducidad"])

            int(p["id"]), int(p["existencia"]), float(p["precio"])

        tema = datos.get("tema", "Claro")

        return productos, tema if tema in PALETAS else "Claro", None

    except (OSError, ValueError, KeyError, TypeError, AttributeError):

        destino = ruta + ".corrupto"

        try:

            os.replace(ruta, destino)

            aviso = (f"El archivo de datos estaba dañado y se guardó como:\n{destino}\n"

                     "Se inició un inventario vacío.")

        except OSError:

            aviso = ("El archivo de datos está dañado y no pudo leerse. "

                     "Se inició un inventario vacío.")

        return [], "Claro", aviso





def guardar_datos(ruta, productos, tema):

    """Escribe el archivo de forma segura (archivo temporal + reemplazo)."""

    carpeta = os.path.dirname(ruta) or "."

    descriptor, temporal = tempfile.mkstemp(dir=carpeta, suffix=".tmp")

    try:

        with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:

            json.dump({"tema": tema, "productos": productos}, archivo,

                      ensure_ascii=False, indent=2)

            archivo.flush()

            os.fsync(archivo.fileno())

        os.replace(temporal, ruta)

    except BaseException:

        try:

            os.unlink(temporal)

        except OSError:

            pass

        raise





# ---------------------------------------------------------------------------

# Interfaz gráfica

# ---------------------------------------------------------------------------

class AppInventario(tk.Tk):

    def __init__(self, ruta=RUTA_DATOS):

        super().__init__()

        self.title("Inventario de Farmacia")

        self.geometry("1220x850")
        self.minsize(1000, 740)

        self.ruta = ruta
        self.productos, self.tema, aviso = cargar_datos(ruta)
        self.id_editando = None
        self.criterio_orden = "nombre"
        self.orden_descendente = False
        self.filtros_aplicados = {
            "nombre": "",
            "ingreso_desde": None,
            "ingreso_hasta": None,
            "caducidad_desde": None,
            "caducidad_hasta": None,
        }



        self._crear_widgets()

        self._aplicar_tema()

        self.limpiar()

        self._refrescar()

        if aviso:

            messagebox.showwarning("Datos dañados", aviso)



    # -- construcción ------------------------------------------------------

    def _crear_widgets(self):
        raiz = ttk.Frame(self, padding=(18, 12))
        raiz.pack(fill="both", expand=True)

        # Encabezado
        encabezado = ttk.Frame(raiz)
        encabezado.pack(fill="x")
        ttk.Label(encabezado, text="💊 Inventario de Farmacia",
                  style="Titulo.TLabel").pack(side="left")
        self.btn_tema = ttk.Button(encabezado, command=self.alternar_tema)
        self.btn_tema.pack(side="right")

        # Formulario de productos
        form = ttk.Frame(raiz, style="Card.TFrame", padding=14)
        form.pack(fill="x", pady=(10, 8))
        for columna, peso in enumerate((3, 2, 2)):
            form.columnconfigure(columna, weight=peso, uniform="formulario")

        self.var_nombre = tk.StringVar()
        self.var_existencia = tk.StringVar()
        self.var_descripcion = tk.StringVar()
        self.var_ingreso = tk.StringVar()
        self.var_precio = tk.StringVar()
        self.var_caducidad = tk.StringVar()

        self.ent_nombre = self._campo(form, 0, 0, "Nombre del producto",
                                      self.var_nombre)
        self._campo(form, 0, 1, "Existencia (unidades)", self.var_existencia)
        self._campo(form, 0, 2, f"Precio ({MONEDA})", self.var_precio)
        self._campo(form, 2, 0, "Descripción", self.var_descripcion)
        self._campo(form, 2, 1, "Fecha de ingreso (DD/MM/AAAA)", self.var_ingreso)
        self._campo(form, 2, 2, "Fecha de caducidad (DD/MM/AAAA)", self.var_caducidad)

        botones_form = ttk.Frame(form, style="Inner.TFrame")
        botones_form.grid(row=4, column=0, columnspan=3, sticky="w", pady=(12, 0))
        ttk.Button(botones_form, text="Guardar", style="Accent.TButton",
                   command=self.guardar).pack(side="left")
        ttk.Button(botones_form, text="Modificar",
                   command=self.modificar).pack(side="left", padx=(8, 0))
        ttk.Button(botones_form, text="Eliminar", style="Danger.TButton",
                   command=self.eliminar).pack(side="left", padx=(8, 0))
        ttk.Button(botones_form, text="Limpiar campos",
                   command=self.limpiar).pack(side="left", padx=(8, 0))
        self.lbl_modo = ttk.Label(botones_form, style="CardMuted.TLabel")
        self.lbl_modo.pack(side="left", padx=(14, 0))

        # Listado, buscador y filtros
        lista = ttk.Frame(raiz, style="Card.TFrame", padding=12)
        lista.pack(fill="both", expand=True)

        filtros = ttk.Frame(lista, style="Inner.TFrame")
        filtros.pack(fill="x", pady=(0, 8))
        for columna, peso in enumerate((2, 1, 1, 1, 1)):
            filtros.columnconfigure(columna, weight=peso, uniform="filtros")

        self.var_busqueda = tk.StringVar()
        self.var_ingreso_desde = tk.StringVar()
        self.var_ingreso_hasta = tk.StringVar()
        self.var_caducidad_desde = tk.StringVar()
        self.var_caducidad_hasta = tk.StringVar()

        campos_filtro = (
            (0, "Buscar por nombre", self.var_busqueda),
            (1, "Ingreso desde", self.var_ingreso_desde),
            (2, "Ingreso hasta", self.var_ingreso_hasta),
            (3, "Caducidad desde", self.var_caducidad_desde),
            (4, "Caducidad hasta", self.var_caducidad_hasta),
        )
        for columna, etiqueta, variable in campos_filtro:
            celda = ttk.Frame(filtros, style="Inner.TFrame")
            celda.grid(row=0, column=columna, sticky="ew",
                       padx=(0 if columna == 0 else 8, 0))
            ttk.Label(celda, text=etiqueta, style="CardMuted.TLabel").pack(
                anchor="w", pady=(0, 3))
            entrada = ttk.Entry(celda, textvariable=variable)
            entrada.pack(fill="x")
            if columna == 0:
                self.ent_busqueda = entrada
                entrada.bind("<Return>", lambda evento: self.aplicar_filtros())

        barra_acciones = ttk.Frame(lista, style="Inner.TFrame")
        barra_acciones.pack(fill="x", pady=(0, 10))

        grupo_busqueda = ttk.Frame(barra_acciones, style="Inner.TFrame")
        grupo_busqueda.pack(side="left")
        ttk.Button(grupo_busqueda, text="Buscar", style="Accent.TButton",
                   command=self.aplicar_filtros).pack(side="left")
        ttk.Button(grupo_busqueda, text="Limpiar filtros",
                   command=self.limpiar_filtros).pack(side="left", padx=(6, 0))

        grupo_orden = ttk.Frame(barra_acciones, style="Inner.TFrame")
        grupo_orden.pack(side="left", padx=(18, 0))
        ttk.Label(grupo_orden, text="Ordenar:", style="CardMuted.TLabel").pack(
            side="left", padx=(0, 5))
        self.btn_orden_nombre = ttk.Button(
            grupo_orden, command=lambda: self._cambiar_orden("nombre"))
        self.btn_orden_nombre.pack(side="left", padx=(0, 5))
        self.btn_orden_ingreso = ttk.Button(
            grupo_orden, command=lambda: self._cambiar_orden("ingreso"))
        self.btn_orden_ingreso.pack(side="left", padx=(0, 5))
        self.btn_orden_caducidad = ttk.Button(
            grupo_orden, command=lambda: self._cambiar_orden("caducidad"))
        self.btn_orden_caducidad.pack(side="left")
        self._actualizar_botones_orden()

        grupo_excel = ttk.Frame(barra_acciones, style="Inner.TFrame")
        grupo_excel.pack(side="right")
        ttk.Button(grupo_excel, text="Excel: listado general",
                   command=self.exportar_general).pack(side="left", padx=(5, 0))
        ttk.Button(grupo_excel, text="Excel: productos vencidos",
                   style="Danger.TButton",
                   command=self.exportar_vencidos).pack(side="left", padx=(5, 0))

        # Tabla de productos
        zona = ttk.Frame(lista, style="Inner.TFrame")
        zona.pack(fill="both", expand=True)
        columnas = ("nombre", "descripcion", "existencia", "precio",
                    "ingreso", "caducidad")
        self.tree = ttk.Treeview(zona, columns=columnas, show="headings",
                                 selectmode="browse", height=12)
        encabezados = (
            ("nombre", "Nombre del producto", 190, "w"),
            ("descripcion", "Descripción", 240, "w"),
            ("existencia", "Existencia", 85, "center"),
            ("precio", "Precio", 90, "e"),
            ("ingreso", "Fecha de ingreso", 115, "center"),
            ("caducidad", "Fecha de caducidad", 125, "center"),
        )
        for col, titulo, ancho, ancla in encabezados:
            self.tree.heading(col, text=titulo)
            self.tree.column(col, width=ancho, minwidth=70, anchor=ancla,
                             stretch=(col in ("nombre", "descripcion")))

        barra_vertical = ttk.Scrollbar(zona, orient="vertical", command=self.tree.yview)
        barra_horizontal = ttk.Scrollbar(lista, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=barra_vertical.set,
                            xscrollcommand=barra_horizontal.set)
        self.tree.pack(side="left", fill="both", expand=True)
        barra_vertical.pack(side="right", fill="y")
        barra_horizontal.pack(fill="x", pady=(2, 0))
        self.tree.bind("<<TreeviewSelect>>", lambda evento: self._al_seleccionar())
        self.tree.bind("<Delete>", lambda evento: self.eliminar())

        self.lbl_vacio = ttk.Label(zona, style="CardMuted.TLabel", justify="center")
        self.lbl_resumen = ttk.Label(lista, style="Card.TLabel")
        self.lbl_resumen.pack(side="bottom", anchor="w", pady=(8, 0))

    def _campo(self, padre, fila, columna, etiqueta, variable):

        ttk.Label(padre, text=etiqueta, style="CardMuted.TLabel").grid(

            row=fila, column=columna, sticky="w",

            padx=(0 if columna == 0 else 10, 0))

        entrada = ttk.Entry(padre, textvariable=variable)

        entrada.grid(row=fila + 1, column=columna, sticky="ew", pady=(2, 8),

                     padx=(0 if columna == 0 else 10, 0))

        return entrada



    # -- tema ---------------------------------------------------------------

    def alternar_tema(self):

        self.tema = "Oscuro" if self.tema == "Claro" else "Claro"

        self._aplicar_tema()

        self._persistir()



    def _aplicar_tema(self):

        p = PALETAS[self.tema]

        self.btn_tema.configure(

            text="☀ Modo claro" if self.tema == "Oscuro" else "🌙 Modo oscuro")



        st = ttk.Style(self)

        st.theme_use("clam")

        self.configure(bg=p["bg"])



        st.configure("TFrame", background=p["bg"])

        st.configure("Card.TFrame", background=p["card"], bordercolor=p["borde"],

                     relief="solid", borderwidth=1)

        st.configure("Inner.TFrame", background=p["card"], borderwidth=0)

        st.configure("TLabel", background=p["bg"], foreground=p["fg"])

        st.configure("Titulo.TLabel", background=p["bg"], foreground=p["fg"],

                     font=("TkDefaultFont", 18, "bold"))

        st.configure("Card.TLabel", background=p["card"], foreground=p["fg"])

        st.configure("CardMuted.TLabel", background=p["card"], foreground=p["muted"])



        st.configure("TEntry", fieldbackground=p["campo"], foreground=p["fg"],

                     insertcolor=p["fg"], bordercolor=p["borde"],

                     lightcolor=p["borde"], darkcolor=p["borde"], padding=6)

        st.map("TEntry", bordercolor=[("focus", p["acento"])],

               lightcolor=[("focus", p["acento"])],

               darkcolor=[("focus", p["acento"])])



        st.configure("TButton", background=p["boton"], foreground=p["fg"],

                     bordercolor=p["borde"], lightcolor=p["boton"],

                     darkcolor=p["boton"], padding=(16, 7),

                     focuscolor=p["boton"], focusthickness=0)

        st.map("TButton", background=[("active", p["boton_hover"]),

                                      ("pressed", p["boton_hover"])])

        for nombre, color, hover in (

            ("Accent", p["acento"], p["acento_hover"]),

            ("Danger", p["peligro"], p["peligro_hover"]),

        ):

            st.configure(f"{nombre}.TButton", background=color, foreground="#ffffff",

                         bordercolor=color, lightcolor=color, darkcolor=color,

                         padding=(18, 7), focuscolor=color, focusthickness=0)

            st.map(f"{nombre}.TButton",

                   background=[("active", hover), ("pressed", hover)],

                   bordercolor=[("active", hover)],

                   lightcolor=[("active", hover)],

                   darkcolor=[("active", hover)])



        st.configure("Treeview", background=p["card"], fieldbackground=p["card"],

                     foreground=p["fg"], bordercolor=p["borde"],

                     lightcolor=p["card"], darkcolor=p["card"], rowheight=28)

        st.map("Treeview", background=[("selected", p["sel"])],

               foreground=[("selected", p["fg"])])

        st.configure("Treeview.Heading", background=p["encabezado"],

                     foreground=p["fg"], bordercolor=p["borde"],

                     lightcolor=p["encabezado"], darkcolor=p["encabezado"],

                     relief="flat", padding=6)

        st.map("Treeview.Heading", background=[("active", p["boton_hover"])])

        st.configure("Vertical.TScrollbar", background=p["boton"],

                     troughcolor=p["card"], bordercolor=p["card"],

                     arrowcolor=p["fg"], lightcolor=p["boton"], darkcolor=p["boton"])

        self.tree.tag_configure("vencido", foreground=p["vencido"])

        self.tree.tag_configure("por_vencer", foreground=p["por_vencer"])



    # -- acciones -------------------------------------------------------------

    def _leer_formulario(self):

        return validar_producto(

            self.var_nombre.get(), self.var_existencia.get(),

            self.var_descripcion.get(), self.var_ingreso.get(),

            self.var_precio.get(), self.var_caducidad.get())



    def guardar(self):

        try:

            datos = self._leer_formulario()

            producto = agregar_producto(self.productos, datos)

        except ValueError as err:

            messagebox.showerror("Datos no válidos", str(err))

            return

        self._persistir()

        self.limpiar()

        self._refrescar()

        if self.tree.exists(str(producto["id"])):

            self.tree.see(str(producto["id"]))

        messagebox.showinfo("Producto guardado",

                            f"«{producto['nombre']}» se agregó al inventario.")



    def modificar(self):

        if self.id_editando is None:

            messagebox.showwarning(

                "Seleccione un producto",

                "Seleccione un producto de la lista para modificarlo.")

            return

        try:

            datos = self._leer_formulario()

            producto = modificar_producto(self.productos, self.id_editando, datos)

        except ValueError as err:

            messagebox.showerror("Datos no válidos", str(err))

            return

        self._persistir()

        self.limpiar()

        self._refrescar()

        messagebox.showinfo("Producto modificado",

                            f"«{producto['nombre']}» se actualizó correctamente.")



    def eliminar(self):

        if self.id_editando is None:

            messagebox.showwarning(

                "Seleccione un producto",

                "Seleccione un producto de la lista para eliminarlo.")

            return

        producto = buscar_producto(self.productos, self.id_editando)

        if producto is None:

            self.limpiar()

            self._refrescar()

            return

        if not messagebox.askyesno(

                "Confirmar eliminación",

                f"¿Está seguro de eliminar «{producto['nombre']}» del inventario?\n"

                "Esta acción no se puede deshacer.",

                icon="warning", default="no"):

            return

        eliminar_producto(self.productos, self.id_editando)

        self._persistir()

        self.limpiar()

        self._refrescar()



    def aplicar_filtros(self):
        """Valida y aplica la búsqueda por nombre y los cuatro límites de fecha."""
        try:
            ingreso_desde = self._fecha_filtro(
                self.var_ingreso_desde.get(), "Ingreso desde")
            ingreso_hasta = self._fecha_filtro(
                self.var_ingreso_hasta.get(), "Ingreso hasta")
            caducidad_desde = self._fecha_filtro(
                self.var_caducidad_desde.get(), "Caducidad desde")
            caducidad_hasta = self._fecha_filtro(
                self.var_caducidad_hasta.get(), "Caducidad hasta")

            if ingreso_desde and ingreso_hasta and ingreso_desde > ingreso_hasta:
                raise ValueError("La fecha «Ingreso desde» no puede ser posterior a «Ingreso hasta».")
            if caducidad_desde and caducidad_hasta and caducidad_desde > caducidad_hasta:
                raise ValueError("La fecha «Caducidad desde» no puede ser posterior a «Caducidad hasta».")
        except ValueError as err:
            messagebox.showerror("Filtros no válidos", str(err))
            return

        self.filtros_aplicados = {
            "nombre": self.var_busqueda.get().strip().casefold(),
            "ingreso_desde": ingreso_desde,
            "ingreso_hasta": ingreso_hasta,
            "caducidad_desde": caducidad_desde,
            "caducidad_hasta": caducidad_hasta,
        }
        self._refrescar()

    @staticmethod
    def _fecha_filtro(texto, campo):
        """Devuelve date o None si el filtro está vacío."""
        if not texto.strip():
            return None
        return parsear_fecha(texto, campo)

    def limpiar_filtros(self):
        for variable in (self.var_busqueda, self.var_ingreso_desde,
                         self.var_ingreso_hasta, self.var_caducidad_desde,
                         self.var_caducidad_hasta):
            variable.set("")
        self.filtros_aplicados = {
            "nombre": "",
            "ingreso_desde": None,
            "ingreso_hasta": None,
            "caducidad_desde": None,
            "caducidad_hasta": None,
        }
        self._refrescar()
        self.ent_busqueda.focus_set()

    def _cambiar_orden(self, criterio):
        if self.criterio_orden == criterio:
            self.orden_descendente = not self.orden_descendente
        else:
            self.criterio_orden = criterio
            self.orden_descendente = False
        self._actualizar_botones_orden()
        self._refrescar()

    def _actualizar_botones_orden(self):
        flecha = "↓" if self.orden_descendente else "↑"
        self.btn_orden_nombre.configure(
            text=("Nombre Z-A" if self.orden_descendente else "Nombre A-Z")
            if self.criterio_orden == "nombre" else "Nombre A-Z")
        self.btn_orden_ingreso.configure(
            text=f"Ingreso {flecha}" if self.criterio_orden == "ingreso"
            else "Fecha ingreso")
        self.btn_orden_caducidad.configure(
            text=f"Caducidad {flecha}" if self.criterio_orden == "caducidad"
            else "Fecha caducidad")

    def _obtener_productos_filtrados(self):
        filtros = self.filtros_aplicados
        resultado = []
        for producto in self.productos:
            if filtros["nombre"] and filtros["nombre"] not in producto["nombre"].casefold():
                continue

            fecha_ingreso = date.fromisoformat(producto["ingreso"])
            fecha_caducidad = date.fromisoformat(producto["caducidad"])

            if filtros["ingreso_desde"] and fecha_ingreso < filtros["ingreso_desde"]:
                continue
            if filtros["ingreso_hasta"] and fecha_ingreso > filtros["ingreso_hasta"]:
                continue
            if filtros["caducidad_desde"] and fecha_caducidad < filtros["caducidad_desde"]:
                continue
            if filtros["caducidad_hasta"] and fecha_caducidad > filtros["caducidad_hasta"]:
                continue
            resultado.append(producto)

        return ordenar(resultado, self.criterio_orden, self.orden_descendente)

    def exportar_general(self):
        self._exportar_excel(solo_vencidos=False)

    def exportar_vencidos(self):
        self._exportar_excel(solo_vencidos=True)

    def _exportar_excel(self, solo_vencidos=False):
        """Exporta el inventario completo o solo los productos ya vencidos."""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Font, PatternFill
        except ImportError:
            messagebox.showerror(
                "Falta una librería",
                "Para exportar a Excel instala openpyxl ejecutando:\n\n"
                "python -m pip install openpyxl")
            return

        hoy = date.today()
        if solo_vencidos:
            productos_exportar = [
                p for p in self.productos
                if date.fromisoformat(p["caducidad"]) < hoy
            ]
            titulo = "Productos vencidos"
            nombre_archivo = "productos_vencidos.xlsx"
            nombre_hoja = "Productos vencidos"
        else:
            productos_exportar = list(self.productos)
            titulo = "Inventario general"
            nombre_archivo = "inventario_general.xlsx"
            nombre_hoja = "Inventario general"

        if not productos_exportar:
            mensaje = ("No hay productos vencidos para exportar."
                       if solo_vencidos else "No hay productos registrados para exportar.")
            messagebox.showinfo("Sin datos", mensaje)
            return

        ruta = filedialog.asksaveasfilename(
            title=f"Exportar {titulo.lower()} a Excel",
            defaultextension=".xlsx",
            initialfile=nombre_archivo,
            filetypes=[("Libro de Excel", "*.xlsx")])
        if not ruta:
            return

        libro = Workbook()
        hoja = libro.active
        hoja.title = nombre_hoja
        encabezados = [
            "ID", "Nombre del producto", "Descripción", "Existencia",
            "Precio (Q)", "Fecha de ingreso", "Fecha de caducidad", "Estado",
        ]
        hoja.append(encabezados)

        relleno_encabezado = PatternFill("solid", fgColor="1F5D70")
        fuente_encabezado = Font(bold=True, color="FFFFFF")
        for celda in hoja[1]:
            celda.fill = relleno_encabezado
            celda.font = fuente_encabezado
            celda.alignment = Alignment(horizontal="center", vertical="center")

        for producto in ordenar(productos_exportar, "caducidad"):
            estado = estado_caducidad(producto["caducidad"], hoy)
            nombre_estado = {
                "vencido": "Vencido",
                "por_vencer": "Por vencer",
                "ok": "Vigente",
            }[estado]
            hoja.append([
                producto["id"],
                producto["nombre"],
                producto["descripcion"],
                producto["existencia"],
                producto["precio"],
                date.fromisoformat(producto["ingreso"]),
                date.fromisoformat(producto["caducidad"]),
                nombre_estado,
            ])
            fila = hoja.max_row
            hoja.cell(fila, 5).number_format = '"Q" #,##0.00'
            hoja.cell(fila, 6).number_format = "DD/MM/YYYY"
            hoja.cell(fila, 7).number_format = "DD/MM/YYYY"
            if estado == "vencido":
                for celda in hoja[fila]:
                    celda.fill = PatternFill("solid", fgColor="FCE4E4")
            elif estado == "por_vencer":
                for celda in hoja[fila]:
                    celda.fill = PatternFill("solid", fgColor="FFF2CC")

        anchos = {"A": 8, "B": 28, "C": 42, "D": 13,
                  "E": 15, "F": 18, "G": 18, "H": 16}
        for columna, ancho in anchos.items():
            hoja.column_dimensions[columna].width = ancho
        hoja.freeze_panes = "A2"
        hoja.auto_filter.ref = hoja.dimensions
        hoja.row_dimensions[1].height = 24

        try:
            libro.save(ruta)
        except OSError as err:
            messagebox.showerror("No se pudo exportar", f"No fue posible guardar el Excel:\n{err}")
            return

        messagebox.showinfo(
            "Exportación completada",
            f"Se exportaron {len(productos_exportar)} producto(s) a:\n{ruta}")

    def limpiar(self):

        self.id_editando = None

        for variable in (self.var_nombre, self.var_existencia, self.var_descripcion,

                         self.var_precio, self.var_caducidad):

            variable.set("")

        self.var_ingreso.set(date.today().strftime(FORMATO_FECHA))

        if self.tree.selection():

            self.tree.selection_remove(*self.tree.selection())

        self.lbl_modo.configure(text="Modo: nuevo producto")

        self.ent_nombre.focus_set()



    def _persistir(self):

        try:

            guardar_datos(self.ruta, self.productos, self.tema)

            return True

        except OSError as err:

            messagebox.showerror(

                "No se pudo guardar en disco",

                f"Los cambios se ven en pantalla pero no se guardaron en el archivo:\n"

                f"{self.ruta}\n\n{err}")

            return False



    # -- actualización de la pantalla -------------------------------------------

    def _al_seleccionar(self):

        seleccion = self.tree.selection()

        if not seleccion:

            return

        producto = buscar_producto(self.productos, int(seleccion[0]))

        if producto is None:

            return

        self.id_editando = producto["id"]

        self.var_nombre.set(producto["nombre"])

        self.var_existencia.set(str(producto["existencia"]))

        self.var_descripcion.set(producto["descripcion"])

        self.var_ingreso.set(formato_fecha(producto["ingreso"]))

        self.var_precio.set(f"{producto['precio']:.2f}")

        self.var_caducidad.set(formato_fecha(producto["caducidad"]))

        self.lbl_modo.configure(

            text="Modo: editando (cambie los datos y presione «Modificar»)")



    def _refrescar(self):
        self.tree.delete(*self.tree.get_children())
        vencidos = por_vencer = 0
        total = len(self.productos)
        unidades = sum(p["existencia"] for p in self.productos)

        for p in self.productos:
            estado = estado_caducidad(p["caducidad"])
            vencidos += estado == "vencido"
            por_vencer += estado == "por_vencer"

        visibles = self._obtener_productos_filtrados()
        for p in visibles:
            estado = estado_caducidad(p["caducidad"])
            self.tree.insert(
                "", "end", iid=str(p["id"]),
                tags=(estado,) if estado != "ok" else (),
                values=(p["nombre"], p["descripcion"], p["existencia"],
                        formato_precio(p["precio"]), formato_fecha(p["ingreso"]),
                        formato_fecha(p["caducidad"])))

        palabra = "producto" if total == 1 else "productos"
        self.lbl_resumen.configure(
            text=(f"Mostrando {len(visibles)} de {total} {palabra} · {unidades:,} unidades   |   "
                  f"Vencidos: {vencidos} (rojo)   ·   "
                  f"Vencen en {DIAS_ALERTA} días o menos: {por_vencer} (naranja)"))

        if total == 0:
            texto = ("No hay productos en el inventario.\n"
                     "Complete el formulario y presione «Guardar».")
            self.lbl_vacio.configure(text=texto)
            self.lbl_vacio.place(in_=self.tree, relx=0.5, rely=0.5, anchor="center")
            self.lbl_vacio.lift()
        elif not visibles:
            self.lbl_vacio.configure(
                text="No se encontraron productos con los filtros indicados.\n"
                     "Pruebe con otro nombre o rango de fechas.")
            self.lbl_vacio.place(in_=self.tree, relx=0.5, rely=0.5, anchor="center")
            self.lbl_vacio.lift()
        else:
            self.lbl_vacio.place_forget()



def main():

    app = AppInventario()

    app.mainloop()





if __name__ == "__main__":

    main()

"""Sistema de Administración de Taxis
Python 3 + Tkinter (tema moderno propio) + SQLite. Solo biblioteca estándar.

Ejecutar:  python taxi_manager.py
"""
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

DB_FILE = "taxis.db"
TARIFA_BASE = 10.00   # Q por viaje
TARIFA_KM = 5.00      # Q por kilómetro
MONEDA = "Q"

ESTADOS_TAXI = ["Disponible", "En servicio", "Mantenimiento"]

# ---- Paleta y tipografía ----
BG = "#F3F4F6"
CARD = "#FFFFFF"
SIDEBAR = "#111827"
SIDEBAR_HOVER = "#1F2937"
ACENTO = "#F59E0B"
ACENTO_OSC = "#D97706"
TEXTO = "#111827"
TEXTO_SUAVE = "#6B7280"
BORDE = "#E5E7EB"
VERDE = "#059669"
ROJO = "#DC2626"
AZUL = "#2563EB"
FUENTE = ("Segoe UI", 10)
FUENTE_B = ("Segoe UI", 10, "bold")
FUENTE_TITULO = ("Segoe UI", 20, "bold")
FUENTE_SUB = ("Segoe UI", 13, "bold")
FUENTE_KPI = ("Segoe UI", 24, "bold")

COLOR_ESTADO = {
    "Disponible": VERDE, "Finalizado": VERDE,
    "En servicio": ACENTO_OSC, "En curso": ACENTO_OSC,
    "Mantenimiento": ROJO, "Cancelado": ROJO,
}


def calcular_tarifa(km):
    return round(TARIFA_BASE + TARIFA_KM * km, 2)


# --------------------------------------------------------------------------
# Capa de datos (SQLite)
# --------------------------------------------------------------------------
class Database:
    def __init__(self, path=DB_FILE):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._crear_tablas()

    def _crear_tablas(self):
        with self.conn:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS taxis (
                    id     INTEGER PRIMARY KEY AUTOINCREMENT,
                    placa  TEXT NOT NULL UNIQUE,
                    marca  TEXT NOT NULL,
                    modelo TEXT NOT NULL,
                    anio   INTEGER NOT NULL,
                    estado TEXT NOT NULL DEFAULT 'Disponible'
                );
                CREATE TABLE IF NOT EXISTS conductores (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre   TEXT NOT NULL,
                    licencia TEXT NOT NULL UNIQUE,
                    telefono TEXT,
                    taxi_id  INTEGER REFERENCES taxis(id) ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS viajes (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha        TEXT NOT NULL,
                    cliente      TEXT NOT NULL,
                    origen       TEXT NOT NULL,
                    destino      TEXT NOT NULL,
                    km           REAL NOT NULL,
                    tarifa       REAL NOT NULL,
                    conductor_id INTEGER NOT NULL REFERENCES conductores(id),
                    taxi_id      INTEGER NOT NULL REFERENCES taxis(id),
                    estado       TEXT NOT NULL DEFAULT 'En curso'
                );
                """
            )

    def query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def execute(self, sql, params=()):
        with self.conn:
            return self.conn.execute(sql, params).lastrowid

    # ---- Taxis ----
    def listar_taxis(self):
        return self.query("SELECT * FROM taxis ORDER BY placa")

    def guardar_taxi(self, placa, marca, modelo, anio, estado, taxi_id=None):
        if taxi_id is None:
            self.execute(
                "INSERT INTO taxis (placa, marca, modelo, anio, estado) VALUES (?,?,?,?,?)",
                (placa, marca, modelo, anio, estado),
            )
        else:
            self.execute(
                "UPDATE taxis SET placa=?, marca=?, modelo=?, anio=?, estado=? WHERE id=?",
                (placa, marca, modelo, anio, estado, taxi_id),
            )

    def eliminar_taxi(self, taxi_id):
        self.execute("DELETE FROM taxis WHERE id=?", (taxi_id,))

    # ---- Conductores ----
    def listar_conductores(self):
        return self.query(
            """SELECT c.*, t.placa FROM conductores c
               LEFT JOIN taxis t ON t.id = c.taxi_id ORDER BY c.nombre"""
        )

    def guardar_conductor(self, nombre, licencia, telefono, taxi_id, conductor_id=None):
        if conductor_id is None:
            self.execute(
                "INSERT INTO conductores (nombre, licencia, telefono, taxi_id) VALUES (?,?,?,?)",
                (nombre, licencia, telefono, taxi_id),
            )
        else:
            self.execute(
                "UPDATE conductores SET nombre=?, licencia=?, telefono=?, taxi_id=? WHERE id=?",
                (nombre, licencia, telefono, taxi_id, conductor_id),
            )

    def eliminar_conductor(self, conductor_id):
        self.execute("DELETE FROM conductores WHERE id=?", (conductor_id,))

    # ---- Viajes ----
    def listar_viajes(self):
        return self.query(
            """SELECT v.*, c.nombre AS conductor, t.placa
               FROM viajes v
               JOIN conductores c ON c.id = v.conductor_id
               JOIN taxis t ON t.id = v.taxi_id
               ORDER BY v.id DESC"""
        )

    def conductores_con_taxi(self):
        return self.query(
            """SELECT c.id, c.nombre, t.placa, t.estado FROM conductores c
               JOIN taxis t ON t.id = c.taxi_id ORDER BY c.nombre"""
        )

    def crear_viaje(self, cliente, origen, destino, km, conductor_id):
        fila = self.query(
            """SELECT c.taxi_id, t.estado FROM conductores c
               LEFT JOIN taxis t ON t.id = c.taxi_id WHERE c.id=?""",
            (conductor_id,),
        )
        if not fila or fila[0]["taxi_id"] is None:
            raise ValueError("El conductor no tiene un taxi asignado.")
        if fila[0]["estado"] != "Disponible":
            raise ValueError(f"El taxi está '{fila[0]['estado']}', no disponible.")
        taxi_id = fila[0]["taxi_id"]
        tarifa = calcular_tarifa(km)
        with self.conn:
            self.conn.execute(
                """INSERT INTO viajes (fecha, cliente, origen, destino, km, tarifa,
                                       conductor_id, taxi_id, estado)
                   VALUES (?,?,?,?,?,?,?,?, 'En curso')""",
                (datetime.now().strftime("%Y-%m-%d %H:%M"), cliente, origen, destino,
                 km, tarifa, conductor_id, taxi_id),
            )
            self.conn.execute("UPDATE taxis SET estado='En servicio' WHERE id=?", (taxi_id,))
        return tarifa

    def cerrar_viaje(self, viaje_id, nuevo_estado):
        """nuevo_estado: 'Finalizado' o 'Cancelado'."""
        fila = self.query("SELECT estado, taxi_id FROM viajes WHERE id=?", (viaje_id,))
        if not fila:
            raise ValueError("El viaje no existe.")
        if fila[0]["estado"] != "En curso":
            raise ValueError("Solo se pueden cerrar viajes que estén 'En curso'.")
        with self.conn:
            self.conn.execute("UPDATE viajes SET estado=? WHERE id=?", (nuevo_estado, viaje_id))
            self.conn.execute(
                "UPDATE taxis SET estado='Disponible' WHERE id=? AND estado='En servicio'",
                (fila[0]["taxi_id"],),
            )

    # ---- Reportes ----
    def resumen(self):
        r = self.query(
            """SELECT
                 COALESCE(SUM(CASE WHEN estado='Finalizado' THEN tarifa END), 0) AS ingresos,
                 SUM(estado='Finalizado') AS finalizados,
                 SUM(estado='Cancelado')  AS cancelados,
                 SUM(estado='En curso')   AS en_curso
               FROM viajes"""
        )[0]
        datos = {k: (r[k] or 0) for k in r.keys()}
        t = self.query(
            "SELECT COUNT(*) AS total, COALESCE(SUM(estado='Disponible'), 0) AS disponibles FROM taxis"
        )[0]
        datos["taxis_total"] = t["total"]
        datos["taxis_disponibles"] = t["disponibles"]
        return datos

    def ingresos_por_conductor(self):
        return self.query(
            """SELECT c.nombre,
                      COUNT(CASE WHEN v.estado='Finalizado' THEN 1 END) AS viajes,
                      COALESCE(SUM(CASE WHEN v.estado='Finalizado' THEN v.km END), 0) AS km,
                      COALESCE(SUM(CASE WHEN v.estado='Finalizado' THEN v.tarifa END), 0) AS ingresos
               FROM conductores c LEFT JOIN viajes v ON v.conductor_id = c.id
               GROUP BY c.id ORDER BY ingresos DESC"""
        )


# --------------------------------------------------------------------------
# Estilo moderno
# --------------------------------------------------------------------------
def aplicar_estilo(root):
    s = ttk.Style(root)
    s.theme_use("clam")
    root.configure(bg=BG)
    s.configure(".", font=FUENTE, background=BG, foreground=TEXTO)

    s.configure("TFrame", background=BG)
    s.configure("Card.TFrame", background=CARD)
    s.configure("Sidebar.TFrame", background=SIDEBAR)
    s.configure("TLabel", background=BG, foreground=TEXTO)
    s.configure("Card.TLabel", background=CARD, foreground=TEXTO_SUAVE)
    s.configure("CardTitle.TLabel", background=CARD, foreground=TEXTO, font=FUENTE_SUB)
    s.configure("Title.TLabel", background=BG, foreground=TEXTO, font=FUENTE_TITULO)
    s.configure("Sub.TLabel", background=BG, foreground=TEXTO_SUAVE)
    s.configure("Brand.TLabel", background=SIDEBAR, foreground=ACENTO, font=("Segoe UI", 16, "bold"))
    s.configure("BrandSub.TLabel", background=SIDEBAR, foreground="#9CA3AF")
    s.configure("Estado.TLabel", background=BG, font=FUENTE_B)

    s.configure("TEntry", fieldbackground="white", bordercolor=BORDE, lightcolor=BORDE,
                darkcolor=BORDE, padding=7)
    s.map("TEntry", bordercolor=[("focus", ACENTO)], lightcolor=[("focus", ACENTO)],
          darkcolor=[("focus", ACENTO)])
    s.configure("TCombobox", fieldbackground="white", background="white", bordercolor=BORDE,
                lightcolor=BORDE, darkcolor=BORDE, padding=7, arrowsize=16)
    s.map("TCombobox", fieldbackground=[("readonly", "white")],
          bordercolor=[("focus", ACENTO)])

    # Botones
    base = dict(borderwidth=0, focusthickness=0, padding=(16, 9), font=FUENTE_B)
    s.configure("Accent.TButton", background=ACENTO, foreground=TEXTO, **base)
    s.map("Accent.TButton", background=[("active", ACENTO_OSC)])
    s.configure("Ghost.TButton", background="#E5E7EB", foreground=TEXTO, **base)
    s.map("Ghost.TButton", background=[("active", "#D1D5DB")])
    s.configure("Danger.TButton", background="#FEE2E2", foreground=ROJO, **base)
    s.map("Danger.TButton", background=[("active", "#FECACA")])
    s.configure("Nav.TButton", background=SIDEBAR, foreground="#D1D5DB", anchor="w",
                borderwidth=0, focusthickness=0, padding=(20, 12), font=FUENTE)
    s.map("Nav.TButton", background=[("active", SIDEBAR_HOVER)])
    s.configure("NavActive.TButton", background=SIDEBAR_HOVER, foreground=ACENTO, anchor="w",
                borderwidth=0, focusthickness=0, padding=(20, 12), font=FUENTE_B)

    # Tablas
    s.configure("Treeview", rowheight=34, background="white", fieldbackground="white",
                foreground=TEXTO, borderwidth=0, font=FUENTE)
    s.configure("Treeview.Heading", background="#F9FAFB", foreground=TEXTO_SUAVE,
                font=FUENTE_B, relief="flat", padding=(8, 8), borderwidth=0)
    s.map("Treeview.Heading", background=[("active", "#F3F4F6")])
    s.map("Treeview", background=[("selected", "#FEF3C7")], foreground=[("selected", TEXTO)])
    s.configure("Vertical.TScrollbar", background="#D1D5DB", troughcolor="white",
                borderwidth=0, arrowsize=12)


# --------------------------------------------------------------------------
# Componentes de interfaz reutilizables
# --------------------------------------------------------------------------
def crear_tree(parent, columnas):
    """columnas: lista de (clave, título, ancho)."""
    marco = ttk.Frame(parent, style="Card.TFrame")
    tree = ttk.Treeview(marco, columns=[c[0] for c in columnas],
                        show="headings", selectmode="browse")
    for clave, titulo, ancho in columnas:
        tree.heading(clave, text=titulo, anchor="w")
        tree.column(clave, width=ancho, anchor="w")
    tree.tag_configure("par", background="#FFFFFF")
    tree.tag_configure("impar", background="#F9FAFB")
    for estado, color in COLOR_ESTADO.items():
        tree.tag_configure(estado, foreground=color)
    sb = ttk.Scrollbar(marco, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return marco, tree


def tarjeta_tabla(parent, titulo, columnas, filtro_var=None):
    card = ttk.Frame(parent, style="Card.TFrame", padding=18)
    cab = ttk.Frame(card, style="Card.TFrame")
    cab.pack(fill="x", pady=(0, 10))
    ttk.Label(cab, text=titulo, style="CardTitle.TLabel").pack(side="left")
    if filtro_var is not None:
        ttk.Entry(cab, textvariable=filtro_var, width=24).pack(side="right")
        ttk.Label(cab, text="Buscar", style="Card.TLabel").pack(side="right", padx=8)
    marco, tree = crear_tree(card, columnas)
    marco.pack(fill="both", expand=True)
    return card, tree


def tarjeta_kpi(parent, titulo, color):
    marco = tk.Frame(parent, bg=CARD)
    tk.Frame(marco, bg=color, width=6).pack(side="left", fill="y")
    interior = tk.Frame(marco, bg=CARD)
    interior.pack(side="left", fill="both", expand=True, padx=18, pady=16)
    tk.Label(interior, text=titulo, bg=CARD, fg=TEXTO_SUAVE, font=FUENTE).pack(anchor="w")
    var = tk.StringVar(value="0")
    tk.Label(interior, textvariable=var, bg=CARD, fg=TEXTO, font=FUENTE_KPI).pack(anchor="w")
    return marco, var


def campo(parent, texto, var, fila, col, valores=None, ancho=18):
    ttk.Label(parent, text=texto, style="Card.TLabel").grid(
        row=fila * 2, column=col, sticky="w", padx=8)
    if valores is None:
        w = ttk.Entry(parent, textvariable=var, width=ancho)
    else:
        w = ttk.Combobox(parent, textvariable=var, values=valores, state="readonly", width=ancho)
    w.grid(row=fila * 2 + 1, column=col, sticky="ew", padx=8, pady=(2, 10))
    parent.columnconfigure(col, weight=1)
    return w


def boton(parent, texto, comando, estilo="Ghost.TButton"):
    b = ttk.Button(parent, text=texto, command=comando, style=estilo, cursor="hand2")
    b.pack(side="left", padx=(8, 0))
    return b


def insertar(tree, iid, valores, indice, estado=None):
    tags = ["par" if indice % 2 == 0 else "impar"]
    if estado in COLOR_ESTADO:
        tags.append(estado)
    tree.insert("", "end", iid=str(iid), values=valores, tags=tuple(tags))


def coincide(valores, texto):
    texto = texto.strip().lower()
    return not texto or texto in " ".join(str(v) for v in valores).lower()


def limpiar_tree(tree):
    tree.delete(*tree.get_children())


def seleccionado(tree):
    sel = tree.selection()
    return int(sel[0]) if sel else None


class Pagina(ttk.Frame):
    """Página base: encabezado + contenido. Las subclases implementan refrescar()."""

    def __init__(self, master, db, on_change, notificar, titulo, subtitulo):
        super().__init__(master, padding=(28, 22))
        self.db, self.on_change, self.notificar = db, on_change, notificar
        ttk.Label(self, text=titulo, style="Title.TLabel").pack(anchor="w")
        ttk.Label(self, text=subtitulo, style="Sub.TLabel").pack(anchor="w", pady=(0, 14))

    def refrescar(self):
        pass


# --------------------------------------------------------------------------
# Página: Inicio (panel de control)
# --------------------------------------------------------------------------
class InicioPagina(Pagina):
    def __init__(self, master, db, on_change, notificar):
        super().__init__(master, db, on_change, notificar,
                         "Panel de control", "Resumen de la operación de la flota")
        fila = ttk.Frame(self)
        fila.pack(fill="x")
        self.kpis = {}
        for i, (clave, titulo, color) in enumerate([
                ("ingresos", "Ingresos totales", VERDE),
                ("finalizados", "Viajes finalizados", AZUL),
                ("en_curso", "Viajes en curso", ACENTO),
                ("disponibles", "Taxis disponibles", "#7C3AED")]):
            marco, var = tarjeta_kpi(fila, titulo, color)
            marco.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            fila.columnconfigure(i, weight=1, uniform="kpi")
            self.kpis[clave] = var

        inferior = ttk.Frame(self)
        inferior.pack(fill="both", expand=True, pady=(16, 0))
        inferior.columnconfigure(0, weight=2, uniform="b")
        inferior.columnconfigure(1, weight=3, uniform="b")
        inferior.rowconfigure(0, weight=1)
        c1, self.tree_cond = tarjeta_tabla(inferior, "Ingresos por conductor", [
            ("nombre", "Conductor", 140), ("viajes", "Viajes", 60), (
                "ingresos", f"Ingresos ({MONEDA})", 100)])
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        c2, self.tree_viajes = tarjeta_tabla(inferior, "Últimos viajes", [
            ("fecha", "Fecha", 110), ("cliente", "Cliente", 100), ("destino", "Destino", 100),
            ("tarifa", f"Tarifa ({MONEDA})", 80), ("estado", "Estado", 80)])
        c2.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.refrescar()

    def refrescar(self):
        r = self.db.resumen()
        self.kpis["ingresos"].set(f"{MONEDA}{r['ingresos']:,.2f}")
        self.kpis["finalizados"].set(str(r["finalizados"]))
        self.kpis["en_curso"].set(str(r["en_curso"]))
        self.kpis["disponibles"].set(f"{r['taxis_disponibles']} / {r['taxis_total']}")
        limpiar_tree(self.tree_cond)
        for i, f in enumerate(self.db.ingresos_por_conductor()):
            insertar(self.tree_cond, i, (f["nombre"], f["viajes"], f"{f['ingresos']:.2f}"), i)
        limpiar_tree(self.tree_viajes)
        for i, v in enumerate(self.db.listar_viajes()[:12]):
            insertar(self.tree_viajes, v["id"], (
                v["fecha"], v["cliente"], v["destino"], f"{v['tarifa']:.2f}", v["estado"]),
                i, v["estado"])


# --------------------------------------------------------------------------
# Página: Taxis
# --------------------------------------------------------------------------
class TaxisPagina(Pagina):
    def __init__(self, master, db, on_change, notificar):
        super().__init__(master, db, on_change, notificar,
                         "Taxis", "Administra los vehículos de la flota")
        self.vars = {k: tk.StringVar() for k in ("placa", "marca", "modelo", "anio", "estado")}
        self.vars["estado"].set(ESTADOS_TAXI[0])
        self.filtro = tk.StringVar()

        form = ttk.Frame(self, style="Card.TFrame", padding=18)
        form.pack(fill="x")
        campo(form, "Placa", self.vars["placa"], 0, 0)
        campo(form, "Marca", self.vars["marca"], 0, 1)
        campo(form, "Modelo", self.vars["modelo"], 0, 2)
        campo(form, "Año", self.vars["anio"], 0, 3)
        campo(form, "Estado", self.vars["estado"], 0, 4, valores=ESTADOS_TAXI)
        barra = ttk.Frame(form, style="Card.TFrame")
        barra.grid(row=2, column=0, columnspan=5, sticky="e", pady=(4, 0))
        boton(barra, "Limpiar", self.limpiar)
        boton(barra, "Eliminar", self.eliminar, "Danger.TButton")
        boton(barra, "Actualizar", self.actualizar)
        boton(barra, "Agregar taxi", self.agregar, "Accent.TButton")

        card, self.tree = tarjeta_tabla(self, "Flota", [
            ("placa", "Placa", 110), ("marca", "Marca", 130), ("modelo", "Modelo", 130),
            ("anio", "Año", 70), ("estado", "Estado", 120)], self.filtro)
        card.pack(fill="both", expand=True, pady=(16, 0))
        self.tree.bind("<<TreeviewSelect>>", self.al_seleccionar)
        self.filtro.trace_add("write", lambda *_: self.refrescar())
        self.refrescar()

    def leer_form(self):
        placa = self.vars["placa"].get().strip().upper()
        marca = self.vars["marca"].get().strip()
        modelo = self.vars["modelo"].get().strip()
        if not (placa and marca and modelo):
            raise ValueError("Placa, marca y modelo son obligatorios.")
        try:
            anio = int(self.vars["anio"].get())
        except ValueError:
            raise ValueError("El año debe ser un número entero.")
        if not 1980 <= anio <= datetime.now().year + 1:
            raise ValueError("El año no es válido.")
        return placa, marca, modelo, anio, self.vars["estado"].get()

    def agregar(self):
        try:
            self.db.guardar_taxi(*self.leer_form())
        except ValueError as e:
            return self.notificar(str(e), True)
        except sqlite3.IntegrityError:
            return self.notificar("Ya existe un taxi con esa placa.", True)
        self.limpiar()
        self.on_change()
        self.notificar("Taxi agregado correctamente.")

    def actualizar(self):
        taxi_id = seleccionado(self.tree)
        if taxi_id is None:
            return self.notificar("Seleccione un taxi de la lista.", True)
        try:
            self.db.guardar_taxi(*self.leer_form(), taxi_id=taxi_id)
        except ValueError as e:
            return self.notificar(str(e), True)
        except sqlite3.IntegrityError:
            return self.notificar("Ya existe un taxi con esa placa.", True)
        self.on_change()
        self.notificar("Taxi actualizado.")

    def eliminar(self):
        taxi_id = seleccionado(self.tree)
        if taxi_id is None:
            return self.notificar("Seleccione un taxi de la lista.", True)
        if not messagebox.askyesno("Confirmar", "¿Eliminar el taxi seleccionado?"):
            return
        try:
            self.db.eliminar_taxi(taxi_id)
        except sqlite3.IntegrityError:
            return self.notificar("El taxi tiene viajes registrados y no se puede eliminar.", True)
        self.limpiar()
        self.on_change()
        self.notificar("Taxi eliminado.")

    def limpiar(self):
        for k, v in self.vars.items():
            v.set(ESTADOS_TAXI[0] if k == "estado" else "")
        self.tree.selection_remove(self.tree.selection())

    def al_seleccionar(self, _evento=None):
        taxi_id = seleccionado(self.tree)
        if taxi_id is None:
            return
        valores = self.tree.item(str(taxi_id), "values")
        for clave, valor in zip(("placa", "marca", "modelo", "anio", "estado"), valores):
            self.vars[clave].set(valor)

    def refrescar(self):
        limpiar_tree(self.tree)
        i = 0
        for t in self.db.listar_taxis():
            valores = (t["placa"], t["marca"], t["modelo"], t["anio"], t["estado"])
            if coincide(valores, self.filtro.get()):
                insertar(self.tree, t["id"], valores, i, t["estado"])
                i += 1


# --------------------------------------------------------------------------
# Página: Conductores
# --------------------------------------------------------------------------
class ConductoresPagina(Pagina):
    SIN_TAXI = "Sin asignar"

    def __init__(self, master, db, on_change, notificar):
        super().__init__(master, db, on_change, notificar,
                         "Conductores", "Registra conductores y asígnales un taxi")
        self.vars = {k: tk.StringVar() for k in ("nombre", "licencia", "telefono", "taxi")}
        self.vars["taxi"].set(self.SIN_TAXI)
        self.taxis_por_texto = {self.SIN_TAXI: None}
        self.filtro = tk.StringVar()

        form = ttk.Frame(self, style="Card.TFrame", padding=18)
        form.pack(fill="x")
        campo(form, "Nombre completo", self.vars["nombre"], 0, 0, ancho=26)
        campo(form, "Licencia", self.vars["licencia"], 0, 1)
        campo(form, "Teléfono", self.vars["telefono"], 0, 2)
        self.combo_taxi = campo(form, "Taxi asignado", self.vars["taxi"], 0, 3,
                                valores=[self.SIN_TAXI])
        barra = ttk.Frame(form, style="Card.TFrame")
        barra.grid(row=2, column=0, columnspan=4, sticky="e", pady=(4, 0))
        boton(barra, "Limpiar", self.limpiar)
        boton(barra, "Eliminar", self.eliminar, "Danger.TButton")
        boton(barra, "Actualizar", self.actualizar)
        boton(barra, "Agregar conductor", self.agregar, "Accent.TButton")

        card, self.tree = tarjeta_tabla(self, "Equipo de conductores", [
            ("nombre", "Nombre", 200), ("licencia", "Licencia", 120),
            ("telefono", "Teléfono", 120), ("taxi", "Taxi", 100)], self.filtro)
        card.pack(fill="both", expand=True, pady=(16, 0))
        self.tree.bind("<<TreeviewSelect>>", self.al_seleccionar)
        self.filtro.trace_add("write", lambda *_: self.refrescar())
        self.refrescar()

    def leer_form(self):
        nombre = self.vars["nombre"].get().strip()
        licencia = self.vars["licencia"].get().strip().upper()
        if not (nombre and licencia):
            raise ValueError("Nombre y licencia son obligatorios.")
        taxi_id = self.taxis_por_texto.get(self.vars["taxi"].get())
        return nombre, licencia, self.vars["telefono"].get().strip(), taxi_id

    def agregar(self):
        try:
            self.db.guardar_conductor(*self.leer_form())
        except ValueError as e:
            return self.notificar(str(e), True)
        except sqlite3.IntegrityError:
            return self.notificar("Ya existe un conductor con esa licencia.", True)
        self.limpiar()
        self.on_change()
        self.notificar("Conductor agregado correctamente.")

    def actualizar(self):
        cid = seleccionado(self.tree)
        if cid is None:
            return self.notificar("Seleccione un conductor de la lista.", True)
        try:
            self.db.guardar_conductor(*self.leer_form(), conductor_id=cid)
        except ValueError as e:
            return self.notificar(str(e), True)
        except sqlite3.IntegrityError:
            return self.notificar("Ya existe un conductor con esa licencia.", True)
        self.on_change()
        self.notificar("Conductor actualizado.")

    def eliminar(self):
        cid = seleccionado(self.tree)
        if cid is None:
            return self.notificar("Seleccione un conductor de la lista.", True)
        if not messagebox.askyesno("Confirmar", "¿Eliminar el conductor seleccionado?"):
            return
        try:
            self.db.eliminar_conductor(cid)
        except sqlite3.IntegrityError:
            return self.notificar(
                "El conductor tiene viajes registrados y no se puede eliminar.", True)
        self.limpiar()
        self.on_change()
        self.notificar("Conductor eliminado.")

    def limpiar(self):
        for k, v in self.vars.items():
            v.set(self.SIN_TAXI if k == "taxi" else "")
        self.tree.selection_remove(self.tree.selection())

    def al_seleccionar(self, _evento=None):
        cid = seleccionado(self.tree)
        if cid is None:
            return
        nombre, licencia, telefono, placa = self.tree.item(str(cid), "values")
        self.vars["nombre"].set(nombre)
        self.vars["licencia"].set(licencia)
        self.vars["telefono"].set(telefono)
        self.vars["taxi"].set(placa if placa in self.taxis_por_texto else self.SIN_TAXI)

    def refrescar(self):
        self.taxis_por_texto = {self.SIN_TAXI: None}
        for t in self.db.listar_taxis():
            self.taxis_por_texto[t["placa"]] = t["id"]
        self.combo_taxi["values"] = list(self.taxis_por_texto)
        limpiar_tree(self.tree)
        i = 0
        for c in self.db.listar_conductores():
            valores = (c["nombre"], c["licencia"], c["telefono"] or "", c["placa"] or "")
            if coincide(valores, self.filtro.get()):
                insertar(self.tree, c["id"], valores, i)
                i += 1


# --------------------------------------------------------------------------
# Página: Viajes
# --------------------------------------------------------------------------
class ViajesPagina(Pagina):
    def __init__(self, master, db, on_change, notificar):
        super().__init__(master, db, on_change, notificar,
                         "Viajes", "Registra, finaliza o cancela servicios de taxi")
        self.vars = {k: tk.StringVar() for k in ("cliente", "origen", "destino", "km", "conductor")}
        self.conductores_por_texto = {}
        self.var_tarifa = tk.StringVar(value=f"{MONEDA}0.00")
        self.filtro = tk.StringVar()

        form = ttk.Frame(self, style="Card.TFrame", padding=18)
        form.pack(fill="x")
        campo(form, "Cliente", self.vars["cliente"], 0, 0)
        campo(form, "Origen", self.vars["origen"], 0, 1)
        campo(form, "Destino", self.vars["destino"], 0, 2)
        campo(form, "Kilómetros", self.vars["km"], 0, 3, ancho=10)
        self.combo = campo(form, "Conductor (taxi)", self.vars["conductor"], 1, 0, valores=[],
                           ancho=34)
        self.combo.grid_configure(columnspan=2)
        ttk.Label(form, text="Tarifa estimada", style="Card.TLabel").grid(
            row=2, column=2, sticky="w", padx=8)
        ttk.Label(form, textvariable=self.var_tarifa, style="CardTitle.TLabel").grid(
            row=3, column=2, sticky="w", padx=8)
        self.vars["km"].trace_add("write", self.actualizar_tarifa)

        barra = ttk.Frame(form, style="Card.TFrame")
        barra.grid(row=4, column=0, columnspan=4, sticky="e", pady=(4, 0))
        boton(barra, "Cancelar viaje", lambda: self.cerrar("Cancelado"), "Danger.TButton")
        boton(barra, "Finalizar viaje", lambda: self.cerrar("Finalizado"))
        boton(barra, "Registrar viaje", self.registrar, "Accent.TButton")

        card, self.tree = tarjeta_tabla(self, "Historial de viajes", [
            ("fecha", "Fecha", 120), ("cliente", "Cliente", 110), ("origen", "Origen", 110),
            ("destino", "Destino", 110), ("km", "Km", 60), ("tarifa", f"Tarifa ({MONEDA})", 90),
            ("conductor", "Conductor", 120), ("placa", "Placa", 80), ("estado", "Estado", 90)],
            self.filtro)
        card.pack(fill="both", expand=True, pady=(16, 0))
        self.filtro.trace_add("write", lambda *_: self.refrescar())
        self.refrescar()

    def leer_km(self):
        try:
            km = float(self.vars["km"].get().replace(",", "."))
        except ValueError:
            raise ValueError("Los kilómetros deben ser un número.")
        if km <= 0:
            raise ValueError("Los kilómetros deben ser mayores que cero.")
        return km

    def actualizar_tarifa(self, *_):
        try:
            self.var_tarifa.set(f"{MONEDA}{calcular_tarifa(self.leer_km()):.2f}")
        except ValueError:
            self.var_tarifa.set(f"{MONEDA}0.00")

    def registrar(self):
        cliente = self.vars["cliente"].get().strip()
        origen = self.vars["origen"].get().strip()
        destino = self.vars["destino"].get().strip()
        cid = self.conductores_por_texto.get(self.vars["conductor"].get())
        try:
            if not (cliente and origen and destino):
                raise ValueError("Cliente, origen y destino son obligatorios.")
            if cid is None:
                raise ValueError("Seleccione un conductor disponible.")
            tarifa = self.db.crear_viaje(cliente, origen, destino, self.leer_km(), cid)
        except ValueError as e:
            return self.notificar(str(e), True)
        for k in ("cliente", "origen", "destino", "km"):
            self.vars[k].set("")
        self.on_change()
        self.notificar(f"Viaje registrado. Tarifa: {MONEDA}{tarifa:.2f}")

    def cerrar(self, estado):
        vid = seleccionado(self.tree)
        if vid is None:
            return self.notificar("Seleccione un viaje de la lista.", True)
        try:
            self.db.cerrar_viaje(vid, estado)
        except ValueError as e:
            return self.notificar(str(e), True)
        self.on_change()
        self.notificar(f"Viaje {estado.lower()}.")

    def refrescar(self):
        self.conductores_por_texto = {}
        for c in self.db.conductores_con_taxi():
            self.conductores_por_texto[f"{c['nombre']} - {c['placa']} ({c['estado']})"] = c["id"]
        self.combo["values"] = list(self.conductores_por_texto)
        self.vars["conductor"].set("")
        limpiar_tree(self.tree)
        i = 0
        for v in self.db.listar_viajes():
            valores = (v["fecha"], v["cliente"], v["origen"], v["destino"], f"{v['km']:.1f}",
                       f"{v['tarifa']:.2f}", v["conductor"], v["placa"], v["estado"])
            if coincide(valores, self.filtro.get()):
                insertar(self.tree, v["id"], valores, i, v["estado"])
                i += 1


# --------------------------------------------------------------------------
# Aplicación principal
# --------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TaxiAdmin - Sistema de Administración de Taxis")
        self.geometry("1180x700")
        self.minsize(1000, 600)
        aplicar_estilo(self)
        self.db = Database()
        self._after_id = None

        # Barra lateral
        lateral = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        lateral.pack(side="left", fill="y")
        lateral.pack_propagate(False)
        ttk.Label(lateral, text="TaxiAdmin", style="Brand.TLabel").pack(
            anchor="w", padx=20, pady=(26, 0))
        ttk.Label(lateral, text="Gestión de flota", style="BrandSub.TLabel").pack(
            anchor="w", padx=20, pady=(0, 24))

        # Contenido
        derecha = ttk.Frame(self)
        derecha.pack(side="left", fill="both", expand=True)
        self.estado = ttk.Label(derecha, text="", style="Estado.TLabel", padding=(28, 6))
        self.estado.pack(side="bottom", fill="x")
        contenedor = ttk.Frame(derecha)
        contenedor.pack(side="top", fill="both", expand=True)
        contenedor.rowconfigure(0, weight=1)
        contenedor.columnconfigure(0, weight=1)

        clases = [("Inicio", InicioPagina), ("Taxis", TaxisPagina),
                  ("Conductores", ConductoresPagina), ("Viajes", ViajesPagina)]
        self.paginas, self.botones = {}, {}
        for nombre, clase in clases:
            pagina = clase(contenedor, self.db, self.refrescar_todo, self.notificar)
            pagina.grid(row=0, column=0, sticky="nsew")
            self.paginas[nombre] = pagina
            b = ttk.Button(lateral, text=nombre, style="Nav.TButton", cursor="hand2",
                           command=lambda n=nombre: self.mostrar(n))
            b.pack(fill="x")
            self.botones[nombre] = b
        self.mostrar("Inicio")

    def mostrar(self, nombre):
        for n, b in self.botones.items():
            b.configure(style="NavActive.TButton" if n == nombre else "Nav.TButton")
        self.paginas[nombre].refrescar()
        self.paginas[nombre].tkraise()

    def refrescar_todo(self):
        for pagina in self.paginas.values():
            pagina.refrescar()

    def notificar(self, mensaje, error=False):
        self.estado.configure(text=mensaje, foreground=ROJO if error else VERDE)
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(5000, lambda: self.estado.configure(text=""))


if __name__ == "__main__":
    App().mainloop()
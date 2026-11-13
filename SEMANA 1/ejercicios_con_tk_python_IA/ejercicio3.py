"""Administrador de tareas con interfaz gráfica Tkinter.

Características:
- Registrar tareas con nombre, descripción y prioridad.
- Marcar tareas como completadas.
- Eliminar tareas con confirmación.
- Filtrar y ordenar las tareas.
- Guardar los datos automáticamente en tareas.json.

No requiere instalar paquetes externos; utiliza únicamente la biblioteca estándar.
"""

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


class AdministradorTareas:
    """Ventana principal y lógica del administrador de tareas."""

    COLORES = {
        "fondo": "#f3f6fb",
        "tarjeta": "#ffffff",
        "texto": "#263445",
        "secundario": "#718096",
        "borde": "#e1e7ef",
        "primario": "#39aeca",
        "primario_hover": "#2797b5",
        "peligro": "#d9534f",
        "peligro_hover": "#bd3d39",
        "suave": "#edf2f7",
        "verde": "#21875a",
        "rojo": "#bd4545",
    }

    PRIORIDADES = ("Alta", "Media", "Baja")
    ESTADOS = ("Pendiente", "Completada")
    ARCHIVO_DATOS = Path(__file__).with_name("tareas.json")

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("To-Do Reminders | Administrador de tareas")
        self.root.geometry("1100x780")
        self.root.minsize(850, 650)
        self.root.configure(bg=self.COLORES["fondo"])

        self.tareas = self.cargar_tareas()
        self.siguiente_id = self.calcular_siguiente_id()
        self.filtro_estado = tk.StringVar(value="Todas")
        self.orden = tk.StringVar(value="Creación")

        self.configurar_estilos()
        self.crear_interfaz()
        self.actualizar_vista()

        self.root.protocol("WM_DELETE_WINDOW", self.salir)
        self.root.bind("<Control-Return>", lambda _event: self.agregar_tarea())
        self.root.bind("<Delete>", lambda _event: self.eliminar_tarea())

    # ------------------------------------------------------------------
    # Persistencia de datos
    # ------------------------------------------------------------------
    def cargar_tareas(self) -> list[dict]:
        """Lee tareas.json. Si no existe, inicia con una lista vacía."""
        if not self.ARCHIVO_DATOS.exists():
            return []

        try:
            with self.ARCHIVO_DATOS.open("r", encoding="utf-8") as archivo:
                datos = json.load(archivo)

            if not isinstance(datos, list):
                raise ValueError("El contenido del archivo no es una lista.")

            tareas_validas = []
            for indice, tarea in enumerate(datos, start=1):
                if not isinstance(tarea, dict):
                    continue

                nombre = str(tarea.get("nombre", "")).strip()
                prioridad = tarea.get("prioridad")
                estado = tarea.get("estado", "Pendiente")
                if not nombre or prioridad not in self.PRIORIDADES:
                    continue
                if estado not in self.ESTADOS:
                    estado = "Pendiente"

                tareas_validas.append(
                    {
                        "id": str(tarea.get("id", indice)),
                        "nombre": nombre,
                        "descripcion": str(tarea.get("descripcion", "")),
                        "prioridad": prioridad,
                        "estado": estado,
                    }
                )
            return tareas_validas

        except (OSError, json.JSONDecodeError, ValueError) as error:
            messagebox.showwarning(
                "Aviso al cargar",
                "No se pudieron leer los datos guardados. La aplicación iniciará "
                f"con una lista vacía.\n\nDetalle: {error}",
            )
            return []

    def guardar_tareas(self) -> bool:
        """Guarda la lista actual en un archivo JSON junto al programa."""
        try:
            with self.ARCHIVO_DATOS.open("w", encoding="utf-8") as archivo:
                json.dump(self.tareas, archivo, ensure_ascii=False, indent=4)
            return True
        except OSError as error:
            messagebox.showerror(
                "Error al guardar",
                f"No fue posible guardar las tareas.\n\nDetalle: {error}",
            )
            return False

    def calcular_siguiente_id(self) -> int:
        """Obtiene un identificador nuevo sin repetir los existentes."""
        ids = []
        for tarea in self.tareas:
            try:
                ids.append(int(tarea["id"]))
            except (KeyError, TypeError, ValueError):
                continue
        return max(ids, default=0) + 1

    # ------------------------------------------------------------------
    # Estilos e interfaz gráfica
    # ------------------------------------------------------------------
    def configurar_estilos(self) -> None:
        estilo = ttk.Style(self.root)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass

        estilo.configure(
            "TFrame", background=self.COLORES["fondo"]
        )
        estilo.configure(
            "TLabel",
            background=self.COLORES["tarjeta"],
            foreground=self.COLORES["texto"],
            font=("Segoe UI", 10),
        )
        estilo.configure(
            "Titulo.TLabel",
            background=self.COLORES["fondo"],
            foreground=self.COLORES["texto"],
            font=("Segoe UI", 21, "bold"),
        )
        estilo.configure(
            "Subtitulo.TLabel",
            background=self.COLORES["fondo"],
            foreground=self.COLORES["secundario"],
            font=("Segoe UI", 9),
        )
        estilo.configure(
            "Campo.TLabel",
            background=self.COLORES["tarjeta"],
            foreground=self.COLORES["secundario"],
            font=("Segoe UI", 9, "bold"),
        )
        estilo.configure(
            "TEntry",
            padding=9,
            fieldbackground="#ffffff",
            foreground=self.COLORES["texto"],
            font=("Segoe UI", 10),
        )
        estilo.configure(
            "TCombobox",
            padding=8,
            fieldbackground="#ffffff",
            foreground=self.COLORES["texto"],
            font=("Segoe UI", 10),
        )
        estilo.map(
            "TCombobox",
            fieldbackground=[("readonly", "#ffffff")],
            foreground=[("readonly", self.COLORES["texto"])],
        )
        estilo.configure(
            "Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground=self.COLORES["texto"],
            rowheight=36,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        estilo.configure(
            "Treeview.Heading",
            background="#edf2f7",
            foreground="#435268",
            font=("Segoe UI", 9, "bold"),
            padding=(10, 10),
            relief="flat",
        )
        estilo.map(
            "Treeview",
            background=[("selected", "#d9f0f6")],
            foreground=[("selected", self.COLORES["texto"])],
        )
        estilo.configure(
            "Primario.TButton",
            background=self.COLORES["primario"],
            foreground="#ffffff",
            padding=(16, 9),
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
        )
        estilo.map(
            "Primario.TButton",
            background=[("active", self.COLORES["primario_hover"]), ("pressed", self.COLORES["primario_hover"])],
            foreground=[("disabled", "#e5e7eb")],
        )
        estilo.configure(
            "Secundario.TButton",
            background=self.COLORES["suave"],
            foreground=self.COLORES["texto"],
            padding=(13, 9),
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
        )
        estilo.map(
            "Secundario.TButton",
            background=[("active", "#dfe7f0"), ("pressed", "#dfe7f0")],
        )
        estilo.configure(
            "Peligro.TButton",
            background=self.COLORES["peligro"],
            foreground="#ffffff",
            padding=(13, 9),
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
        )
        estilo.map(
            "Peligro.TButton",
            background=[("active", self.COLORES["peligro_hover"]), ("pressed", self.COLORES["peligro_hover"])],
        )

    def crear_tarjeta(self, parent: tk.Widget, **kwargs) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=self.COLORES["tarjeta"],
            highlightthickness=1,
            highlightbackground=self.COLORES["borde"],
            bd=0,
            **kwargs,
        )

    def crear_interfaz(self) -> None:
        contenedor = tk.Frame(self.root, bg=self.COLORES["fondo"])
        contenedor.pack(fill="both", expand=True, padx=24, pady=18)

        # Encabezado
        encabezado = tk.Frame(contenedor, bg=self.COLORES["fondo"])
        encabezado.pack(fill="x", pady=(0, 16))

        titulo_area = tk.Frame(encabezado, bg=self.COLORES["fondo"])
        titulo_area.pack(side="left", fill="x", expand=True)
        ttk.Label(
            titulo_area,
            text="✓  Administrador de tareas",
            style="Titulo.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            titulo_area,
            text="Organiza tus actividades y lleva el control de lo que tienes pendiente.",
            style="Subtitulo.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        # Formulario
        tarjeta_formulario = self.crear_tarjeta(contenedor)
        tarjeta_formulario.pack(fill="x", pady=(0, 14))
        formulario = tk.Frame(tarjeta_formulario, bg=self.COLORES["tarjeta"])
        formulario.pack(fill="x", padx=20, pady=18)
        formulario.columnconfigure(0, weight=1)
        formulario.columnconfigure(1, weight=0)

        ttk.Label(formulario, text="Nombre de la tarea", style="Campo.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        ttk.Label(formulario, text="Prioridad", style="Campo.TLabel").grid(
            row=0, column=1, sticky="w", padx=(14, 0), pady=(0, 6)
        )

        self.entrada_nombre = ttk.Entry(formulario)
        self.entrada_nombre.grid(row=1, column=0, sticky="ew", ipady=3)
        self.entrada_nombre.insert(0, "Escribe el nombre de la tarea...")
        self.entrada_nombre.bind("<FocusIn>", self.quitar_indicacion_nombre)
        self.entrada_nombre.bind("<FocusOut>", self.restaurar_indicacion_nombre)

        self.combo_prioridad = ttk.Combobox(
            formulario,
            values=self.PRIORIDADES,
            state="readonly",
            width=16,
        )
        self.combo_prioridad.grid(row=1, column=1, sticky="ew", padx=(14, 0))
        self.combo_prioridad.set("")

        ttk.Label(formulario, text="Descripción de la actividad", style="Campo.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(14, 6)
        )
        self.campo_descripcion = tk.Text(
            formulario,
            height=3,
            wrap="word",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg=self.COLORES["texto"],
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=self.COLORES["borde"],
            highlightcolor=self.COLORES["primario"],
            padx=9,
            pady=7,
        )
        self.campo_descripcion.grid(row=3, column=0, columnspan=2, sticky="ew")

        botones_formulario = tk.Frame(formulario, bg=self.COLORES["tarjeta"])
        botones_formulario.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        ttk.Button(
            botones_formulario,
            text="＋  Agregar tarea",
            style="Primario.TButton",
            command=self.agregar_tarea,
        ).pack(side="left")
        ttk.Button(
            botones_formulario,
            text="✓  Completar",
            style="Secundario.TButton",
            command=self.completar_tarea,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            botones_formulario,
            text="Eliminar",
            style="Peligro.TButton",
            command=self.eliminar_tarea,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            botones_formulario,
            text="Limpiar",
            style="Secundario.TButton",
            command=self.limpiar_formulario,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            botones_formulario,
            text="Salir",
            style="Secundario.TButton",
            command=self.salir,
        ).pack(side="right")

        # Filtros y ordenamiento
        tarjeta_filtros = self.crear_tarjeta(contenedor)
        tarjeta_filtros.pack(fill="x", pady=(0, 14))
        filtros = tk.Frame(tarjeta_filtros, bg=self.COLORES["tarjeta"])
        filtros.pack(fill="x", padx=20, pady=15)

        ttk.Label(filtros, text="Estado:").pack(side="left", padx=(0, 8))
        self.combo_filtro = ttk.Combobox(
            filtros,
            textvariable=self.filtro_estado,
            values=("Todas", "Pendientes", "Completadas"),
            state="readonly",
            width=14,
        )
        self.combo_filtro.pack(side="left")
        self.combo_filtro.bind("<<ComboboxSelected>>", lambda _event: self.actualizar_vista())

        ttk.Label(filtros, text="Ordenar por:").pack(side="left", padx=(22, 8))
        self.combo_orden = ttk.Combobox(
            filtros,
            textvariable=self.orden,
            values=("Creación", "Prioridad", "Nombre"),
            state="readonly",
            width=14,
        )
        self.combo_orden.pack(side="left")
        self.combo_orden.bind("<<ComboboxSelected>>", lambda _event: self.actualizar_vista())

        self.etiqueta_resumen = ttk.Label(
            filtros,
            text="0 tareas  |  0 completadas",
            foreground=self.COLORES["secundario"],
        )
        self.etiqueta_resumen.pack(side="right")

        # Tabla de tareas
        tarjeta_lista = self.crear_tarjeta(contenedor)
        tarjeta_lista.pack(fill="both", expand=True)
        lista_interior = tk.Frame(tarjeta_lista, bg=self.COLORES["tarjeta"])
        lista_interior.pack(fill="both", expand=True, padx=18, pady=16)

        cabecera_lista = tk.Frame(lista_interior, bg=self.COLORES["tarjeta"])
        cabecera_lista.pack(fill="x", pady=(0, 10))
        tk.Label(
            cabecera_lista,
            text="Mis tareas",
            font=("Segoe UI", 13, "bold"),
            bg=self.COLORES["tarjeta"],
            fg=self.COLORES["texto"],
        ).pack(side="left")
        tk.Label(
            cabecera_lista,
            text="Selecciona una tarea para ver su descripción",
            font=("Segoe UI", 9),
            bg=self.COLORES["tarjeta"],
            fg=self.COLORES["secundario"],
        ).pack(side="right")

        marco_tabla = tk.Frame(lista_interior, bg=self.COLORES["tarjeta"])
        marco_tabla.pack(fill="both", expand=True)
        columnas = ("numero", "nombre", "prioridad", "estado")
        self.tabla = ttk.Treeview(
            marco_tabla,
            columns=columnas,
            show="headings",
            selectmode="browse",
        )
        self.tabla.heading("numero", text="Número")
        self.tabla.heading("nombre", text="Nombre de la tarea")
        self.tabla.heading("prioridad", text="Prioridad")
        self.tabla.heading("estado", text="Estado")
        self.tabla.column("numero", width=80, minwidth=65, anchor="center", stretch=False)
        self.tabla.column("nombre", width=520, minwidth=180, anchor="w")
        self.tabla.column("prioridad", width=140, minwidth=100, anchor="center", stretch=False)
        self.tabla.column("estado", width=150, minwidth=110, anchor="center", stretch=False)

        barra = ttk.Scrollbar(marco_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        self.tabla.tag_configure("Alta", foreground="#bd4545")
        self.tabla.tag_configure("Media", foreground="#b7791f")
        self.tabla.tag_configure("Baja", foreground="#21875a")
        self.tabla.tag_configure("Completada", foreground="#718096")
        self.tabla.bind("<<TreeviewSelect>>", self.mostrar_descripcion)

        self.etiqueta_vacia = tk.Label(
            lista_interior,
            text="",
            bg=self.COLORES["tarjeta"],
            fg=self.COLORES["secundario"],
            font=("Segoe UI", 10),
            pady=12,
        )
        self.etiqueta_vacia.pack(fill="x")

        tk.Label(
            lista_interior,
            text="Descripción de la tarea seleccionada",
            bg=self.COLORES["tarjeta"],
            fg=self.COLORES["secundario"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(12, 5))
        self.detalle_descripcion = tk.Text(
            lista_interior,
            height=2,
            wrap="word",
            font=("Segoe UI", 9),
            bg="#f8fafc",
            fg=self.COLORES["texto"],
            relief="flat",
            padx=8,
            pady=6,
            state="disabled",
        )
        self.detalle_descripcion.pack(fill="x")

        pie = tk.Label(
            contenedor,
            text="Los cambios se guardan automáticamente en el archivo tareas.json",
            bg=self.COLORES["fondo"],
            fg=self.COLORES["secundario"],
            font=("Segoe UI", 8),
        )
        pie.pack(anchor="e", pady=(8, 0))

        self.entrada_nombre.focus_set()

    # ------------------------------------------------------------------
    # Eventos del formulario
    # ------------------------------------------------------------------
    def quitar_indicacion_nombre(self, _event=None) -> None:
        if self.entrada_nombre.get() == "Escribe el nombre de la tarea...":
            self.entrada_nombre.delete(0, "end")
            self.entrada_nombre.configure(foreground=self.COLORES["texto"])

    def restaurar_indicacion_nombre(self, _event=None) -> None:
        if not self.entrada_nombre.get().strip():
            self.entrada_nombre.delete(0, "end")
            self.entrada_nombre.insert(0, "Escribe el nombre de la tarea...")
            self.entrada_nombre.configure(foreground="#9aa5b1")

    def agregar_tarea(self) -> None:
        nombre = self.entrada_nombre.get().strip()
        if nombre == "Escribe el nombre de la tarea...":
            nombre = ""
        prioridad = self.combo_prioridad.get().strip()
        descripcion = self.campo_descripcion.get("1.0", "end").strip()

        # Validación 1: el nombre es obligatorio.
        if not nombre:
            messagebox.showwarning(
                "Dato requerido",
                "Por favor, ingresa el nombre de la tarea.",
                parent=self.root,
            )
            self.entrada_nombre.focus_set()
            return

        # Validación 2: se debe elegir una prioridad válida.
        if prioridad not in self.PRIORIDADES:
            messagebox.showwarning(
                "Dato requerido",
                "Por favor, selecciona una prioridad: Alta, Media o Baja.",
                parent=self.root,
            )
            self.combo_prioridad.focus_set()
            return

        nueva_tarea = {
            "id": str(self.siguiente_id),
            "nombre": nombre,
            "descripcion": descripcion,
            "prioridad": prioridad,
            "estado": "Pendiente",
        }
        self.siguiente_id += 1
        self.tareas.append(nueva_tarea)
        self.guardar_tareas()
        self.limpiar_formulario()
        self.filtro_estado.set("Todas")
        self.actualizar_vista()
        self.tabla.selection_set(nueva_tarea["id"])
        self.tabla.focus(nueva_tarea["id"])
        self.tabla.see(nueva_tarea["id"])
        self.mostrar_descripcion()

    def obtener_tarea_seleccionada(self) -> dict | None:
        seleccion = self.tabla.selection()
        if not seleccion:
            if not self.tareas:
                messagebox.showinfo(
                    "Sin tareas",
                    "No existen tareas registradas.",
                    parent=self.root,
                )
            else:
                messagebox.showwarning(
                    "Selección requerida",
                    "Selecciona una tarea de la lista para continuar.",
                    parent=self.root,
                )
            return None

        identificador = seleccion[0]
        for tarea in self.tareas:
            if tarea["id"] == identificador:
                return tarea
        return None

    def completar_tarea(self) -> None:
        tarea = self.obtener_tarea_seleccionada()
        if tarea is None:
            return

        if tarea["estado"] == "Completada":
            messagebox.showinfo(
                "Tarea completada",
                "La tarea seleccionada ya está completada.",
                parent=self.root,
            )
            return

        tarea["estado"] = "Completada"
        self.guardar_tareas()
        self.actualizar_vista()
        if self.filtro_estado.get() == "Pendientes":
            self.filtro_estado.set("Todas")
            self.actualizar_vista()
        self.tabla.selection_set(tarea["id"])
        self.mostrar_descripcion()
        messagebox.showinfo(
            "Tarea actualizada",
            f'La tarea "{tarea["nombre"]}" se marcó como completada.',
            parent=self.root,
        )

    def eliminar_tarea(self) -> None:
        tarea = self.obtener_tarea_seleccionada()
        if tarea is None:
            return

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f'¿Estás seguro de que deseas eliminar la tarea "{tarea["nombre"]}"?',
            icon="warning",
            parent=self.root,
        )
        if not confirmar:
            return

        self.tareas = [item for item in self.tareas if item["id"] != tarea["id"]]
        self.guardar_tareas()
        self.limpiar_detalle()
        self.actualizar_vista()

    def limpiar_formulario(self) -> None:
        self.entrada_nombre.delete(0, "end")
        self.entrada_nombre.configure(foreground=self.COLORES["texto"])
        self.combo_prioridad.set("")
        self.campo_descripcion.delete("1.0", "end")
        self.entrada_nombre.focus_set()

    def salir(self) -> None:
        self.root.destroy()

    # ------------------------------------------------------------------
    # Tabla, filtros y descripción
    # ------------------------------------------------------------------
    def actualizar_vista(self) -> None:
        for elemento in self.tabla.get_children():
            self.tabla.delete(elemento)

        tareas_visibles = list(self.tareas)
        filtro = self.filtro_estado.get()
        if filtro == "Pendientes":
            tareas_visibles = [t for t in tareas_visibles if t["estado"] == "Pendiente"]
        elif filtro == "Completadas":
            tareas_visibles = [t for t in tareas_visibles if t["estado"] == "Completada"]

        criterio = self.orden.get()
        if criterio == "Prioridad":
            orden_prioridad = {"Alta": 0, "Media": 1, "Baja": 2}
            tareas_visibles.sort(key=lambda t: orden_prioridad.get(t["prioridad"], 3))
        elif criterio == "Nombre":
            tareas_visibles.sort(key=lambda t: t["nombre"].casefold())
        else:
            tareas_visibles.sort(key=lambda t: int(t["id"]) if t["id"].isdigit() else 0)

        for numero, tarea in enumerate(tareas_visibles, start=1):
            etiqueta = "Completada" if tarea["estado"] == "Completada" else tarea["prioridad"]
            self.tabla.insert(
                "",
                "end",
                iid=tarea["id"],
                values=(numero, tarea["nombre"], tarea["prioridad"], tarea["estado"]),
                tags=(etiqueta,),
            )

        total = len(self.tareas)
        completadas = sum(1 for tarea in self.tareas if tarea["estado"] == "Completada")
        pendientes = total - completadas
        self.etiqueta_resumen.configure(
            text=f"{total} tareas  |  {pendientes} pendientes  |  {completadas} completadas"
        )

        if total == 0:
            self.etiqueta_vacia.configure(
                text="No existen tareas registradas. Agrega una tarea usando el formulario superior."
            )
        elif not tareas_visibles:
            self.etiqueta_vacia.configure(
                text="No hay tareas que coincidan con el filtro seleccionado."
            )
        else:
            self.etiqueta_vacia.configure(text="")

    def mostrar_descripcion(self, _event=None) -> None:
        seleccion = self.tabla.selection()
        if not seleccion:
            self.limpiar_detalle()
            return

        identificador = seleccion[0]
        tarea = next((t for t in self.tareas if t["id"] == identificador), None)
        self.detalle_descripcion.configure(state="normal")
        self.detalle_descripcion.delete("1.0", "end")
        if tarea:
            texto = tarea["descripcion"].strip() or "Esta tarea no tiene una descripción."
            self.detalle_descripcion.insert("1.0", texto)
        self.detalle_descripcion.configure(state="disabled")

    def limpiar_detalle(self) -> None:
        self.detalle_descripcion.configure(state="normal")
        self.detalle_descripcion.delete("1.0", "end")
        self.detalle_descripcion.configure(state="disabled")


def main() -> None:
    ventana = tk.Tk()
    AdministradorTareas(ventana)
    ventana.mainloop()


if __name__ == "__main__":
    main()

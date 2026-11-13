"""Control de gastos personales del día, con interfaz gráfica (tkinter).

Estructura:
  - Funciones de lógica (validar, registrar, calcular, resumir), sin dependencia
    de la interfaz, para que sean fáciles de probar.
  - Clase AppGastos con la interfaz gráfica.
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox

MONEDA = "Q"
CATEGORIAS = ["Alimentación", "Transporte", "Educación", "Entretenimiento", "Otros"]
UMBRAL_ALERTA = 0.80  # aviso preventivo al llegar al 80 % del presupuesto


# ---------------------------------------------------------------------------
# Funciones de lógica
# ---------------------------------------------------------------------------
def validar_monto(texto, campo="El monto"):
    """Convierte el texto a número positivo. Lanza ValueError con mensaje claro."""
    texto = texto.strip().replace(",", ".")
    if not texto:
        raise ValueError(f"{campo} no puede estar vacío.")
    try:
        valor = float(texto)
    except ValueError:
        raise ValueError(f"{campo} debe ser un número válido (ejemplo: 25.50).")
    if math.isnan(valor) or math.isinf(valor):
        raise ValueError(f"{campo} debe ser un número válido.")
    if valor <= 0:
        raise ValueError(f"{campo} debe ser mayor que cero.")
    return round(valor, 2)


def validar_descripcion(texto):
    """Valida que la descripción no esté vacía."""
    texto = texto.strip()
    if not texto:
        raise ValueError("La descripción del gasto no puede estar vacía.")
    return texto


def validar_categoria(categoria):
    """Valida que la categoría pertenezca a la lista permitida."""
    if categoria not in CATEGORIAS:
        raise ValueError("Seleccione una categoría de la lista.")
    return categoria


def registrar_gasto(gastos, descripcion, categoria, monto_texto):
    """Valida los datos y agrega el gasto a la lista. Devuelve el gasto creado."""
    gasto = {
        "descripcion": validar_descripcion(descripcion),
        "categoria": validar_categoria(categoria),
        "monto": validar_monto(monto_texto),
    }
    gastos.append(gasto)
    return gasto


def calcular_total(gastos):
    """Suma de todos los gastos registrados."""
    return round(sum(g["monto"] for g in gastos), 2)


def calcular_disponible(presupuesto, gastos):
    """Dinero restante del presupuesto (negativo si se excedió)."""
    return round(presupuesto - calcular_total(gastos), 2)


def resumen_por_categoria(gastos):
    """Devuelve {categoria: total} incluyendo todas las categorías."""
    resumen = {cat: 0.0 for cat in CATEGORIAS}
    for g in gastos:
        resumen[g["categoria"]] += g["monto"]
    return {cat: round(total, 2) for cat, total in resumen.items()}


def estado_presupuesto(presupuesto, gastos):
    """Devuelve ('excedido' | 'alerta' | 'ok', mensaje)."""
    total = calcular_total(gastos)
    disponible = calcular_disponible(presupuesto, gastos)
    if total > presupuesto:
        return "excedido", (
            f"¡ADVERTENCIA! Los gastos superan el presupuesto por "
            f"{MONEDA} {abs(disponible):,.2f}."
        )
    if presupuesto > 0 and total >= presupuesto * UMBRAL_ALERTA:
        return "alerta", (
            f"Atención: ya usó el {total / presupuesto * 100:.0f}% del presupuesto."
        )
    return "ok", "Dentro del presupuesto."


def formato(valor):
    return f"{MONEDA} {valor:,.2f}"


# ---------------------------------------------------------------------------
# Interfaz gráfica
# ---------------------------------------------------------------------------
class AppGastos(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Control de Gastos Personales")
        self.geometry("760x680")
        self.minsize(700, 620)

        self.presupuesto = None
        self.gastos = []

        self._crear_widgets()
        self._actualizar_estado_formulario()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    # -- construcción de la interfaz ---------------------------------------
    def _crear_widgets(self):
        pad = {"padx": 10, "pady": 5}

        # 1. Presupuesto
        marco_p = ttk.LabelFrame(self, text="1. Presupuesto del día")
        marco_p.pack(fill="x", **pad)
        ttk.Label(marco_p, text=f"Presupuesto disponible ({MONEDA}):").grid(
            row=0, column=0, sticky="w", padx=8, pady=8)
        self.var_presupuesto = tk.StringVar()
        self.ent_presupuesto = ttk.Entry(marco_p, textvariable=self.var_presupuesto, width=15)
        self.ent_presupuesto.grid(row=0, column=1, padx=8, pady=8)
        self.ent_presupuesto.bind("<Return>", lambda e: self.establecer_presupuesto())
        self.btn_presupuesto = ttk.Button(
            marco_p, text="Establecer", command=self.establecer_presupuesto)
        self.btn_presupuesto.grid(row=0, column=2, padx=8, pady=8)
        self.lbl_presupuesto = ttk.Label(marco_p, text="Sin presupuesto definido",
                                         font=("TkDefaultFont", 10, "bold"))
        self.lbl_presupuesto.grid(row=0, column=3, padx=12, pady=8, sticky="w")

        # 2. Registro de gasto
        marco_g = ttk.LabelFrame(self, text="2. Registrar gasto")
        marco_g.pack(fill="x", **pad)
        ttk.Label(marco_g, text="Descripción:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.var_desc = tk.StringVar()
        self.ent_desc = ttk.Entry(marco_g, textvariable=self.var_desc, width=30)
        self.ent_desc.grid(row=0, column=1, padx=8, pady=6)

        ttk.Label(marco_g, text="Categoría:").grid(row=0, column=2, sticky="w", padx=8, pady=6)
        self.var_cat = tk.StringVar()
        self.cmb_cat = ttk.Combobox(marco_g, textvariable=self.var_cat, values=CATEGORIAS,
                                    state="readonly", width=18)
        self.cmb_cat.grid(row=0, column=3, padx=8, pady=6)

        ttk.Label(marco_g, text=f"Monto ({MONEDA}):").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.var_monto = tk.StringVar()
        self.ent_monto = ttk.Entry(marco_g, textvariable=self.var_monto, width=15)
        self.ent_monto.grid(row=1, column=1, sticky="w", padx=8, pady=6)
        self.ent_monto.bind("<Return>", lambda e: self.agregar_gasto())

        self.btn_agregar = ttk.Button(marco_g, text="Agregar gasto", command=self.agregar_gasto)
        self.btn_agregar.grid(row=1, column=3, sticky="e", padx=8, pady=6)

        # 3. Lista de gastos
        marco_l = ttk.LabelFrame(self, text="3. Gastos registrados")
        marco_l.pack(fill="both", expand=True, **pad)
        columnas = ("descripcion", "categoria", "monto")
        self.tabla = ttk.Treeview(marco_l, columns=columnas, show="headings", height=7)
        self.tabla.heading("descripcion", text="Descripción")
        self.tabla.heading("categoria", text="Categoría")
        self.tabla.heading("monto", text="Monto")
        self.tabla.column("descripcion", width=280)
        self.tabla.column("categoria", width=150)
        self.tabla.column("monto", width=110, anchor="e")
        barra = ttk.Scrollbar(marco_l, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        self.tabla.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        barra.pack(side="left", fill="y", pady=8, padx=(0, 8))
        botones = ttk.Frame(marco_l)
        botones.pack(side="left", fill="y", padx=8, pady=8)
        ttk.Button(botones, text="Eliminar\nseleccionado",
                   command=self.eliminar_gasto).pack(fill="x", pady=2)
        ttk.Button(botones, text="Reiniciar día",
                   command=self.reiniciar).pack(fill="x", pady=2)

        # 4. Totales y estado
        marco_t = ttk.LabelFrame(self, text="4. Totales")
        marco_t.pack(fill="x", **pad)
        ttk.Label(marco_t, text="Total de gastos:").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.lbl_total = ttk.Label(marco_t, text=formato(0), font=("TkDefaultFont", 11, "bold"))
        self.lbl_total.grid(row=0, column=1, sticky="w", padx=8)
        ttk.Label(marco_t, text="Dinero disponible:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.lbl_disponible = ttk.Label(marco_t, text=formato(0), font=("TkDefaultFont", 11, "bold"))
        self.lbl_disponible.grid(row=1, column=1, sticky="w", padx=8)
        self.lbl_estado = tk.Label(marco_t, text="", font=("TkDefaultFont", 10, "bold"),
                                   anchor="w", justify="left")
        self.lbl_estado.grid(row=2, column=0, columnspan=4, sticky="we", padx=8, pady=(4, 8))

        # 5. Resumen por categoría
        marco_r = ttk.LabelFrame(self, text="5. Resumen por categoría")
        marco_r.pack(fill="x", **pad)
        self.tabla_resumen = ttk.Treeview(
            marco_r, columns=("categoria", "total", "porcentaje"), show="headings", height=5)
        self.tabla_resumen.heading("categoria", text="Categoría")
        self.tabla_resumen.heading("total", text="Total gastado")
        self.tabla_resumen.heading("porcentaje", text="% de los gastos")
        self.tabla_resumen.column("categoria", width=200)
        self.tabla_resumen.column("total", width=150, anchor="e")
        self.tabla_resumen.column("porcentaje", width=130, anchor="e")
        self.tabla_resumen.pack(fill="x", padx=8, pady=8)

        self._refrescar()

    # -- acciones -------------------------------------------------------------
    def establecer_presupuesto(self):
        try:
            valor = validar_monto(self.var_presupuesto.get(), "El presupuesto")
        except ValueError as err:
            messagebox.showerror("Presupuesto no válido", str(err))
            return
        self.presupuesto = valor
        self.lbl_presupuesto.config(text=f"Presupuesto: {formato(valor)}")
        self._actualizar_estado_formulario()
        self._refrescar()
        self.ent_desc.focus_set()

    def agregar_gasto(self):
        if self.presupuesto is None:
            messagebox.showerror("Falta presupuesto",
                                 "Primero debe establecer el presupuesto disponible.")
            return
        estado_antes = estado_presupuesto(self.presupuesto, self.gastos)[0]
        try:
            registrar_gasto(self.gastos, self.var_desc.get(), self.var_cat.get(),
                            self.var_monto.get())
        except ValueError as err:
            messagebox.showerror("Datos no válidos", str(err))
            return

        self.var_desc.set("")
        self.var_monto.set("")
        self.cmb_cat.set("")
        self._refrescar()
        self.ent_desc.focus_set()

        estado, mensaje = estado_presupuesto(self.presupuesto, self.gastos)
        # Se avisa en ventana al cruzar de nivel o mientras siga excedido.
        if estado == "excedido":
            messagebox.showwarning("Presupuesto excedido", mensaje)
        elif estado == "alerta" and estado_antes == "ok":
            messagebox.showinfo("Cerca del límite", mensaje)

    def eliminar_gasto(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showinfo("Eliminar gasto", "Seleccione un gasto de la lista.")
            return
        # Se eliminan de mayor a menor índice para no desfasar posiciones.
        indices = sorted((self.tabla.index(i) for i in seleccion), reverse=True)
        for i in indices:
            del self.gastos[i]
        self._refrescar()

    def reiniciar(self):
        if not self.gastos and self.presupuesto is None:
            return
        if messagebox.askyesno("Reiniciar", "¿Borrar presupuesto y todos los gastos?"):
            self.gastos.clear()
            self.presupuesto = None
            self.var_presupuesto.set("")
            self.lbl_presupuesto.config(text="Sin presupuesto definido")
            self._actualizar_estado_formulario()
            self._refrescar()

    # -- actualización de la pantalla ------------------------------------------
    def _actualizar_estado_formulario(self):
        """Los campos de gasto solo se habilitan cuando ya hay presupuesto."""
        estado = "normal" if self.presupuesto is not None else "disabled"
        self.ent_desc.config(state=estado)
        self.ent_monto.config(state=estado)
        self.btn_agregar.config(state=estado)
        self.cmb_cat.config(state="readonly" if estado == "normal" else "disabled")

    def _refrescar(self):
        # Lista de gastos
        self.tabla.delete(*self.tabla.get_children())
        for g in self.gastos:
            self.tabla.insert("", "end",
                              values=(g["descripcion"], g["categoria"], formato(g["monto"])))

        # Totales
        total = calcular_total(self.gastos)
        self.lbl_total.config(text=formato(total))

        if self.presupuesto is None:
            self.lbl_disponible.config(text="—")
            self.lbl_estado.config(text="Defina el presupuesto para comenzar.",
                                   fg="gray40")
        else:
            disponible = calcular_disponible(self.presupuesto, self.gastos)
            estado, mensaje = estado_presupuesto(self.presupuesto, self.gastos)
            color = {"ok": "#1b7f3b", "alerta": "#b36b00", "excedido": "#c62828"}[estado]
            self.lbl_disponible.config(text=formato(disponible))
            self.lbl_estado.config(text=mensaje, fg=color)

        # Resumen por categoría
        self.tabla_resumen.delete(*self.tabla_resumen.get_children())
        resumen = resumen_por_categoria(self.gastos)
        for cat, subtotal in resumen.items():
            pct = (subtotal / total * 100) if total > 0 else 0
            self.tabla_resumen.insert("", "end",
                                      values=(cat, formato(subtotal), f"{pct:.1f}%"))


def main():
    app = AppGastos()
    app.mainloop()


if __name__ == "__main__":
    main()
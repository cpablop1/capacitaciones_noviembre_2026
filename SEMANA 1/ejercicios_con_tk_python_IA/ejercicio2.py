"""Juego de adivinanza de números con interfaz gráfica (tkinter).

La computadora elige un número secreto entre 1 y 100 y el jugador tiene
7 intentos para descubrirlo, recibiendo pistas de "mayor" o "menor".

Estructura:
  - Funciones de lógica (validar_numero y partida), sin dependencia de tkinter.
  - Clase AppAdivinanza con la interfaz gráfica.
"""

import random
import tkinter as tk
from tkinter import ttk, messagebox

NUM_MIN = 1
NUM_MAX = 100
MAX_INTENTOS = 7


# ---------------------------------------------------------------------------
# Lógica del juego
# ---------------------------------------------------------------------------
def validar_numero(texto):
    """Convierte el texto en un entero entre NUM_MIN y NUM_MAX.

    Lanza ValueError con un mensaje claro si el dato no es válido.
    """
    texto = texto.strip()
    if not texto:
        raise ValueError("Escriba un número antes de presionar Adivinar.")
    try:
        numero = int(texto)
    except ValueError:
        raise ValueError("Debe ingresar un número entero (sin letras ni decimales).")
    if not NUM_MIN <= numero <= NUM_MAX:
        raise ValueError(f"El número debe estar entre {NUM_MIN} y {NUM_MAX}.")
    return numero


def partida(secreto):
    """Generador que controla una partida con un ciclo while.

    Cómo se usa:
        juego = partida(secreto)
        next(juego)               # prepara el generador
        estado = juego.send(50)   # envía un intento y recibe el resultado

    El ciclo while se repite mientras queden intentos y el número no haya sido
    adivinado. Cada send() equivale a una vuelta del ciclo; así el límite de 7
    intentos lo controla el while y la ventana puede seguir respondiendo
    entre un intento y otro.

    Cada resultado es un diccionario con:
        intentos   -> intentos usados hasta ahora
        restantes  -> intentos que aún quedan
        pista      -> "mayor", "menor" o "acierto"
        numero     -> el número que se acaba de probar
        fin        -> True si la partida terminó
        gano       -> True si el jugador adivinó
    """
    intentos = 0
    adivinado = False
    numero = yield  # espera el primer intento

    while intentos < MAX_INTENTOS and not adivinado:
        intentos += 1
        if numero == secreto:
            adivinado = True
            pista = "acierto"
        elif numero < secreto:
            pista = "mayor"   # el secreto es MAYOR que el número probado
        else:
            pista = "menor"   # el secreto es MENOR que el número probado

        resultado = {
            "intentos": intentos,
            "restantes": MAX_INTENTOS - intentos,
            "pista": pista,
            "numero": numero,
            "fin": adivinado or intentos >= MAX_INTENTOS,
            "gano": adivinado,
        }
        numero = yield resultado


# ---------------------------------------------------------------------------
# Interfaz gráfica
# ---------------------------------------------------------------------------
class AppAdivinanza(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Adivina el número")
        self.geometry("480x560")
        self.resizable(False, False)

        self.secreto = None
        self.juego = None
        self.minimo = NUM_MIN   # límites del rango que va quedando posible
        self.maximo = NUM_MAX

        self._crear_widgets()
        self.nuevo_juego()

    def _crear_widgets(self):
        ttk.Label(self, text="🎯 Adivina el número",
                  font=("TkDefaultFont", 18, "bold")).pack(pady=(18, 4))
        ttk.Label(
            self,
            text=(f"Pensé un número entre {NUM_MIN} y {NUM_MAX}.\n"
                  f"Tienes {MAX_INTENTOS} intentos para descubrirlo."),
            justify="center",
        ).pack(pady=(0, 12))

        # Entrada del número
        marco = ttk.Frame(self)
        marco.pack(pady=6)
        ttk.Label(marco, text="Tu número:").grid(row=0, column=0, padx=6)
        self.var_numero = tk.StringVar()
        self.entrada = ttk.Entry(marco, textvariable=self.var_numero, width=10,
                                 justify="center", font=("TkDefaultFont", 14))
        self.entrada.grid(row=0, column=1, padx=6)
        self.entrada.bind("<Return>", lambda e: self.adivinar())
        self.btn_adivinar = ttk.Button(marco, text="Adivinar", command=self.adivinar)
        self.btn_adivinar.grid(row=0, column=2, padx=6)

        # Intentos
        self.lbl_intentos = ttk.Label(self, font=("TkDefaultFont", 11, "bold"))
        self.lbl_intentos.pack(pady=(14, 2))
        self.barra = ttk.Progressbar(self, maximum=MAX_INTENTOS, length=300)
        self.barra.pack(pady=(0, 8))

        # Pista
        self.lbl_pista = tk.Label(self, text="", font=("TkDefaultFont", 13, "bold"),
                                  wraplength=420, justify="center", height=2)
        self.lbl_pista.pack(pady=4)
        self.lbl_rango = ttk.Label(self, text="")
        self.lbl_rango.pack()

        # Historial
        marco_h = ttk.LabelFrame(self, text="Intentos realizados")
        marco_h.pack(fill="both", expand=True, padx=20, pady=12)
        self.lista = tk.Listbox(marco_h, height=7, activestyle="none",
                                font=("TkDefaultFont", 10))
        self.lista.pack(fill="both", expand=True, padx=8, pady=8)

        ttk.Button(self, text="Salir", command=self.destroy).pack(pady=(0, 14))

    # -- control del juego ------------------------------------------------
    def nuevo_juego(self):
        self.secreto = random.randint(NUM_MIN, NUM_MAX)
        self.juego = partida(self.secreto)
        next(self.juego)  # deja el generador listo para recibir intentos
        self.minimo, self.maximo = NUM_MIN, NUM_MAX

        self.var_numero.set("")
        self.lista.delete(0, "end")
        self.lbl_pista.config(text="¡Comienza el juego! Escribe tu primer número.",
                              fg="gray30")
        self._actualizar_contadores(0)
        self.entrada.config(state="normal")
        self.btn_adivinar.config(state="normal")
        self.entrada.focus_set()

    def _actualizar_contadores(self, usados):
        self.lbl_intentos.config(
            text=f"Intentos utilizados: {usados} de {MAX_INTENTOS}")
        self.barra["value"] = usados
        self.lbl_rango.config(
            text=f"El número está entre {self.minimo} y {self.maximo}")

    def adivinar(self):
        try:
            numero = validar_numero(self.var_numero.get())
        except ValueError as err:
            # Un dato inválido NO consume un intento.
            messagebox.showerror("Dato no válido", str(err))
            self.var_numero.set("")
            self.entrada.focus_set()
            return

        estado = self.juego.send(numero)

        if estado["pista"] == "mayor":
            self.minimo = max(self.minimo, numero + 1)
            texto = f"⬆ El número secreto es MAYOR que {numero}"
            color = "#1565c0"
            nota = "es mayor"
        elif estado["pista"] == "menor":
            self.maximo = min(self.maximo, numero - 1)
            texto = f"⬇ El número secreto es MENOR que {numero}"
            color = "#c62828"
            nota = "es menor"
        else:
            texto = f"¡Correcto! El número era {numero}"
            color = "#1b7f3b"
            nota = "¡acertaste!"

        self.lista.insert("end", f"Intento {estado['intentos']}:  {numero}  →  {nota}")
        self.lbl_pista.config(text=texto, fg=color)
        self._actualizar_contadores(estado["intentos"])
        self.var_numero.set("")
        self.entrada.focus_set()

        if estado["fin"]:
            self._terminar(estado)

    def _terminar(self, estado):
        self.entrada.config(state="disabled")
        self.btn_adivinar.config(state="disabled")

        if estado["gano"]:
            usados = estado["intentos"]
            palabra = "intento" if usados == 1 else "intentos"
            mensaje = (f"🎉 ¡Felicidades! Adivinaste el número {self.secreto} "
                       f"en {usados} {palabra}.")
            titulo = "¡Ganaste!"
        else:
            mensaje = (f"😢 Se agotaron los {MAX_INTENTOS} intentos.\n"
                       f"El número secreto era {self.secreto}.")
            titulo = "Fin del juego"
            self.lbl_pista.config(text=f"El número secreto era {self.secreto}",
                                  fg="#c62828")

        if messagebox.askyesno(titulo, f"{mensaje}\n\n¿Desea jugar nuevamente?"):
            self.nuevo_juego()
        else:
            self.destroy()


def main():
    app = AppAdivinanza()
    app.mainloop()


if __name__ == "__main__":
    main()
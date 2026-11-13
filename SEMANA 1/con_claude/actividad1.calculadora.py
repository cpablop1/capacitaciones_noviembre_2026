"""Actividad 1. Calculadora básica con validaciones."""


def pedir_numero(mensaje):
    """Pide un número por teclado y repite hasta que sea válido."""
    while True:
        texto = input(mensaje).strip().replace(",", ".")
        try:
            return float(texto)
        except ValueError:
            print("Error: debe ingresar un número válido (ejemplo: 5 o 3.14).")


def pedir_operacion():
    """Muestra el menú y repite hasta que la opción sea válida."""
    print("\nOperaciones disponibles:")
    print("  1. Suma")
    print("  2. Resta")
    print("  3. Multiplicación")
    print("  4. División")
    while True:
        opcion = input("Seleccione una operación (1-4): ").strip()
        if opcion in ("1", "2", "3", "4"):
            return opcion
        print("Error: opción no válida. Escriba un número del 1 al 4.")


def main():
    print("=== CALCULADORA BÁSICA ===")
    num1 = pedir_numero("Ingrese el primer número: ")
    num2 = pedir_numero("Ingrese el segundo número: ")
    opcion = pedir_operacion()

    if opcion == "1":
        resultado = num1 + num2
        simbolo = "+"
    elif opcion == "2":
        resultado = num1 - num2
        simbolo = "-"
    elif opcion == "3":
        resultado = num1 * num2
        simbolo = "*"
    else:
        simbolo = "/"
        if num2 == 0:
            print("\nError: no se puede dividir entre cero.")
            return
        resultado = num1 / num2

    print(f"\nResultado: {num1} {simbolo} {num2} = {resultado}")


if __name__ == "__main__":
    main()
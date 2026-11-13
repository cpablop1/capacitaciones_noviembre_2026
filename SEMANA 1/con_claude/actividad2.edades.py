"""Actividad 2. Clasificación de edades con validaciones."""


def pedir_edad():
    """Pide la edad y repite hasta que sea un entero no negativo."""
    while True:
        texto = input("Ingrese la edad de la persona: ").strip()
        try:
            edad = int(texto)
        except ValueError:
            print("Error: debe ingresar un número entero (ejemplo: 25).")
            continue
        if edad < 0:
            print("Error: la edad no puede ser negativa.")
            continue
        return edad


def clasificar(edad):
    if edad <= 10:
        return "Niño"
    elif edad <= 16:
        return "Adolescente"
    elif edad <= 30:
        return "Joven"
    else:
        return "Adulto"


def main():
    print("=== CLASIFICACIÓN DE EDADES ===")
    edad = pedir_edad()
    print(f"\nLa persona de {edad} años es: {clasificar(edad)}")


if __name__ == "__main__":
    main()
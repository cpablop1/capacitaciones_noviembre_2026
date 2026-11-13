
# Variables iniciales
contador = 0
acumulador = 0

print("=== SISTEMA DE CALIFICACIONES ===")

# Ciclo para ingresar las notas de 5 estudiantes
for i in range(5):

    print("\nEstudiante", i + 1)

    # Validar que la nota sea numerica y este entre 0 y 100
    while True:
        try:
            nota = float(input("Ingrese la calificacion (0-100): "))

            if nota >= 0 and nota <= 100:
                break
            else:
                print("Error: La calificacion debe estar entre 0 y 100.")

        except ValueError:
            print("Error: Debe ingresar un valor numerico.")

    # Acumular las calificaciones
    acumulador += nota
    contador += 1

    # Determinar si aprobo o reprobo
    if nota >= 60:
        print("Resultado: APROBADO")
    else:
        print("Resultado: REPROBADO")

# Calcular promedio general
promedio = acumulador / contador

# Mostrar resultados finales
print("\n=== RESULTADOS GENERALES ===")
print("Cantidad de estudiantes:", contador)
print("Suma de calificaciones:", acumulador)
print("Promedio general:", round(promedio, 2))

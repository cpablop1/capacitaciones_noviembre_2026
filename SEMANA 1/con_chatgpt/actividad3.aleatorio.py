
import random

# Variables iniciales
contador = 0
acumulador = 0

print("=== GENERADOR DE NUMEROS ALEATORIOS ===")

# Ciclo para generar 10 numeros
for i in range(10):

    numero = random.randint(1, 25)

    contador += 1
    acumulador += numero

    print("Numero", contador, ":", numero)

# Calcular promedio
promedio = acumulador / contador

# Mostrar resultados
print("\n=== RESULTADOS ===")
print("Cantidad de numeros generados:", contador)
print("Suma de los numeros:", acumulador)
print("Promedio:", round(promedio, 2))

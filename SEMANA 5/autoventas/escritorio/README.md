# AutoVentas — versión de escritorio (Python + tkinter)

Sistema de gestión y venta de autos con cuatro pestañas: **Inventario · Clientes · Ventas · Resumen**.
Solo usa la biblioteca estándar de Python 3.

## Ejecutar

```bash
python main.py
```

Los datos se guardan automáticamente en `datos/autoventas.json` tras cada operación.

## Pruebas

```bash
python -m unittest discover -s pruebas -t . -v
```

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `validaciones.py` | Validación y conversión de cada campo (RNF-02). Sin tkinter. |
| `logica.py` | Reglas de negocio: autos, clientes, ventas, filtros y resumen (RF-01 a RF-06). Sin tkinter ni archivos. |
| `persistencia.py` | Lectura/escritura atómica del JSON (RNF-03). |
| `interfaz.py` | Ventana con `ttk.Notebook` y las 4 pestañas (RNF-01). Solo llama a `logica.py`. |
| `main.py` | Une las capas: carga el JSON, crea el servicio y abre la ventana. |
| `pruebas/` | Pruebas unitarias, incluidos los casos CP-01 a CP-06. |

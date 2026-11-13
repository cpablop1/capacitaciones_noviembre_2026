# AutoVentas — versión web (HTML5 + CSS3 + JavaScript)

Misma aplicación que la versión de escritorio, organizada en cuatro secciones:
**Inventario · Clientes · Ventas · Resumen**. Sin librerías externas ni servidor.

## Ejecutar

Abrir `index.html` en el navegador (Chrome, Edge o Firefox actuales). Funciona sin conexión.
Los datos se guardan en el `localStorage` del navegador, con el mismo formato JSON que la
versión de escritorio.

## Pruebas

Requiere Node.js 18 o superior. Desde esta carpeta:

```bash
node --test
```

## Estructura

| Archivo | Responsabilidad | Equivalente en escritorio |
|---|---|---|
| `js/validaciones.js` | Validación y conversión de cada campo (RNF-02). Sin DOM. | `validaciones.py` |
| `js/logica.js` | Reglas de negocio: autos, clientes, ventas, búsqueda y resumen. Sin DOM. | `logica.py` |
| `js/persistencia.js` | Lectura/escritura en `localStorage`; respaldo si los datos están dañados (RNF-03). | `persistencia.py` |
| `js/interfaz.js` | Las 4 secciones, formularios, buscadores y diálogos. Solo llama a `logica.js`. | `interfaz.py` |
| `js/main.js` | Une las capas y sincroniza si la app está abierta en dos pestañas. | `main.py` |
| `index.html`, `css/estilos.css` | Estructura accesible y diseño responsive (RNF-05). | — |
| `pruebas/autoventas.test.js` | Las mismas 37 pruebas de escritorio, incluidos CP-01 a CP-06. | `pruebas/test_autoventas.py` |

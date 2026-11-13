/**
 * Punto de entrada de AutoVentas (versión web). Une las capas, igual que main.py:
 * carga los datos de localStorage, crea el servicio y arranca la interfaz.
 */
(function (raiz) {
  "use strict";

  const { persistencia, logica, interfaz } = raiz.AV;
  const { datos, aviso, almacen } = persistencia.cargar();
  const servicio = new logica.AutoVentas(datos, (d) => persistencia.guardar(d, almacen));
  const app = new interfaz.Aplicacion(servicio, { aviso });

  // Si la aplicación está abierta en dos pestañas, la que no hizo el cambio se
  // actualiza sola para no sobrescribir los datos con una copia vieja.
  raiz.addEventListener("storage", (evento) => {
    if (evento.key !== persistencia.CLAVE || evento.newValue === null) return;
    try {
      servicio.reemplazarDatos(persistencia.interpretar(evento.newValue));
      app.notificarCambio();
      app.aviso("Los datos se actualizaron desde otra pestaña.");
    } catch (error) {
      console.error("No se pudieron leer los datos de otra pestaña:", error);
    }
  });

  raiz.AV.app = app; // acceso para depuración y pruebas automatizadas
})(window);

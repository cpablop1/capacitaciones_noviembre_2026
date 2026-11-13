// Genera la documentación Word de AutoVentas (fase 1: versión de escritorio).
// Uso: node generar.js <carpeta_documentacion>
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Header, Footer,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber,
  PageBreak, TableOfContents, VerticalAlign,
} = require("docx");

const CARPETA = process.argv[2];
const CAPTURAS = path.join(CARPETA, "capturas_escritorio");
const CAPTURAS_WEB = path.join(CARPETA, "capturas_web");
const SALIDA = path.join(CARPETA, "AutoVentas_Documentacion.docx");

const FUENTE = "Calibri";
const AZUL = "1F3A5F";
const AZUL_CLARO = "E8EEF6";
const GRIS = "5B6573";
const ANCHO = 9360; // 8.5" − 2 × 1" de margen, en DXA

// ---------- utilidades ----------
function runs(texto, extra = {}) {
  // **negrita** dentro del texto
  return texto.split("**").map((parte, i) =>
    new TextRun({ text: parte, bold: i % 2 === 1 || extra.bold, italics: extra.italics,
                  color: extra.color, size: extra.size, font: extra.font }));
}
const p = (texto, opciones = {}) => new Paragraph({
  children: runs(texto, opciones), alignment: opciones.align, keepNext: opciones.keepNext,
  spacing: { after: opciones.after ?? 120, before: opciones.before ?? 0 } });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const h3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });
const vineta = (t, nivel = 0) => new Paragraph({ numbering: { reference: "vinetas", level: nivel },
  children: runs(t), spacing: { after: 60 } });
const numero = (t, ref = "numeros") => new Paragraph({ numbering: { reference: ref, level: 0 },
  children: runs(t), spacing: { after: 60 } });
const salto = () => new Paragraph({ children: [new PageBreak()] });
const codigo = (t) => new Paragraph({
  children: [new TextRun({ text: t, font: "Consolas", size: 19 })],
  shading: { type: ShadingType.CLEAR, fill: "F3F5F8", color: "auto" },
  spacing: { after: 0 }, indent: { left: 200 } });

const borde = { style: BorderStyle.SINGLE, size: 4, color: "C5CDD8" };
const bordes = { top: borde, bottom: borde, left: borde, right: borde };

function celda(texto, ancho, { encabezado = false, fondo, negrita = false } = {}) {
  const parrafos = String(texto).split("\n").map((linea) => new Paragraph({
    children: runs(linea, { bold: encabezado || negrita, color: encabezado ? "FFFFFF" : undefined,
                           size: 20 }),
    spacing: { after: 40 } }));
  return new TableCell({
    borders: bordes, width: { size: ancho, type: WidthType.DXA }, children: parrafos,
    verticalAlign: VerticalAlign.CENTER,
    shading: encabezado ? { fill: AZUL, type: ShadingType.CLEAR, color: "auto" }
      : fondo ? { fill: fondo, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 70, bottom: 70, left: 110, right: 110 } });
}

function tabla(encabezados, filas, proporciones, { primeraNegrita = false } = {}) {
  const total = proporciones.reduce((a, b) => a + b, 0);
  const anchos = proporciones.map((x) => Math.floor((x / total) * ANCHO));
  anchos[anchos.length - 1] += ANCHO - anchos.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: ANCHO, type: WidthType.DXA }, columnWidths: anchos,
    rows: [
      new TableRow({ tableHeader: true,
        children: encabezados.map((e, i) => celda(e, anchos[i], { encabezado: true })) }),
      ...filas.map((fila, f) => new TableRow({ cantSplit: true,
        children: fila.map((valor, i) => celda(valor, anchos[i], {
          fondo: f % 2 ? "F6F8FB" : undefined, negrita: primeraNegrita && i === 0 })) })),
    ] });
}
const espacio = () => new Paragraph({ children: [], spacing: { after: 120 } });

/** Lee la imagen y calcula su tamaño en el documento respetando la proporción real del PNG. */
function cargarImagen(archivo, carpeta, anchoMax, altoMax) {
  const datos = fs.readFileSync(path.join(carpeta, archivo));
  const anchoReal = datos.readUInt32BE(16), altoReal = datos.readUInt32BE(20);
  const escala = Math.min(anchoMax / anchoReal, altoMax / altoReal);
  return { datos, ancho: Math.round(anchoReal * escala), alto: Math.round(altoReal * escala) };
}

function imagen(archivo, leyenda, { carpeta = CAPTURAS, anchoMax = 600, altoMax = 640 } = {}) {
  const img = cargarImagen(archivo, carpeta, anchoMax, altoMax);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 }, keepNext: true,
      children: [new ImageRun({ type: "png", data: img.datos,
        transformation: { width: img.ancho, height: img.alto },
        altText: { title: leyenda, description: leyenda, name: archivo } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
      children: [new TextRun({ text: leyenda, italics: true, color: GRIS, size: 19 })] }),
  ];
}

/** Varias capturas en una fila (para las vistas de teléfono), cada una con su leyenda. */
function imagenesEnFila(elementos, leyendaGeneral, { carpeta = CAPTURAS_WEB } = {}) {
  const anchoCelda = Math.floor(ANCHO / elementos.length);
  const sinBorde = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const celdas = elementos.map(({ archivo, leyenda }) => {
    const img = cargarImagen(archivo, carpeta, 190, 420);
    return new TableCell({
      width: { size: anchoCelda, type: WidthType.DXA },
      borders: { top: sinBorde, bottom: sinBorde, left: sinBorde, right: sinBorde },
      children: [
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ type: "png", data: img.datos,
          transformation: { width: img.ancho, height: img.alto },
          altText: { title: leyenda, description: leyenda, name: archivo } })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60 },
          children: [new TextRun({ text: leyenda, italics: true, color: GRIS, size: 18 })] }),
      ] });
  });
  return [
    new Table({ width: { size: ANCHO, type: WidthType.DXA }, columnWidths: elementos.map(() => anchoCelda),
      rows: [new TableRow({ cantSplit: true, children: celdas })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 240 },
      children: [new TextRun({ text: leyendaGeneral, italics: true, color: GRIS, size: 19 })] }),
  ];
}

function prompt(numeroPrompt, titulo, fase, inicial, mejorado, aprendizaje) {
  return [
    h3(`Prompt ${numeroPrompt}. ${titulo}`),
    p(`**Fase:** ${fase}`, { keepNext: true }),
    tabla(["Versión inicial", "Versión mejorada"], [[inicial, mejorado]], [1, 1.6]),
    p(`**Qué cambió y por qué:** ${aprendizaje}`, { before: 100, after: 200 }),
  ];
}

// ---------- contenido ----------
const portada = [
  new Paragraph({ spacing: { before: 2600, after: 0 }, alignment: AlignmentType.LEFT,
    children: [new TextRun({ text: "PROYECTO FINAL", color: GRIS, bold: true, size: 26 })] }),
  new Paragraph({ spacing: { after: 120 },
    children: [new TextRun({ text: "AutoVentas", bold: true, size: 72, color: AZUL })] }),
  new Paragraph({ spacing: { after: 480 },
    children: [new TextRun({ text: "Sistema de gestión y venta de automóviles", size: 34, color: AZUL })] }),
  new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: AZUL, space: 4 } },
    spacing: { after: 360 }, children: [] }),
  p("**Documento:** Documentación del proceso de desarrollo con IA como asistente"),
  p("**Versión del documento:** 2.1 — Versión final: fase 1 (escritorio) y fase 2 (web)"),
  p("**Tecnologías:** Python 3 + tkinter (escritorio) · HTML5, CSS3 y JavaScript (web, fase 2)"),
  p("**Fecha:** 13 de noviembre de 2026"),
  p("**Estado:** proyecto terminado. Las dos versiones fueron probadas y validadas por el responsable."),
  salto(),
];

const indice = [
  new Paragraph({ children: [new TextRun({ text: "Contenido", bold: true, size: 32, color: AZUL })],
    spacing: { after: 200 } }),
  new TableOfContents("Contenido", { hyperlink: true, headingStyleRange: "1-2" }),
  salto(),
];

const introduccion = [
  h1("1. Descripción general"),
  p("AutoVentas es un sistema para administrar el inventario de autos de una agencia, registrar a sus clientes, vender autos con descuento y consultar indicadores del negocio. El instructivo pide construir **el mismo sistema en dos tecnologías**:"),
  vineta("**Versión de escritorio:** Python con tkinter, organizada en pestañas (ttk.Notebook)."),
  vineta("**Versión web:** HTML5, CSS3 y JavaScript, organizada en secciones equivalentes a las pestañas."),
  p("Primero se desarrolla y valida la lógica en Python; después se traslada la misma funcionalidad a la web. Así se demuestra que el diseño (requerimientos, modelo de datos y arquitectura) es independiente de la tecnología.", { before: 120 }),
  h2("1.1 Plan de trabajo acordado"),
  tabla(["Fase", "Alcance", "Estado"], [
    ["1. Escritorio", "Aplicación Python + tkinter con 4 pestañas, pruebas unitarias y documentación.", "Terminada; en validación"],
    ["Validación escritorio", "El responsable ejecuta la aplicación y confirma que cumple los requisitos.", "Aprobada tras la iteración 1 (sección 7.3)"],
    ["2. Web", "Traslado de la misma funcionalidad a HTML, CSS y JavaScript con localStorage y diseño responsive.", "Terminada (sección 7.4)"],
    ["Validación web", "El responsable revisa la versión web contra los mismos requisitos.", "Aprobada sin cambios"],
    ["Documentación", "Este documento se actualiza al cierre de cada fase.", "Versión 2.1 (final)"],
  ], [1.2, 4, 1.4], { primeraNegrita: true }),
  h2("1.2 Objetivos"),
  numero("Usar la IA como asistente de desarrollo y reconocer sus limitaciones."),
  numero("Redactar prompts con contexto, instrucción, restricciones y formato de salida, e iterar sobre ellos."),
  numero("Definir requerimientos funcionales y no funcionales, historias de usuario y criterios de aceptación."),
  numero("Diseñar un modelo de datos y una arquitectura con separación de responsabilidades."),
  numero("Distinguir entre código generado y código validado, y refactorizarlo."),
  numero("Depurar, escribir pruebas unitarias y aplicar validaciones y seguridad básica."),
];

const requerimientos = [
  h1("2. Requerimientos"),
  h2("2.1 Requerimientos funcionales"),
  p("Ambas versiones cumplen los mismos requerimientos. La columna «Web» indica solo lo que cambia respecto de escritorio."),
  tabla(["ID", "Requerimiento", "Escritorio (tkinter)", "Web (HTML, CSS, JS)"], [
    ["RF-01", "Registrar, editar y eliminar autos (marca, modelo, año, precio, kilometraje, estado).", "Pestaña Inventario: formulario a la izquierda; al seleccionar una fila se carga para editar o eliminar. El estado lo asigna el sistema.", "Sección Inventario con el mismo formulario; los errores aparecen bajo cada campo."],
    ["RF-02", "Listar el inventario con búsqueda y filtros por marca, año y rango de precio.", "Búsqueda por marca o modelo y filtros por marca, año, precio mínimo, precio máximo y estado. Se aplican al escribir.", "Mismos filtros; la marca sugiere las marcas registradas."],
    ["RF-03", "Registrar clientes (nombre, teléfono, correo, documento).", "Pestaña Clientes con registro, edición, eliminación y búsqueda. El listado se ordena por ID, de menor a mayor.", "Igual, en la sección Clientes."],
    ["RF-04", "Registrar una venta: elegir cliente y auto, calcular total con descuento y marcar el auto como «Vendido».", "Pestaña Ventas: buscadores de cliente y de auto disponible que filtran al escribir; total en vivo, confirmación y cambio del auto a «Vendido».", "Mismos buscadores (con teclado: flechas y Enter) y diálogo de confirmación con el detalle."],
    ["RF-05", "Mostrar el historial de ventas.", "Tabla «Historial de ventas», de la más reciente a la más antigua.", "Igual."],
    ["RF-06", "Mostrar un resumen (dashboard): autos disponibles, vendidos y total vendido.", "Pestaña Resumen con 6 indicadores, últimas ventas e inventario por marca.", "Igual, en tarjetas que se reacomodan según la pantalla."],
  ], [0.75, 2.2, 2.6, 2.1], { primeraNegrita: true }),
  h2("2.2 Requerimientos no funcionales"),
  tabla(["ID", "Requerimiento", "Escritorio (tkinter)", "Web (HTML, CSS, JS)"], [
    ["RNF-01", "Interfaz clara, con navegación por pestañas (Python) o secciones (web).", "ttk.Notebook con Inventario · Clientes · Ventas · Resumen; tema visual propio, mensajes en barra de estado.", "Cuatro secciones con barra de navegación; la dirección (#ventas) indica la sección. Navegable con teclado."],
    ["RNF-02", "Validación de datos de entrada (campos vacíos, precios negativos, correo inválido).", "Módulo validaciones.py. Todos los errores de un formulario se muestran juntos.", "validaciones.js con las mismas reglas y mensajes; resumen de errores y campo marcado en rojo."],
    ["RNF-03", "Persistencia local: JSON en Python y localStorage en web.", "datos/autoventas.json, guardado automático tras cada operación, escritura atómica y respaldo si el archivo está dañado.", "localStorage con el mismo formato JSON; respaldo si los datos están dañados y aviso si el navegador bloquea el almacenamiento."],
    ["RNF-04", "Código modular, con lógica separada de la interfaz.", "5 módulos; la lógica no importa tkinter y se prueba sin interfaz ni archivos.", "5 archivos JS equivalentes; la lógica no usa el DOM y se prueba con Node."],
    ["RNF-05", "Diseño responsive en la versión web.", "No aplica; la ventana se adapta al tamaño y escalado de la pantalla.", "Tres diseños: computadora, tableta y teléfono (tablas como tarjetas). Verificado sin desplazamiento horizontal."],
  ], [0.75, 2.2, 2.6, 2.1], { primeraNegrita: true }),
];

function historia(id, titulo, enunciado, criterios) {
  return [
    h3(`${id}: ${titulo}`),
    p(enunciado, { italics: true }),
    tabla(["Criterio de aceptación", "Cumplimiento (escritorio y web)"], criterios, [1, 1.3]),
    espacio(),
  ];
}

const historias = [
  h1("3. Historias de usuario y criterios de aceptación"),
  p("Los criterios se cumplen igual en las dos versiones: la lógica web es una traducción directa de la de escritorio y las mismas 37 pruebas pasan en ambas (sección 6)."),
  ...historia("HU-01", "Registrar un auto", "Como vendedor, quiero registrar un auto para tenerlo en el inventario.", [
    ["Todos los campos son obligatorios.", "Cumple. Si faltan campos se listan todos en un solo mensaje (prueba: 5 errores juntos)."],
    ["Precio > 0 y año entre 1990 y el año actual.", "Cumple. Se rechazan precio 0, negativo o texto, y años 1989 y 2027; se aceptan 1990 y 2026."],
    ["Al guardar, el auto aparece en la lista con estado «Disponible».", "Cumple. La barra de estado confirma «registrado con estado Disponible»."],
  ]),
  ...historia("HU-02", "Buscar autos", "Como vendedor, quiero filtrar el inventario para encontrar rápido un auto.", [
    ["Se puede filtrar por marca y por rango de precio.", "Cumple. También por año, estado y texto libre; no distingue mayúsculas ni tildes."],
    ["Si no hay resultados, se muestra un mensaje claro.", "Cumple. «Sin resultados: ningún auto coincide con los filtros aplicados.»"],
  ]),
  ...historia("HU-03", "Registrar un cliente", "Como vendedor, quiero guardar los datos del cliente para asociarlos a una venta.", [
    ["El correo debe tener formato válido.", "Cumple. Se rechazan «abc», «a@b», «a@@b.com», «a b@c.com», etc."],
    ["No se permiten documentos duplicados.", "Cumple. «1234-56789-0101» y «1234567890101» se reconocen como el mismo documento."],
  ]),
  ...historia("HU-04", "Registrar una venta", "Como vendedor, quiero vender un auto a un cliente.", [
    ["Solo se pueden vender autos «Disponibles».", "Cumple. El buscador de autos de la venta solo muestra disponibles y la lógica bloquea cualquier intento con un auto vendido."],
    ["Total = precio − descuento (máximo 15 %).", "Cumple. El descuento se ingresa en %; 15 % se acepta y 20 % se rechaza."],
    ["Al confirmar, el auto pasa a «Vendido» y la venta queda en el historial.", "Cumple. Ambas cosas ocurren en una sola transacción."],
  ]),
  ...historia("HU-05", "Ver resumen", "Como gerente, quiero ver indicadores generales del negocio.", [
    ["Se muestran autos disponibles, vendidos y monto total vendido.", "Cumple, además de ventas realizadas, clientes y valor del inventario disponible."],
    ["Los valores se actualizan automáticamente tras cada operación.", "Cumple. Cada operación refresca todas las pestañas."],
  ]),
];

const modelo = [
  h1("4. Modelo de datos"),
  p("Relaciones: una venta pertenece a un cliente y a un auto; un cliente puede tener varias ventas. Los campos marcados como **adicional** no están en el instructivo y se agregaron para conservar el historial exacto aunque cambien los datos después."),
  h3("Auto"),
  tabla(["Campo", "Tipo", "Regla"], [
    ["id", "entero", "Asignado por el sistema; nunca se reutiliza."],
    ["marca, modelo", "texto", "Obligatorios, máximo 40 caracteres."],
    ["anio", "entero", "Entre 1990 y el año actual."],
    ["precio", "decimal (Q)", "Mayor que 0. Acepta «85,000.50» o «Q 85000»."],
    ["kilometraje", "entero", "0 o más, sin decimales."],
    ["estado", "texto", "«Disponible» al registrar; «Vendido» al vender."],
  ], [1.4, 1.2, 4]),
  h3("Cliente"),
  tabla(["Campo", "Tipo", "Regla"], [
    ["id", "entero", "Asignado por el sistema."],
    ["nombre", "texto", "Obligatorio; letras, espacios, puntos y guiones; de 3 a 80 caracteres."],
    ["telefono", "texto", "De 8 a 15 dígitos; admite espacios, guiones y «+»."],
    ["correo", "texto", "Formato usuario@dominio.ext; se guarda en minúsculas."],
    ["documento", "texto", "De 5 a 20 letras, números o guiones; único (sin contar guiones ni mayúsculas)."],
  ], [1.4, 1.2, 4]),
  h3("Venta"),
  tabla(["Campo", "Tipo", "Regla"], [
    ["id", "entero", "Asignado por el sistema."],
    ["id_auto, id_cliente", "entero", "Deben existir; el auto debe estar «Disponible»."],
    ["fecha", "texto", "Fecha y hora de registro, formato AAAA-MM-DD HH:MM."],
    ["descuento", "decimal (Q)", "Monto = precio × porcentaje / 100."],
    ["total", "decimal (Q)", "precio − descuento."],
    ["precio (adicional)", "decimal (Q)", "Precio del auto al momento de la venta."],
    ["porcentaje_descuento (adicional)", "decimal", "De 0 a 15."],
  ], [1.9, 1.2, 3.5]),
];

const arquitectura = [
  h1("5. Arquitectura"),
  p("La aplicación se dividió en capas para cumplir RNF-04. La interfaz no contiene reglas de negocio y la lógica no sabe que existe una interfaz ni un archivo: recibe una función para guardar. Esto permite probar toda la lógica en milisegundos y reutilizar el mismo diseño en la versión web."),
  tabla(["Módulo", "Responsabilidad", "Depende de"], [
    ["validaciones.py", "Validar y convertir cada campo; ErrorValidacion con uno o varios mensajes.", "Nada (biblioteca estándar)"],
    ["logica.py", "Clase AutoVentas: CRUD de autos y clientes, filtros, búsqueda por palabras, ventas, historial y resumen. Cada cambio es una transacción.", "validaciones.py"],
    ["persistencia.py", "Cargar y guardar el JSON de forma atómica; respaldar un archivo dañado.", "Nada"],
    ["interfaz.py", "Ventana, estilos y las 4 pestañas, más el componente SelectorBuscable (buscador con lista). Solo llama a la lógica y muestra resultados.", "logica.py, tkinter"],
    ["main.py", "Une las capas: carga el JSON, crea el servicio y abre la ventana.", "Todos"],
    ["pruebas/", "37 pruebas unitarias, incluidos CP-01 a CP-06.", "logica.py, persistencia.py"],
  ], [1.5, 4, 1.8], { primeraNegrita: true }),
  h2("5.1 Flujo de una operación"),
  numero("El usuario completa el formulario y pulsa el botón (o Enter).", "flujo"),
  numero("La interfaz envía el texto tal como se escribió al servicio AutoVentas.", "flujo"),
  numero("El servicio valida todo; si hay errores, lanza ErrorValidacion con la lista completa y nada cambia.", "flujo"),
  numero("Si es válido, aplica el cambio y llama a la función de guardado. Si el guardado falla, los datos en memoria vuelven a su estado anterior.", "flujo"),
  numero("La interfaz refresca las cuatro pestañas y muestra el resultado en la barra de estado.", "flujo"),
  h2("5.2 Decisiones de diseño ante puntos no definidos"),
  p("El instructivo deja algunos puntos abiertos. Estas son las decisiones tomadas; el responsable puede pedir cambiarlas durante la validación:"),
  tabla(["Punto abierto", "Decisión", "Razón"], [
    ["RF-01 incluye «estado» como dato del auto.", "El estado no se escribe a mano: nace «Disponible» y pasa a «Vendido» solo con una venta.", "Evita autos «Vendidos» sin venta en el historial."],
    ["¿Descuento en monto o en porcentaje?", "Se ingresa en porcentaje (0–15 %) y se guarda el monto.", "La regla y el caso CP-04 están expresados en porcentaje."],
    ["¿Se puede editar o eliminar un auto vendido?", "No; queda en solo lectura.", "Forma parte del historial de ventas."],
    ["¿Se puede eliminar un cliente con compras?", "No.", "Una venta debe pertenecer a un cliente existente."],
    ["Filtro por marca y por año.", "Marca: coincidencia parcial sin mayúsculas ni tildes. Año: exacto.", "Rapidez de búsqueda (HU-02)."],
    ["Cómo buscar en Ventas (iteración 1).", "Cada palabra escrita debe aparecer en el registro, en cualquier orden: «corolla 2020» encuentra el Toyota Corolla 2020. Clientes en orden de ID; autos por marca y modelo.", "Pocas letras bastan para llegar al registro aunque haya muchos."],
    ["Moneda.", "Quetzales (Q).", "Contexto de las prácticas del curso."],
  ], [2, 2.8, 2.2]),
  h2("5.3 Equivalencia entre la versión de escritorio y la web"),
  p("La versión web se construyó traduciendo cada capa por separado. Solo cambian la persistencia y la interfaz; las reglas de negocio, los mensajes de error y el formato de los datos son los mismos. Esto demuestra que el diseño es independiente de la tecnología."),
  tabla(["Responsabilidad", "Escritorio", "Web", "Qué cambia"], [
    ["Validaciones", "validaciones.py", "js/validaciones.js", "Nada: mismas reglas y mensajes. En web el error indica también qué campo marcar."],
    ["Reglas de negocio", "logica.py", "js/logica.js", "Nada: misma clase AutoVentas, transacciones, búsqueda y resumen."],
    ["Persistencia", "persistencia.py (archivo JSON)", "js/persistencia.js (localStorage)", "Dónde se guarda; el contenido JSON es idéntico."],
    ["Interfaz", "interfaz.py (ttk.Notebook)", "index.html, css/estilos.css, js/interfaz.js", "Pestañas → secciones; messagebox → diálogo; barra de estado → avisos breves."],
    ["Arranque", "main.py", "js/main.js", "En web, sincroniza si la app está abierta en dos pestañas."],
    ["Pruebas", "unittest (37)", "node --test (37)", "Mismos casos traducidos; en web, un almacén falso sustituye a localStorage."],
  ], [1.4, 1.7, 2.1, 2.8], { primeraNegrita: true }),
  h2("5.4 Decisiones propias de la versión web"),
  vineta("**Sin librerías ni servidor.** Basta abrir index.html; funciona sin conexión. Los archivos JS usan un envoltorio que los hace funcionar en el navegador y en Node, para probar la misma lógica."),
  vineta("**Seguridad básica.** Los datos del usuario se insertan siempre como texto (textContent), nunca como HTML: si alguien escribe «<img onerror=…>» se muestra tal cual y no se ejecuta. Se verificó en la prueba de extremo a extremo."),
  vineta("**Accesibilidad.** Etiquetas en todos los campos, errores anunciados a lectores de pantalla, navegación entre secciones con flechas, buscadores con el patrón «combobox» y enlace para saltar al contenido."),
  vineta("**Responsive (RNF-05).** Computadora ≥ 1100 px: formulario y listado lado a lado. Tableta 760–1099 px: formulario arriba. Teléfono < 760 px: una columna, navegación en cuatro botones iguales y tablas convertidas en tarjetas."),
  vineta("**Datos seguros.** Si localStorage tiene datos dañados se respaldan antes de iniciar vacío; si está bloqueado, la app funciona y avisa que no guardará; si otra pestaña cambia los datos, esta se actualiza para no sobrescribirlos."),
];

const pruebas = [
  h1("6. Pruebas"),
  h2("6.1 Casos de prueba mínimos del instructivo"),
  p("Cada caso se verificó en las dos versiones y de dos formas: con una prueba unitaria sobre la lógica y operando la interfaz real con un script que llena los formularios y pulsa los botones (la ventana tkinter en escritorio; la página en Microsoft Edge en web)."),
  tabla(["ID", "Caso", "Resultado esperado", "Resultado obtenido (igual en ambas versiones)", "Escritorio", "Web"], [
    ["CP-01", "Registrar auto con precio −5000", "Rechazado con mensaje de error", "«El precio debe ser mayor que cero.» No se guarda. En web, además, el campo Precio queda marcado.", "Aprobado", "Aprobado"],
    ["CP-02", "Registrar cliente con correo «abc»", "Rechazado por formato inválido", "«El correo no tiene un formato válido (ejemplo: nombre@dominio.com).»", "Aprobado", "Aprobado"],
    ["CP-03", "Vender un auto con estado «Vendido»", "Operación bloqueada", "«Operación bloqueada: el auto #2 Honda Civic 2019 no está disponible (estado: Vendido).»", "Aprobado", "Aprobado"],
    ["CP-04", "Aplicar descuento del 20 %", "Rechazado (máximo 15 %)", "La vista previa y el registro muestran «El descuento no puede superar el 15 %.» No se crea la venta.", "Aprobado", "Aprobado"],
    ["CP-05", "Venta correcta", "Auto pasa a «Vendido» y el total se calcula bien", "Q 135,000.00 − 10 % = Q 121,500.00; el auto cambia a «Vendido» y sale del buscador de disponibles.", "Aprobado", "Aprobado"],
    ["CP-06", "Filtrar por una marca inexistente", "Mensaje «sin resultados»", "Filtro «Ferrari»: «Sin resultados: ningún auto coincide con los filtros aplicados.»", "Aprobado", "Aprobado"],
  ], [0.7, 1.4, 1.4, 2.8, 0.95, 0.85], { primeraNegrita: true }),
  h2("6.2 Pruebas unitarias"),
  p("Las dos versiones tienen las mismas 37 pruebas, organizadas en los mismos grupos. Escritorio (desde la carpeta escritorio):"),
  codigo("python -m unittest discover -s pruebas -t . -v"),
  p("Web (desde la carpeta web, con Node.js 18 o superior):", { before: 120 }),
  codigo("node --test"),
  p("Resultado: **escritorio 37/37 aprobadas · web 37/37 aprobadas.** Las pruebas web pasaron en la primera ejecución, lo que confirma que la traducción de la lógica conservó las reglas.", { before: 120 }),
  tabla(["Grupo", "Pruebas", "Qué verifica"], [
    ["Casos mínimos", "6", "CP-01 a CP-06."],
    ["HU-01 Autos", "8", "Campos obligatorios, límites de año, precio y kilometraje, edición, eliminación, bloqueo de autos vendidos e id no reutilizados."],
    ["HU-02 Búsqueda", "5", "Marca sin mayúsculas ni tildes, rango de precio, año, texto, estado y filtros inválidos."],
    ["HU-03 Clientes", "5", "Formatos de correo, documento duplicado, edición, bloqueo al eliminar y teléfonos inválidos."],
    ["HU-04 Ventas", "4", "Descuento de 15 %, descuento vacío o negativo, venta sin selección y orden del historial."],
    ["Buscadores (iteración 1)", "4", "Búsqueda por palabras sin orden ni tildes, clientes ordenados por ID, búsqueda de cliente por cualquier dato y de auto solo entre disponibles."],
    ["HU-05 Resumen", "1", "Indicadores antes y después de dos ventas."],
    ["RNF-03 Persistencia", "4", "Guardar y recargar, archivo (o localStorage) dañado, fallo al guardar sin perder datos y formato del JSON."],
  ], [1.6, 0.8, 5], { primeraNegrita: true }),
  h2("6.3 Evidencia de la interfaz de escritorio"),
  ...imagen("02_inventario.png", "Figura 1. Inventario: formulario, filtros y autos disponibles (verde) y vendidos (gris). Abajo, el bloqueo de CP-03."),
  ...imagen("06_filtro_sin_resultados.png", "Figura 2. CP-06: filtro por una marca inexistente."),
  ...imagen("03_clientes.png", "Figura 3. Clientes ordenados por ID; abajo, el rechazo de un documento duplicado escrito con guiones."),
  ...imagen("08_ventas_busqueda.png", "Figura 4. Ventas: los buscadores filtran mientras se escribe («toyota» deja solo los 2 Toyota disponibles)."),
  ...imagen("05_venta_descuento_20.png", "Figura 5. CP-04: un descuento de 20 % se marca como inválido antes de registrar."),
  ...imagen("04_ventas.png", "Figura 6. Ventas: cliente y auto elegidos con el buscador, total en vivo e historial."),
  ...imagen("07_resumen.png", "Figura 7. Resumen: indicadores actualizados tras dos ventas."),
  h2("6.4 Prueba de extremo a extremo de la versión web"),
  p("Un script maneja la página real en Microsoft Edge sin ventana: escribe en los formularios, pulsa botones y teclas, cambia el tamaño de pantalla y toma capturas. Registra además cualquier error de la consola del navegador. Resultado final: **45 de 45 verificaciones correctas y ningún error en la consola.**"),
  tabla(["Grupo", "Verificaciones", "Qué se comprobó"], [
    ["Casos mínimos", "10", "CP-01 a CP-06 con el resultado esperado (tabla de la sección 6.1), incluido que el error marque el campo y que no se guarde nada."],
    ["Inventario y clientes", "13", "Arranque, navegación, lista vacía, 5 errores juntos, registro de 6 autos y 8 clientes, aviso de confirmación, documento duplicado, orden por ID, auto vendido en solo lectura, filtros combinados y rango de precio invertido."],
    ["Ventas", "10", "Buscadores (escritura, Enter, flechas, «Sin resultados»), vista previa del total, confirmación, el auto vendido sale del buscador, historial ordenado, máximo 2 avisos."],
    ["Resumen y persistencia", "2", "Indicadores correctos y datos conservados tras recargar la página."],
    ["Responsive", "7", "Sin desplazamiento horizontal en teléfono (390 px) y tableta (820 px); tablas como tarjetas en teléfono."],
    ["Seguridad y robustez", "3", "Texto con HTML no se ejecuta, eliminar con confirmación, datos dañados se respaldan y la app inicia vacía con aviso."],
  ], [1.7, 1.3, 4.6], { primeraNegrita: true }),
  h2("6.5 Evidencia de la interfaz web"),
  ...imagen("web_02_inventario.png", "Figura 8. Web — Inventario: formulario, filtros y estado de cada auto.", { carpeta: CAPTURAS_WEB }),
  ...imagen("web_02_cp01_precio_negativo.png", "Figura 9. Web — CP-01: el error aparece arriba del formulario y bajo el campo Precio.", { carpeta: CAPTURAS_WEB }),
  ...imagen("web_03_clientes.png", "Figura 10. Web — Clientes ordenados por ID; documento duplicado bloqueado.", { carpeta: CAPTURAS_WEB }),
  ...imagen("web_04_ventas_buscadores.png", "Figura 11. Web — Ventas: buscadores de cliente y de auto.", { carpeta: CAPTURAS_WEB }),
  ...imagen("web_05_cp04_descuento_20.png", "Figura 12. Web — CP-04: descuento de 20 % rechazado.", { carpeta: CAPTURAS_WEB }),
  ...imagen("web_06_confirmar_venta.png", "Figura 13. Web — Confirmación de la venta con el detalle del cálculo.", { carpeta: CAPTURAS_WEB }),
  ...imagen("web_07_ventas.png", "Figura 14. Web — Ventas registradas, historial y avisos de confirmación.", { carpeta: CAPTURAS_WEB }),
  ...imagen("web_08_cp03_bloqueado.png", "Figura 15. Web — CP-03: intento de vender un auto vendido.", { carpeta: CAPTURAS_WEB }),
  ...imagen("web_09_cp06_sin_resultados.png", "Figura 16. Web — CP-06: filtro por una marca inexistente.", { carpeta: CAPTURAS_WEB }),
  ...imagen("web_10_resumen.png", "Figura 17. Web — Resumen: mismos valores que la versión de escritorio (Figura 7).", { carpeta: CAPTURAS_WEB }),
  ...imagenesEnFila([
    { archivo: "web_11_movil_inventario.png", leyenda: "Inventario: tabla como tarjetas" },
    { archivo: "web_12_movil_ventas.png", leyenda: "Ventas: buscadores" },
    { archivo: "web_13_movil_resumen.png", leyenda: "Resumen" },
  ], "Figura 18. Web en un teléfono de 390 px de ancho (RNF-05)."),
  ...imagen("web_14_tableta_inventario.png", "Figura 19. Web en una tableta de 820 px: formulario arriba del listado.", { carpeta: CAPTURAS_WEB, altoMax: 560 }),
];

const bitacora = [
  h1("7. Bitácora del proceso"),
  p("Registro cronológico del desarrollo de las dos fases (13 de noviembre de 2026)."),
  h3("Fase 1: versión de escritorio"),
  tabla(["#", "Actividad", "Resultado"], [
    ["1", "Lectura del instructivo y extracción de RF, RNF, HU, modelo de datos y casos de prueba.", "Lista de 6 RF, 5 RNF, 5 HU y 6 CP como criterios de terminado."],
    ["2", "Diseño de la arquitectura en capas y decisiones sobre puntos no definidos (sección 5.2).", "5 módulos; la lógica no depende de tkinter."],
    ["3", "Generación de validaciones.py, logica.py y persistencia.py.", "Reglas de negocio centralizadas y probables sin interfaz."],
    ["4", "Generación de interfaz.py y main.py con ttk.Notebook y 4 pestañas.", "Aplicación funcional."],
    ["5", "Pruebas unitarias (33).", "33/33 aprobadas en la primera ejecución."],
    ["6", "Prueba automatizada de la ventana real: llenado de formularios, CP-01 a CP-06 y capturas.", "Todos los casos con el resultado esperado."],
    ["7", "Revisión visual de las capturas.", "**Defecto encontrado:** con el escalado de Windows al 150 % la ventana de tamaño fijo cortaba los botones del formulario, los filtros y las columnas."],
    ["8", "Corrección: tamaño de ventana calculado según el contenido y la pantalla, columnas escaladas, filtros en dos filas.", "Re-prueba completa: casos aprobados y diseño correcto."],
    ["9", "Documentación (este documento).", "Versión 1.0."],
    ["10", "Primera validación del responsable.", "Dos cambios solicitados (sección 7.3)."],
    ["11", "Implementación: búsqueda por palabras en logica.py, orden por ID y componente SelectorBuscable en la pestaña Ventas.", "Cambios aplicados sin tocar las reglas de negocio existentes."],
    ["12", "Pruebas: 4 pruebas unitarias nuevas y re-ejecución de la prueba de la ventana real con 8 clientes.", "37/37 aprobadas; CP-01 a CP-06 siguen aprobados."],
    ["13", "Actualización de capturas y de este documento.", "Versión 1.1."],
    ["14", "Nueva validación del responsable.", "Aprobada: «Sí, inicia la web»."],
  ], [0.4, 3.6, 3.4]),
  h3("Fase 2: versión web"),
  tabla(["#", "Actividad", "Resultado"], [
    ["15", "Traducción de validaciones.py y logica.py a JavaScript, conservando reglas, mensajes y nombres de campo.", "validaciones.js y logica.js; el formato de datos es idéntico al JSON de escritorio."],
    ["16", "Persistencia con localStorage: respaldo de datos dañados, aviso si el almacenamiento está bloqueado.", "persistencia.js."],
    ["17", "Estructura HTML accesible con 4 secciones y CSS responsive con la paleta de escritorio.", "index.html y estilos.css (computadora, tableta y teléfono)."],
    ["18", "Interfaz: formularios con errores por campo, buscadores de venta, diálogos y avisos.", "interfaz.js y main.js; los datos del usuario se insertan solo como texto."],
    ["19", "Traducción de las 37 pruebas unitarias a node:test.", "37/37 aprobadas en la primera ejecución."],
    ["20", "Prueba de extremo a extremo en Edge sin ventana.", "**Defecto del script de prueba (no de la app):** se quedó esperando indefinidamente al recargar una dirección con «#», porque el navegador la trata como un salto dentro de la misma página. Se corrigió la prueba y se agregaron límites de tiempo."],
    ["21", "Revisión visual de las capturas.", "**Defecto encontrado:** los avisos se acumulaban y tapaban el total del historial, y cada error aparecía dos veces (en el formulario y en un aviso). Corrección: avisos solo para confirmaciones, máximo 2, se cierran a los 5 s o con un clic."],
    ["22", "Re-ejecución de todas las pruebas.", "Unitarias 37/37; extremo a extremo 45/45; sin errores en la consola."],
    ["23", "Actualización de este documento.", "Versión 2.0."],
    ["24", "Validación de la versión web por el responsable.", "Aprobada sin cambios: «Sí, cumple»."],
    ["25", "Cierre del documento.", "Versión 2.1 (final)."],
  ], [0.4, 3.6, 3.4]),
  h2("7.1 Código generado frente a código validado"),
  p("Los defectos de los pasos 7 y 21 son el ejemplo central de este proyecto: en ambas fases el código generado pasaba **todas** las pruebas unitarias, pero tenía un problema que solo apareció al ejecutar la interfaz real y mirarla. Las pruebas unitarias verifican la lógica, no cómo se ve ni cómo se siente la interfaz. Por eso el código no se considera validado hasta que (1) pasa las pruebas, (2) se opera la interfaz real y (3) una persona confirma que cumple los requisitos."),
  h2("7.2 Limitaciones de la IA observadas"),
  vineta("**No ve la pantalla del usuario por defecto.** El diseño se pensó para una resolución típica; hizo falta capturar y revisar la ventana para detectar el corte por escalado."),
  vineta("**Completa los vacíos del instructivo con supuestos.** Las decisiones de la sección 5.2 son razonables, pero deben ser confirmadas por una persona."),
  vineta("**Depende del entorno.** El primer intento del script de prueba falló porque la consola de Windows (cp1252) no podía imprimir el símbolo «−»; no era un error de la aplicación, sino del entorno."),
  vineta("**También se equivoca en sus propias herramientas.** En la fase 2, el script de prueba que escribió la IA se quedó colgado por un detalle del navegador (recargar una dirección con «#»). Las pruebas también son código y también hay que depurarlas."),
  vineta("**Diseña para el caso típico.** Los avisos funcionaban bien de uno en uno; el problema apareció con varias operaciones seguidas. Revisar capturas de escenarios reales, no solo de una operación aislada, lo hizo visible."),
  vineta("**No sustituye la validación humana.** La claridad de la interfaz y la utilidad para el vendedor solo las puede juzgar el usuario. La iteración 1 lo confirma: con pocos datos de prueba la lista desplegable parecía suficiente, pero con muchos clientes el usuario necesitó un buscador."),
  h2("7.3 Iteración 1: cambios solicitados en la validación"),
  p("Al revisar la versión de escritorio, el responsable solicitó dos cambios:"),
  tabla(["Solicitud", "Cambio realizado", "Verificación"], [
    ["«El listado de clientes, necesito que se ordene por id de menor a mayor.»",
     "buscar_clientes() devuelve los clientes ordenados por ID; la tabla de la pestaña Clientes y el buscador de Ventas usan ese orden.",
     "Prueba unitaria test_clientes_ordenados_por_id y tabla de la ventana real con 8 clientes: IDs 1 a 8 en orden (Figura 3)."],
    ["«En ventas me cuesta buscar el cliente entre tantos que hay, al igual que buscar auto.»",
     "Los dos desplegables de Ventas se reemplazaron por buscadores: un cuadro de texto que filtra una lista mientras se escribe. Cliente: por nombre, documento, teléfono o correo. Auto: por marca, modelo, año o #id, solo disponibles. Enter elige el primer resultado; debajo se confirma la selección con ✔ y, si no hay coincidencias, se muestra «Sin resultados».",
     "3 pruebas unitarias de búsqueda y prueba de la ventana real: «ruiz» → Ana Ruiz; «civic» → Honda Civic; «ferrari» → «Sin resultados»; tras vender, el auto desaparece del buscador (Figuras 4 y 6)."],
  ], [2, 3.2, 2.4]),
  p("Como la búsqueda vive en logica.py y no en la interfaz, la versión web reutilizó exactamente la misma regla.", { before: 120 }),
  h2("7.4 Fase 2: traslado a la versión web"),
  p("Tras la aprobación de la versión de escritorio, se trasladó la misma funcionalidad a HTML, CSS y JavaScript. Resultados principales:"),
  vineta("**El diseño fue independiente de la tecnología.** Las capas de validación y lógica se tradujeron casi línea por línea y las 37 pruebas, traducidas igual, pasaron en la primera ejecución. Los indicadores del Resumen dieron los mismos valores en ambas versiones con los mismos datos (Figuras 7 y 17)."),
  vineta("**Solo cambió lo que depende de la tecnología:** dónde se guardan los datos (archivo JSON → localStorage) y cómo se presentan (pestañas tkinter → secciones HTML con diseño responsive)."),
  vineta("**La web agregó requisitos propios:** diseño responsive (RNF-05), protección contra texto con HTML, accesibilidad y manejo del almacenamiento del navegador (sección 5.4)."),
  vineta("**Los cambios de la iteración 1 llegaron incluidos:** orden por ID y buscadores de venta, porque ya formaban parte de la lógica y de las pruebas."),
];

const prompts = [
  h1("8. Bitácora de prompts"),
  p("Los cinco prompts más importantes del proyecto, con su versión inicial y la mejorada, más dos prompts complementarios: los cambios de la validación y el traslado a la web. Las versiones mejoradas siguen la estructura **contexto · instrucción · restricciones · formato de salida**. Las versiones iniciales de los prompts 1, adicional y 6 son literales; las demás representan la forma breve en que suele pedirse cada tarea."),
  ...prompt(1, "Arranque del proyecto", "Análisis y planificación",
    "Vamos a construir este sistema de práctica en dos versiones según el instructivo, una versión en Python y tkinter para una versión de escritorio, luego con html, css y javascript para una versión web, primero iniciar con la versión de escritorio [...] también necesito documentar todo el proceso, dejar constancia de todo en documento Word.",
    "**Contexto:** proyecto final «AutoVentas» (PDF adjunto) con RF-01 a RF-06, RNF-01 a RNF-05, HU-01 a HU-05 y CP-01 a CP-06.\n**Instrucción:** construye solo la versión de escritorio (Python 3 + tkinter, ttk.Notebook con Inventario, Clientes, Ventas y Resumen). La versión web empieza cuando yo valide la de escritorio.\n**Restricciones:** solo biblioteca estándar; persistencia en JSON; lógica separada de la interfaz; textos en español; moneda en quetzales.\n**Formato de salida:** código en SEMANA 5/autoventas/escritorio, pruebas unitarias con los CP y un documento Word con requerimientos, HU, pruebas y bitácora de prompts.",
    "La versión inicial dice qué construir, pero no fija la tecnología exacta de pestañas, la ubicación de los archivos ni lo que debe contener el Word. La mejorada convierte el instructivo en criterios verificables y separa claramente las fases."),
  ...prompt(2, "Lógica de negocio y validaciones", "Desarrollo — capa de lógica",
    "Haz la lógica del sistema de venta de autos en Python.",
    "**Contexto:** modelo de datos Auto, Cliente y Venta del instructivo.\n**Instrucción:** escribe validaciones.py y logica.py con una clase AutoVentas que registre, edite, elimine y filtre autos y clientes, registre ventas y calcule el resumen.\n**Restricciones:** sin tkinter ni archivos; la persistencia se inyecta como función; precio > 0; año de 1990 al actual; correo válido; documento único; descuento máximo de 15 %; solo se venden autos «Disponible»; reunir todos los errores de un formulario; si falla el guardado, revertir.\n**Formato de salida:** dos módulos con docstrings en español y una excepción ErrorValidacion con una lista de mensajes.",
    "Sin restricciones, la IA tiende a mezclar la lógica con la interfaz y a validar solo el primer error. Enumerar las reglas del instructivo y exigir la separación de capas produjo código que se puede probar sin abrir ninguna ventana."),
  ...prompt(3, "Interfaz con pestañas", "Desarrollo — capa de interfaz",
    "Hazme la interfaz con tkinter con pestañas.",
    "**Contexto:** ya existe logica.py con la clase AutoVentas.\n**Instrucción:** crea interfaz.py con ttk.Notebook y 4 pestañas. Inventario: formulario, filtros (texto, marca, año, precio mín./máx., estado) y tabla. Clientes: formulario, búsqueda y tabla. Ventas: cliente y auto disponibles, descuento en %, total en vivo, confirmación e historial. Resumen: indicadores.\n**Restricciones:** la interfaz no valida ni calcula; solo llama a la lógica. Tras cada operación, refrescar todas las pestañas. Mensaje claro cuando una tabla esté vacía. Botón para intentar vender un auto desde Inventario (CP-03).\n**Formato de salida:** un módulo con una clase por pestaña y estilos ttk propios.",
    "Pedir «pestañas» a secas produce pantallas genéricas. Detallar el contenido de cada pestaña y la regla «la interfaz no calcula» evitó duplicar reglas en dos lugares."),
  ...prompt(4, "Pruebas unitarias", "Pruebas",
    "Escribe pruebas para el programa.",
    "**Contexto:** casos mínimos CP-01 a CP-06 y criterios de aceptación de HU-01 a HU-05.\n**Instrucción:** escribe pruebas con unittest: una prueba por cada CP (con el ID en el nombre), pruebas por historia de usuario y pruebas de persistencia (recargar, archivo dañado, fallo al guardar).\n**Restricciones:** sin archivos reales salvo en carpetas temporales; probar valores límite (1990, año actual, 15 %); sin dependencias externas.\n**Formato de salida:** pruebas/test_autoventas.py, ejecutable con python -m unittest.",
    "«Escribe pruebas» suele producir pruebas que repiten el camino feliz. Vincular cada prueba con un CP o una HU hace que el informe sirva como evidencia de que se cumple el instructivo."),
  ...prompt(5, "Depuración del defecto de escalado", "Depuración",
    "La ventana se ve mal, arréglalo.",
    "**Contexto:** Windows con escalado al 150 % en una pantalla de 2560×1600; la ventana usa geometry(\"1220x760\") fijo.\n**Síntomas:** en la captura no aparecen los botones Guardar/Eliminar del Inventario, el filtro «Buscar» y el botón «Limpiar filtros» quedan cortados, las columnas Precio y Kilometraje se truncan y el historial de ventas casi no se ve.\n**Instrucción:** haz que la ventana se adapte al contenido y a la pantalla con cualquier escalado.\n**Restricciones:** no cambiar la lógica; mantener las 4 pestañas; volver a ejecutar la prueba de la interfaz y comparar capturas.",
    "Un «se ve mal» no indica causa ni criterio de éxito. Describir el entorno, los síntomas exactos y cómo comprobar la corrección llevó directo a la causa (tamaños en píxeles fijos con fuentes escaladas) y a una corrección verificable."),
  h3("Prompt adicional. Cambios de la primera validación"),
  p("Se incluye porque muestra cómo una observación real del usuario se convierte en un pedido verificable. La versión inicial es literal.", { keepNext: true }),
  p("**Fase:** Validación — iteración 1", { keepNext: true }),
  tabla(["Versión inicial", "Versión mejorada"], [[
    "El listado de clientes, necesito que se orden por id de menor a mayor y en ventas me cuesta buscar el cliente entre tantos que hay, al igual que buscar auto, entonces necesito un buscador que facilite al buscar clientes y autos para efectuar la venta.",
    "**Contexto:** AutoVentas de escritorio; pestañas Clientes y Ventas; puede haber decenas de clientes y autos.\n**Instrucción:** (1) ordena la tabla de clientes por ID ascendente; (2) en Ventas, reemplaza los desplegables por buscadores que filtren mientras se escribe: cliente por nombre, documento, teléfono o correo; auto por marca, modelo, año o #id.\n**Restricciones:** la regla de búsqueda va en logica.py (sin mayúsculas, tildes ni orden de palabras); el buscador de autos solo muestra disponibles; mensaje claro si no hay resultados; Enter elige el primero; mantener CP-01 a CP-06.\n**Formato de salida:** cambios en logica.py e interfaz.py, pruebas unitarias nuevas, capturas y documento actualizados.",
  ]], [1, 1.6]),
  p("**Qué cambió y por qué:** el pedido original es claro sobre el problema, pero no dice por qué campos buscar ni qué pasa si no hay resultados. La versión mejorada fija esos detalles y pide que la regla viva en la lógica, para probarla y reutilizarla en la web.", { before: 100, after: 200 }),
  ...prompt(6, "Traslado a la versión web", "Fase 2 — versión web",
    "Sí, inicia la web.\n(Con el contexto del primer pedido: «luego con html, css y javascript para una versión web».)",
    "**Contexto:** la versión de escritorio de AutoVentas está validada; su lógica vive en validaciones.py y logica.py, con 37 pruebas, y guarda un JSON con autos, clientes y ventas.\n**Instrucción:** construye la versión web con HTML5, CSS3 y JavaScript, con una sección por pestaña (Inventario, Clientes, Ventas, Resumen), traduciendo capa por capa: mismas reglas, mensajes y formato de datos; persistencia en localStorage.\n**Restricciones:** sin librerías ni servidor (que funcione al abrir index.html); lógica sin acceso al DOM y probada con Node; diseño responsive para computadora, tableta y teléfono; datos del usuario insertados solo como texto; accesible con teclado; mantener la iteración 1 (orden por ID y buscadores).\n**Formato de salida:** carpeta web/ con index.html, css/ y js/ por capas, las 37 pruebas traducidas, prueba de la página real en el navegador con capturas y documento actualizado.",
    "«Inicia la web» depende de todo el contexto anterior. La versión mejorada lo hace explícito y exige traducir capa por capa con las mismas pruebas: así se puede demostrar con evidencia que el diseño no depende de la tecnología, que es el objetivo del proyecto."),
];

const ejecucion = [
  h1("9. Instrucciones de ejecución"),
  h3("Versión de escritorio"),
  p("Requisito: Python 3.10 o superior (incluye tkinter). No necesita instalar paquetes."),
  codigo("cd \"SEMANA 5/autoventas/escritorio\""),
  codigo("python main.py"),
  p("Los datos se guardan en escritorio/datos/autoventas.json. Para ejecutar las pruebas:", { before: 120 }),
  codigo("python -m unittest discover -s pruebas -t . -v"),
  h3("Versión web"),
  p("Abrir el archivo SEMANA 5/autoventas/web/index.html en un navegador actual (Chrome, Edge o Firefox). No necesita servidor ni conexión a internet. Los datos se guardan en el navegador (localStorage); cada navegador tiene sus propios datos."),
  p("Para ejecutar las pruebas (requiere Node.js 18 o superior), desde la carpeta web:", { before: 120 }),
  codigo("node --test"),
  h2("9.1 Guía de validación sugerida"),
  p("Los mismos pasos sirven para las dos versiones. En la web, pruebe además el paso 7.", { keepNext: true }),
  numero("Inventario: registrar 3 autos; intentar uno con precio −5000 (CP-01) y otro con todos los campos vacíos.", "validacion"),
  numero("Clientes: registrar varios clientes y comprobar que la tabla queda ordenada por ID; intentar el correo «abc» (CP-02) y un documento repetido.", "validacion"),
  numero("Ventas: buscar un cliente escribiendo parte del nombre o del documento y un auto por marca o modelo (Enter elige el primero).", "validacion"),
  numero("Ventas: intentar un descuento de 20 % (CP-04); registrar una venta con 10 % y comprobar el total (CP-05).", "validacion"),
  numero("Inventario: seleccionar el auto vendido y pulsar «Vender este auto» (CP-03); filtrar por la marca «Ferrari» (CP-06).", "validacion"),
  numero("Resumen: comprobar los indicadores; cerrar y volver a abrir la aplicación para confirmar que los datos persisten.", "validacion"),
  numero("Solo web: reducir el ancho de la ventana (o abrir la página en un teléfono) y comprobar que todo se reacomoda en una columna y que las tablas se ven como tarjetas.", "validacion"),
];

// ---------- documento ----------
const encabezadoYPie = {
  headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
    children: [new TextRun({ text: "AutoVentas — Documentación del proyecto", color: GRIS, size: 18 })] })] }) },
  footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Página ", color: GRIS, size: 18 }),
               new TextRun({ children: [PageNumber.CURRENT], color: GRIS, size: 18 })] })] }) },
};

const listaNumerada = (ref) => ({ reference: ref, levels: [{ level: 0, format: LevelFormat.DECIMAL,
  text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] });

const doc = new Document({
  creator: "AutoVentas", title: "AutoVentas — Documentación del proyecto",
  styles: {
    default: { document: { run: { font: FUENTE, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FUENTE, size: 32, bold: true, color: AZUL },
        paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FUENTE, size: 26, bold: true, color: AZUL },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FUENTE, size: 23, bold: true, color: "2E5C8A" },
        paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: { config: [
    { reference: "vinetas", levels: [
      { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
      { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 1440, hanging: 360 } } } }] },
    listaNumerada("numeros"), listaNumerada("flujo"), listaNumerada("validacion"),
  ] },
  features: { updateFields: true },
  sections: [
    { properties: { page: { size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      children: portada.slice(0, -1) },
    { properties: { page: { size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      ...encabezadoYPie,
      children: [...indice, ...introduccion, ...requerimientos, ...historias, ...modelo,
                 ...arquitectura, ...pruebas, ...bitacora, ...prompts, ...ejecucion] },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(SALIDA, buffer);
  console.log("Generado:", SALIDA);
});

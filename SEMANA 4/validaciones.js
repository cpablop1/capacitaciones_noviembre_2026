"use strict";

/* =========================================================
   Solicitud de empleo · Validaciones del formulario
   JavaScript puro, sin frameworks ni librerías externas.
   ========================================================= */

/* ---------- Datos: municipios por departamento de Guatemala ---------- */

const MUNICIPIOS = {
    "Alta Verapaz": ["Cobán", "Santa Cruz Verapaz", "San Cristóbal Verapaz", "Tactic", "Tamahú", "Tucurú", "Panzós", "Senahú", "San Pedro Carchá", "San Juan Chamelco", "Lanquín", "Cahabón", "Chisec", "Chahal", "Fray Bartolomé de las Casas", "Santa Catalina La Tinta", "Raxruhá"],
    "Baja Verapaz": ["Salamá", "San Miguel Chicaj", "Rabinal", "Cubulco", "Granados", "El Chol", "San Jerónimo", "Purulhá"],
    "Chimaltenango": ["Chimaltenango", "San José Poaquil", "San Martín Jilotepeque", "Comalapa", "Santa Apolonia", "Tecpán Guatemala", "Patzún", "Pochuta", "Patzicía", "Santa Cruz Balanyá", "Acatenango", "Yepocapa", "San Andrés Itzapa", "Parramos", "Zaragoza", "El Tejar"],
    "Chiquimula": ["Chiquimula", "San José La Arada", "San Juan Ermita", "Jocotán", "Camotán", "Olopa", "Esquipulas", "Concepción Las Minas", "Quezaltepeque", "San Jacinto", "Ipala"],
    "El Progreso": ["Guastatoya", "Morazán", "San Agustín Acasaguastlán", "San Cristóbal Acasaguastlán", "El Jícaro", "Sansare", "Sanarate", "San Antonio La Paz"],
    "Escuintla": ["Escuintla", "Santa Lucía Cotzumalguapa", "La Democracia", "Siquinalá", "Masagua", "Tiquisate", "La Gomera", "Guanagazapa", "San José", "Iztapa", "Palín", "San Vicente Pacaya", "Nueva Concepción"],
    "Guatemala": ["Guatemala", "Santa Catarina Pinula", "San José Pinula", "San José del Golfo", "Palencia", "Chinautla", "San Pedro Ayampuc", "Mixco", "San Pedro Sacatepéquez", "San Juan Sacatepéquez", "San Raymundo", "Chuarrancho", "Fraijanes", "Amatitlán", "Villa Nueva", "Villa Canales", "San Miguel Petapa"],
    "Huehuetenango": ["Huehuetenango", "Chiantla", "Malacatancito", "Cuilco", "Nentón", "San Pedro Necta", "Jacaltenango", "Soloma", "Ixtahuacán", "Santa Bárbara", "La Libertad", "La Democracia", "San Miguel Acatán", "San Rafael La Independencia", "Todos Santos Cuchumatán", "San Juan Atitán", "Santa Eulalia", "San Mateo Ixtatán", "Colotenango", "San Sebastián Huehuetenango", "Tectitán", "Concepción Huista", "San Juan Ixcoy", "San Antonio Huista", "San Sebastián Coatán", "Barillas", "Aguacatán", "San Rafael Petzal", "San Gaspar Ixchil", "Santiago Chimaltenango", "Santa Ana Huista", "Unión Cantinil", "Petatán"],
    "Izabal": ["Puerto Barrios", "Livingston", "El Estor", "Morales", "Los Amates"],
    "Jalapa": ["Jalapa", "San Pedro Pinula", "San Luis Jilotepeque", "San Manuel Chaparrón", "San Carlos Alzatate", "Monjas", "Mataquescuintla"],
    "Jutiapa": ["Jutiapa", "El Progreso", "Santa Catarina Mita", "Agua Blanca", "Asunción Mita", "Yupiltepeque", "Atescatempa", "Jerez", "El Adelanto", "Zapotitlán", "Comapa", "Jalpatagua", "Conguaco", "Moyuta", "Pasaco", "San José Acatempa", "Quesada"],
    "Petén": ["Flores", "San José", "San Benito", "San Andrés", "La Libertad", "San Francisco", "Santa Ana", "Dolores", "San Luis", "Sayaxché", "Melchor de Mencos", "Poptún", "Las Cruces", "El Chal"],
    "Quetzaltenango": ["Quetzaltenango", "Salcajá", "Olintepeque", "San Carlos Sija", "Sibilia", "Cabricán", "Cajolá", "San Miguel Sigüilá", "San Juan Ostuncalco", "San Mateo", "Concepción Chiquirichapa", "San Martín Sacatepéquez", "Almolonga", "Cantel", "Huitán", "Zunil", "Colomba", "San Francisco La Unión", "El Palmar", "Coatepeque", "Génova", "Flores Costa Cuca", "La Esperanza", "Palestina de Los Altos"],
    "Quiché": ["Santa Cruz del Quiché", "Chiché", "Chinique", "Zacualpa", "Chajul", "Chichicastenango", "Patzité", "San Antonio Ilotenango", "San Pedro Jocopilas", "Cunén", "San Juan Cotzal", "Joyabaj", "Nebaj", "San Andrés Sajcabajá", "Uspantán", "Sacapulas", "San Bartolomé Jocotenango", "Canillá", "Chicamán", "Ixcán", "Pachalum"],
    "Retalhuleu": ["Retalhuleu", "San Sebastián", "Santa Cruz Muluá", "San Martín Zapotitlán", "San Felipe", "San Andrés Villa Seca", "Champerico", "Nuevo San Carlos", "El Asintal"],
    "Sacatepéquez": ["Antigua Guatemala", "Jocotenango", "Pastores", "Sumpango", "Santo Domingo Xenacoj", "Santiago Sacatepéquez", "San Bartolomé Milpas Altas", "San Lucas Sacatepéquez", "Santa Lucía Milpas Altas", "Magdalena Milpas Altas", "Santa María de Jesús", "Ciudad Vieja", "San Miguel Dueñas", "Alotenango", "San Antonio Aguas Calientes", "Santa Catarina Barahona"],
    "San Marcos": ["San Marcos", "San Pedro Sacatepéquez", "San Antonio Sacatepéquez", "Comitancillo", "San Miguel Ixtahuacán", "Concepción Tutuapa", "Tacaná", "Sibinal", "Tajumulco", "Tejutla", "San Rafael Pie de la Cuesta", "Nuevo Progreso", "El Tumbador", "El Rodeo", "Malacatán", "Catarina", "Ayutla", "Ocós", "San Pablo", "El Quetzal", "La Reforma", "Pajapita", "Ixchiguán", "San José Ojetenam", "San Cristóbal Cucho", "Sipacapa", "Esquipulas Palo Gordo", "Río Blanco", "San Lorenzo", "La Blanca"],
    "Santa Rosa": ["Cuilapa", "Barberena", "Santa Rosa de Lima", "Casillas", "San Rafael Las Flores", "Oratorio", "San Juan Tecuaco", "Chiquimulilla", "Taxisco", "Santa María Ixhuatán", "Guazacapán", "Santa Cruz Naranjo", "Pueblo Nuevo Viñas", "Nueva Santa Rosa"],
    "Sololá": ["Sololá", "San José Chacayá", "Santa María Visitación", "Santa Lucía Utatlán", "Nahualá", "Santa Catarina Ixtahuacán", "Santa Clara La Laguna", "Concepción", "San Andrés Semetabaj", "Panajachel", "Santa Catarina Palopó", "San Antonio Palopó", "San Lucas Tolimán", "Santa Cruz La Laguna", "San Pablo La Laguna", "San Marcos La Laguna", "San Juan La Laguna", "San Pedro La Laguna", "Santiago Atitlán"],
    "Suchitepéquez": ["Mazatenango", "Cuyotenango", "San Francisco Zapotitlán", "San Bernardino", "San José El Ídolo", "Santo Domingo Suchitepéquez", "San Lorenzo", "Samayac", "San Pablo Jocopilas", "San Antonio Suchitepéquez", "San Miguel Panán", "San Gabriel", "Chicacao", "Patulul", "Santa Bárbara", "San Juan Bautista", "Santo Tomás La Unión", "Zunilito", "Pueblo Nuevo", "Río Bravo", "San José La Máquina"],
    "Totonicapán": ["Totonicapán", "San Cristóbal Totonicapán", "San Francisco El Alto", "San Andrés Xecul", "Momostenango", "Santa María Chiquimula", "Santa Lucía La Reforma", "San Bartolo"],
    "Zacapa": ["Zacapa", "Estanzuela", "Río Hondo", "Gualán", "Teculután", "Usumatlán", "Cabañas", "San Diego", "La Unión", "Huité", "San Jorge"]
};

/* ---------- Constantes de validación ---------- */

const EDAD_MINIMA = 18;
const ANIO_GRADUACION_MINIMO = 1950;
const LONGITUD_DPI = 13;
const LONGITUD_TELEFONO = 8; // Guatemala: 8 dígitos
const TAM_MAX_FOTO = 2 * 1024 * 1024; // 2 MB
const TAM_MAX_PDF = 5 * 1024 * 1024; // 5 MB
const TIPOS_IMAGEN = ["image/jpeg", "image/png"];
const MAX_FUNCIONES = 500;

const REGEX_NOMBRE = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[ '\-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$/;
const REGEX_CORREO = /^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$/;

/* ---------- Utilidades ---------- */

const $ = (id) => document.getElementById(id);
const formulario = $("formRegistro");
const tocados = new Set(); // campos que el usuario ya visitó

/** Fecha de hoy en formato AAAA-MM-DD (hora local). */
function hoyISO() {
    const d = new Date();
    const mes = String(d.getMonth() + 1).padStart(2, "0");
    const dia = String(d.getDate()).padStart(2, "0");
    return `${d.getFullYear()}-${mes}-${dia}`;
}

function calcularEdad(fechaISO) {
    const [anio, mes, dia] = fechaISO.split("-").map(Number);
    const hoy = new Date();
    let edad = hoy.getFullYear() - anio;
    const cumpleTranscurrido =
        hoy.getMonth() + 1 > mes || (hoy.getMonth() + 1 === mes && hoy.getDate() >= dia);
    if (!cumpleTranscurrido) edad--;
    return edad;
}

/** Valor de un campo sin espacios sobrantes (también funciona con grupos de radio). */
const valor = (nombre) => String(formulario.elements[nombre].value || "").trim().replace(/\s+/g, " ");

/** Devuelve siempre un arreglo con los elementos de un campo. */
function elementos(nombre) {
    const el = formulario.elements[nombre];
    return el instanceof RadioNodeList ? Array.from(el) : [el];
}

const tieneExperiencia = () => formulario.elements.experiencia.value === "si";

function formatoTamano(bytes) {
    return bytes < 1024 * 1024
        ? `${Math.max(1, Math.round(bytes / 1024))} KB`
        : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/* ---------- Validadores (devuelven "" si el campo es válido) ---------- */

function validarNombre(texto, etiqueta) {
    if (!texto) return `Ingresa tus ${etiqueta}.`;
    if (texto.length < 2) return `Tus ${etiqueta} deben tener al menos 2 caracteres.`;
    if (!REGEX_NOMBRE.test(texto)) return `Tus ${etiqueta} solo pueden contener letras y espacios.`;
    return "";
}

function validarTextoLibre(texto, mensajeVacio, minimo, etiqueta) {
    if (!texto) return mensajeVacio;
    if (texto.length < minimo) return `${etiqueta} debe tener al menos ${minimo} caracteres.`;
    return "";
}

function validarFecha(nombre, mensajeVacio) {
    const v = valor(nombre);
    if (!v) return mensajeVacio;
    if (v > hoyISO()) return "La fecha no puede ser posterior a hoy.";
    return "";
}

const validadores = {
    /* 1. Datos personales */
    nombres: () => validarNombre(valor("nombres"), "nombres"),
    apellidos: () => validarNombre(valor("apellidos"), "apellidos"),

    fechaNacimiento: () => {
        const v = valor("fechaNacimiento");
        if (!v) return "Selecciona tu fecha de nacimiento.";
        if (v > hoyISO()) return "La fecha de nacimiento no puede ser futura.";
        const edad = calcularEdad(v);
        if (edad < EDAD_MINIMA) return `Debes tener al menos ${EDAD_MINIMA} años para registrarte.`;
        if (edad > 100) return "Revisa la fecha de nacimiento ingresada.";
        return "";
    },

    dpi: () => {
        const v = valor("dpi");
        if (!v) return "Ingresa tu número de DPI.";
        if (/\D/.test(v)) return "El DPI solo debe contener números.";
        if (v.length !== LONGITUD_DPI) {
            return `El DPI debe tener exactamente ${LONGITUD_DPI} dígitos (ingresaste ${v.length}).`;
        }
        return "";
    },

    genero: () => (valor("genero") ? "" : "Selecciona una opción de género."),

    fotografia: () => {
        const archivo = formulario.elements.fotografia.files[0];
        if (!archivo) return "Adjunta tu fotografía.";
        if (!TIPOS_IMAGEN.includes(archivo.type)) return "La fotografía debe estar en formato JPG o PNG.";
        if (archivo.size > TAM_MAX_FOTO) return "La fotografía no debe superar los 2 MB.";
        return "";
    },

    /* 2. Información de contacto */
    correo: () => {
        const v = valor("correo");
        if (!v) return "Ingresa tu correo electrónico.";
        if (v.length > 100 || !REGEX_CORREO.test(v)) {
            return "Ingresa un correo válido, por ejemplo: nombre@correo.com.";
        }
        return "";
    },

    telefono: () => {
        const v = valor("telefono");
        if (!v) return "Ingresa tu número de teléfono.";
        if (/\D/.test(v)) return "El teléfono solo debe contener números.";
        if (v.length !== LONGITUD_TELEFONO) {
            return `El teléfono debe tener ${LONGITUD_TELEFONO} dígitos (ingresaste ${v.length}).`;
        }
        return "";
    },

    direccion: () =>
        validarTextoLibre(valor("direccion"), "Ingresa tu dirección de residencia.", 5, "La dirección"),

    departamento: () => (valor("departamento") ? "" : "Selecciona un departamento."),

    municipio: () => {
        if (!valor("departamento")) return "Primero selecciona un departamento.";
        return valor("municipio") ? "" : "Selecciona un municipio.";
    },

    /* 3. Información académica */
    nivelAcademico: () => (valor("nivelAcademico") ? "" : "Selecciona tu nivel académico."),

    profesion: () =>
        validarTextoLibre(valor("profesion"), "Ingresa tu profesión o especialidad.", 3, "La profesión"),

    institucion: () =>
        validarTextoLibre(valor("institucion"), "Ingresa tu institución educativa.", 3, "El nombre de la institución"),

    anioGraduacion: () => {
        const v = valor("anioGraduacion");
        const anioActual = new Date().getFullYear();
        if (!v) return "Ingresa tu año de graduación.";
        if (!/^\d{4}$/.test(v)) return "Ingresa un año válido de 4 dígitos.";
        const anio = Number(v);
        if (anio < ANIO_GRADUACION_MINIMO || anio > anioActual) {
            return `El año debe estar entre ${ANIO_GRADUACION_MINIMO} y ${anioActual}.`;
        }
        return "";
    },

    /* 4. Experiencia laboral (los campos dependientes solo se validan si responde "Sí") */
    experiencia: () => (valor("experiencia") ? "" : "Indica si tienes experiencia laboral."),

    empresa: () =>
        !tieneExperiencia()
            ? ""
            : validarTextoLibre(valor("empresa"), "Ingresa el nombre de la última empresa.", 2, "El nombre de la empresa"),

    puesto: () =>
        !tieneExperiencia()
            ? ""
            : validarTextoLibre(valor("puesto"), "Ingresa el puesto que desempeñaste.", 2, "El puesto"),

    fechaInicio: () =>
        !tieneExperiencia() ? "" : validarFecha("fechaInicio", "Selecciona la fecha de inicio."),

    fechaFin: () => {
        if (!tieneExperiencia()) return "";
        const mensaje = validarFecha("fechaFin", "Selecciona la fecha de finalización.");
        if (mensaje) return mensaje;
        const inicio = valor("fechaInicio");
        if (inicio && valor("fechaFin") < inicio) {
            return "La fecha de finalización no puede ser anterior a la fecha de inicio.";
        }
        return "";
    },

    funciones: () =>
        !tieneExperiencia()
            ? ""
            : validarTextoLibre(valor("funciones"), "Describe las funciones que realizabas.", 20, "La descripción"),

    /* 5. Confirmación */
    hojaVida: () => {
        const archivo = formulario.elements.hojaVida.files[0];
        if (!archivo) return "Adjunta tu hoja de vida en formato PDF.";
        const esPdf = /\.pdf$/i.test(archivo.name) && (archivo.type === "application/pdf" || archivo.type === "");
        if (!esPdf) return "El archivo debe ser un PDF (.pdf).";
        if (archivo.size > TAM_MAX_PDF) return "La hoja de vida no debe superar los 5 MB.";
        return "";
    },

    aceptaDatos: () =>
        formulario.elements.aceptaDatos.checked
            ? ""
            : "Debes aceptar el tratamiento de tus datos personales para poder registrarte."
};

/* ---------- Mostrar / ocultar errores ---------- */

/** Valida un campo, actualiza su mensaje y devuelve true si es válido. */
function validarCampo(nombre) {
    const mensaje = validadores[nombre]();
    const zonaError = $(`error-${nombre}`);
    zonaError.textContent = mensaje;
    zonaError.closest(".campo").classList.toggle("con-error", mensaje !== "");
    elementos(nombre).forEach((el) => {
        el.setAttribute("aria-invalid", mensaje ? "true" : "false");
        el.setAttribute("aria-describedby", `error-${nombre}`);
    });
    return mensaje === "";
}

function limpiarError(nombre) {
    const zonaError = $(`error-${nombre}`);
    zonaError.textContent = "";
    zonaError.closest(".campo").classList.remove("con-error");
    elementos(nombre).forEach((el) => el.removeAttribute("aria-invalid"));
}

function mostrarEstado(texto) {
    const estado = $("estadoFormulario");
    estado.textContent = texto;
    estado.hidden = false;
}

function ocultarEstado() {
    $("estadoFormulario").hidden = true;
}

/* ---------- Comportamientos de la interfaz ---------- */

function cargarDepartamentos() {
    const select = formulario.elements.departamento;
    Object.keys(MUNICIPIOS).forEach((depto) => select.add(new Option(depto, depto)));
}

function cargarMunicipios(departamento) {
    const select = formulario.elements.municipio;
    select.innerHTML = "";
    select.add(
        new Option(
            departamento ? "Selecciona un municipio" : "Primero selecciona un departamento",
            "",
            true,
            true
        )
    );
    select.disabled = !departamento;
    (MUNICIPIOS[departamento] || []).forEach((m) => select.add(new Option(m, m)));
}

function alternarExperiencia(mostrar) {
    $("bloqueExperiencia").hidden = !mostrar;
    ["empresa", "puesto", "fechaInicio", "fechaFin", "funciones"].forEach((nombre) => {
        formulario.elements[nombre].disabled = !mostrar;
        if (!mostrar) {
            formulario.elements[nombre].value = "";
            tocados.delete(nombre);
            limpiarError(nombre);
        }
    });
    if (!mostrar) {
        formulario.elements.fechaFin.min = "";
        actualizarContador();
    }
}

function actualizarContador() {
    $("contadorFunciones").textContent = `${formulario.elements.funciones.value.length} / ${MAX_FUNCIONES}`;
}

let urlFoto = null;

function actualizarVistaFoto() {
    const archivo = formulario.elements.fotografia.files[0];
    const img = $("vistaFoto");
    if (urlFoto) URL.revokeObjectURL(urlFoto);
    urlFoto = null;

    if (archivo && TIPOS_IMAGEN.includes(archivo.type)) {
        urlFoto = URL.createObjectURL(archivo);
        img.src = urlFoto;
        img.hidden = false;
        $("iconoFoto").style.display = "none";
        $("textoFoto").textContent = archivo.name;
    } else {
        img.removeAttribute("src");
        img.hidden = true;
        $("iconoFoto").style.display = "";
        $("textoFoto").textContent = archivo ? archivo.name : "Seleccionar fotografía";
    }
    img.closest(".archivo-zona").classList.toggle("con-archivo", Boolean(archivo) && validadores.fotografia() === "");
}

function actualizarNombrePdf() {
    const archivo = formulario.elements.hojaVida.files[0];
    $("nombrePdf").textContent = archivo
        ? `${archivo.name} (${formatoTamano(archivo.size)})`
        : "Seleccionar o arrastrar tu hoja de vida";
    $("nombrePdf")
        .closest(".archivo-zona")
        .classList.toggle("con-archivo", Boolean(archivo) && validadores.hojaVida() === "");
}

/** Deja la interfaz como al inicio (se ejecuta después de reiniciar el formulario). */
function restablecerInterfaz() {
    tocados.clear();
    Object.keys(validadores).forEach(limpiarError);
    cargarMunicipios("");
    alternarExperiencia(false);
    actualizarVistaFoto();
    actualizarNombrePdf();
    actualizarContador();
    ocultarEstado();
}

/* ---------- Eventos ---------- */

function manejarCambio(evento) {
    const el = evento.target;
    const nombre = el.name;
    if (!(nombre in validadores)) return;

    // Solo números en DPI y teléfono, con su longitud máxima
    if (nombre === "dpi") el.value = el.value.replace(/\D/g, "").slice(0, LONGITUD_DPI);
    if (nombre === "telefono") el.value = el.value.replace(/\D/g, "").slice(0, LONGITUD_TELEFONO);

    // Efectos secundarios según el campo
    if (nombre === "departamento") {
        cargarMunicipios(el.value);
        if (tocados.has("municipio")) validarCampo("municipio");
    }
    if (nombre === "experiencia") alternarExperiencia(el.value === "si");
    if (nombre === "fechaInicio") {
        formulario.elements.fechaFin.min = el.value;
        if (tocados.has("fechaFin")) validarCampo("fechaFin");
    }
    if (nombre === "funciones") actualizarContador();
    if (nombre === "fotografia") actualizarVistaFoto();
    if (nombre === "hojaVida") actualizarNombrePdf();

    // Opciones, casillas, archivos y listas se validan apenas cambian
    const validarYa = ["radio", "checkbox", "file"].includes(el.type) || el.tagName === "SELECT";
    if (validarYa && evento.type === "change") tocados.add(nombre);

    if (tocados.has(nombre)) validarCampo(nombre);
}

formulario.addEventListener("input", manejarCambio);
formulario.addEventListener("change", manejarCambio);

// Al salir de un campo de texto se valida (evita errores prematuros en radios y casillas)
formulario.addEventListener("focusout", (evento) => {
    const el = evento.target;
    if (!(el.name in validadores) || ["radio", "checkbox", "file"].includes(el.type)) return;
    tocados.add(el.name);
    validarCampo(el.name);
});

formulario.addEventListener("submit", (evento) => {
    evento.preventDefault();

    const nombres = Object.keys(validadores);
    nombres.forEach((n) => tocados.add(n));
    const invalidos = nombres.filter((n) => !validarCampo(n));

    if (invalidos.length > 0) {
        mostrarEstado(
            invalidos.length === 1
                ? "Hay 1 campo por corregir. Revísalo antes de continuar."
                : `Hay ${invalidos.length} campos por corregir. Revísalos antes de continuar.`
        );
        const primero = elementos(invalidos[0])[0];
        primero.closest(".campo").scrollIntoView({ behavior: "smooth", block: "center" });
        primero.focus({ preventScroll: true });
        return;
    }

    ocultarEstado();
    mostrarConfirmacion();
});

// type="reset" limpia los valores; aquí se limpia el resto de la interfaz
formulario.addEventListener("reset", () => setTimeout(restablecerInterfaz, 0));

/* ---------- Mensaje de confirmación ---------- */

function mostrarConfirmacion() {
    const dialogo = $("dialogoExito");

    $("mensajeExito").textContent =
        `Gracias, ${valor("nombres").split(" ")[0]}. Hemos recibido tus datos y los tendremos en cuenta en nuestros próximos procesos de selección.`;

    const resumen = $("resumenExito");
    resumen.innerHTML = "";
    [
        ["Nombre", `${valor("nombres")} ${valor("apellidos")}`],
        ["Correo", valor("correo")],
        ["Teléfono", `+502 ${valor("telefono")}`],
        ["Hoja de vida", formulario.elements.hojaVida.files[0].name]
    ].forEach(([etiqueta, texto]) => {
        const fila = document.createElement("div");
        const dt = document.createElement("dt");
        const dd = document.createElement("dd");
        dt.textContent = etiqueta;
        dd.textContent = texto;
        dd.title = texto;
        fila.append(dt, dd);
        resumen.append(fila);
    });

    // Aquí se enviarían los datos al servidor, por ejemplo:
    // fetch("/api/solicitudes", { method: "POST", body: new FormData(formulario) });

    if (typeof dialogo.showModal === "function") dialogo.showModal();
    else dialogo.setAttribute("open", "");
}

$("btnCerrarExito").addEventListener("click", () => $("dialogoExito").close());

// Al cerrar el mensaje (botón o tecla Esc) el formulario queda listo para una nueva solicitud
$("dialogoExito").addEventListener("close", () => {
    formulario.reset();
    window.scrollTo({ top: 0, behavior: "smooth" });
});

/* ---------- Inicio ---------- */

cargarDepartamentos();
cargarMunicipios("");
$("fechaNacimiento").max = hoyISO();
$("fechaInicio").max = hoyISO();
$("fechaFin").max = hoyISO();
$("anioGraduacion").max = new Date().getFullYear();
actualizarContador();
/* ══ Datos: el banco oficial (data/qir.json, lo genera la GitHub Action) o, si aún no existe, un DEMO marcado como ficticio ══ */
const ASIGS_BASE = [
  ['quimica_general', 'Química general'], ['quimica_inorganica', 'Química inorgánica'], ['quimica_organica', 'Química orgánica'], ['fisicoquimica', 'Fisicoquímica y Termodinámica'], ['quimica_analitica', 'Química analítica'], ['tecnicas', 'Técnicas instrumentales'], ['bioquimica', 'Bioquímica y Metabolismo'], ['biologia_molecular', 'Genética y Biología molecular'], ['bioquimica_clinica', 'Bioquímica clínica y Análisis clínicos'], ['microbiologia', 'Microbiología'], ['inmunologia', 'Inmunología'], ['hematologia', 'Hematología'], ['fisiologia', 'Fisiología y Fisiopatología'], ['farmacologia', 'Farmacología y Toxicología'], ['estadistica', 'Bioestadística, Calidad y Gestión del laboratorio'],
  ['otras', 'Sin clasificar']
].map(([id, nombre]) => ({id, nombre}));

/* DEMO · preguntas ESCRITAS PARA LA DEMOSTRACIÓN (no son preguntas oficiales del QIR); sirven para probar la app sin datos */
const DEMO_PREG = [
  ["quimica_general", "¿Cuál es la geometría molecular del amoniaco (NH3) según la teoría de repulsión de pares electrónicos (VSEPR)?", ["Plana trigonal.", "Pirámide trigonal.", "Tetraédrica.", "Lineal."], 2],
  ["quimica_general", "¿Cuántos moles de agua hay en 36 g de agua (masa molar 18 g/mol)?", ["0,5 moles.", "1 mol.", "2 moles.", "18 moles."], 3],
  ["quimica_inorganica", "¿Cuál es el número de coordinación del ion metálico en el complejo [Co(NH3)6]3+?", ["3.", "4.", "6.", "9."], 3],
  ["quimica_organica", "Un haloalcano primario reacciona con un nucleófilo fuerte en un disolvente aprótico polar. ¿Qué mecanismo es el más probable?", ["Sustitución nucleófila unimolecular (SN1).", "Sustitución nucleófila bimolecular (SN2).", "Eliminación unimolecular (E1).", "Adición electrófila."], 2],
  ["quimica_organica", "¿Qué grupo funcional se obtiene al oxidar suavemente un alcohol primario?", ["Una cetona.", "Un aldehído.", "Un éter.", "Una amina."], 2],
  ["fisicoquimica", "Según la ecuación de Arrhenius, si aumenta la temperatura, la constante de velocidad de una reacción:", ["Disminuye.", "No cambia.", "Aumenta.", "Solo cambia si hay un catalizador."], 3],
  ["fisicoquimica", "Un proceso es espontáneo a temperatura y presión constantes cuando:", ["La variación de energía libre de Gibbs es negativa.", "La variación de entalpía es positiva.", "La variación de entropía es negativa.", "La variación de energía libre de Gibbs es positiva."], 1],
  ["quimica_analitica", "¿Cuál es el pH de una disolución acuosa 0,01 M de ácido clorhídrico a 25 °C?", ["1.", "2.", "7.", "12."], 2],
  ["tecnicas", "Según la ley de Lambert-Beer, la absorbancia de una disolución es directamente proporcional a:", ["La transmitancia.", "La concentración del analito y la longitud del paso óptico.", "El cuadrado de la concentración del analito.", "La longitud de onda de la radiación."], 2],
  ["bioquimica", "¿En qué compartimento de la célula eucariota tiene lugar el ciclo de Krebs?", ["En el citosol.", "En la matriz mitocondrial.", "En el retículo endoplasmático.", "En la membrana mitocondrial externa."], 2],
  ["inmunologia", "¿Qué inmunoglobulina interviene principalmente en las reacciones de hipersensibilidad de tipo I?", ["IgG.", "IgM.", "IgA.", "IgE."], 4],
  ["estadistica", "En la evaluación de una prueba diagnóstica, ¿cómo se define la sensibilidad?", ["Proporción de sanos con resultado negativo.", "Proporción de positivos que están realmente enfermos.", "Proporción de enfermos con resultado positivo.", "Proporción de negativos que están realmente sanos."], 3]
].map(([asig, enunciado, opciones, correcta], i) => ({id: 'demo-' + (i + 1), anio: 0, n: i + 1, asig, enunciado, opciones, correcta, anulada: false, imagen: false, demo: true}));

/* DEMO · recuentos FICTICIOS de 2015 a 2026 (no son datos reales): solo para ver la predicción funcionando */
function demoConteos() {
  const base = {"quimica_general": 14, "quimica_inorganica": 12, "quimica_organica": 22, "fisicoquimica": 20, "quimica_analitica": 18, "tecnicas": 14, "bioquimica": 22, "biologia_molecular": 12, "bioquimica_clinica": 14, "microbiologia": 10, "inmunologia": 10, "hematologia": 8, "fisiologia": 8, "farmacologia": 6, "estadistica": 10};
  const r = rng('demo-oraculoqir'), c = {};
  for (let y = 2015; y <= 2026; y++) {
    c[y] = {};
    for (const k in base) { const tr = k === 'bioquimica_clinica' ? (y - 2015) * 0.35 : k === 'quimica_inorganica' ? -(y - 2015) * 0.25 : 0; c[y][k] = Math.max(0, Math.round(base[k] * 1.05 + tr + (r() - 0.5) * 5)); }
  }
  return c;
}

let DATA = {real: false, asignaturas: ASIGS_BASE, preguntas: DEMO_PREG, conteos: demoConteos(), examenes: [], generado: null};
const nombreAsig = id => t((DATA.asignaturas.find(a => a.id === id) || {nombre: id}).nombre);
/* Carga data/qir.json (mismo origen, en GitHub Pages). Abierta como fichero local o sin datos todavía → DEMO */
async function cargaDatos() {
  try {
    const r = await fetch('data/qir.json', {cache: 'no-cache'});
    if (!r.ok) throw 0;
    const j = await r.json();
    const ps = (j.preguntas || []).filter(q => q && q.enunciado && q.anio);
    if (ps.length < 100) throw 0;
    DATA = {real: true, asignaturas: j.asignaturas || ASIGS_BASE, preguntas: ps, conteos: conteos(ps), examenes: j.examenes || [], generado: j.generado || null, clasificacion: j.clasificacion || ''};
    try { const a = await (await fetch('data/asignaturas.json', {cache: 'no-cache'})).json(); DATA.kws = Object.fromEntries((a.asignaturas || []).map(x => [x.id, x.kw || []])); } catch { DATA.kws = {}; }
  } catch { /* se queda el DEMO */ }
  return DATA;
}

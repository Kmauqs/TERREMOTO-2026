# Terremoto del 10 de agosto de 2026 — Eje Cafetero (Colombia)

Repositorio de acelerogramas, espectros y productos derivados del sismo **SGC2026pqqmro**, obtenidos del [Servicio Geológico Colombiano (SGC)](https://www2.sgc.gov.co/) y post-procesados para análisis de demanda sísmica en ingeniería estructural.

---

## 1. Resumen del sismo

| Parámetro | Valor |
|-----------|-------|
| **Código de evento** | SGC2026pqqmro |
| **Fecha y hora (UTC)** | 2026-08-10 · 12:34:27 |
| **Magnitud** | **M 7.4** |
| **Epicentro** | San José del Palmar, Chocó |
| **Latitud / Longitud** | 4.99° N / −76.293° W |
| **Profundidad** | 103 km |
| **Región tectónica** | Subducción — **intraslab** (probabilidad ~1.0 según STREC/ShakeMap SGC) |
| **Área de interés** | Eje Cafetero (Quindío, Risaralda, Caldas) y municipios aledaños |
| **Estaciones RNAC con forma de onda en este repo** | 8 (ARMEC, CBOCA, CCALA, CIRS, CTRUJ, FLND, MAN1C, SLNT) |
| **Estaciones con PGA reportado por SGC** | 79 (tabla completa) |

El evento corresponde a un sismo profundo de placa, con distancias epicentrales típicamente de 75–90 km a las estaciones del Eje Cafetero compiladas aquí. Las PGA horizontales en estaciones confiables del área de estudio alcanzan demandas elevadas (p. ej. FLND y CIRS, PGA horizontal > 0.3 g), coherentes con la severidad del movimiento en el corredor cafetero.

Productos oficiales de intensidad instrumental (ShakeMap) incluidos en `SGC-Data/` reportan, a escala regional, PGA máximos de grilla del orden de ~0.3 g y SA(0.3) hasta ~0.55 g (versión automática del mapa).

> **Observación — estación CBOCA (Pereira):** los amplitudes registrados en CBOCA (PGA horizontal ≈ 0.04 g) constituyen un **dato atípico** respecto a la atenuación/propagación esperada del sismo y, sobre todo, respecto a los **daños reales evidenciados en Pereira**, ciudad entre las más afectadas por el evento. Existen indicios de que la estación podría estar **defectuosa** o de que el registro no es representativo del movimiento fuerte en el área urbana. **No se recomienda emplear los datos de CBOCA** en análisis estadísticos, ajustes de atenuación, validación de GMPE ni modelaciones detalladas de demanda sísmica. El acelerograma se conserva en el repositorio solo como archivo fuente SGC, claramente marcado como no confiable.

---

## 2. Información recopilada del Servicio Geológico Colombiano

Tabla de productos descargados o derivados directamente de fuentes SGC / RNAC, con vínculos a los archivos del repositorio.

| Producto | Descripción | Ubicación en el repositorio |
|----------|-------------|-----------------------------|
| Acelerograma ANC — ARMEC | Armenia (Quindío); Δt = 0.005 s; EW–VER–NS | [SGC2026pqqmro_ARMEC_10.anc](SGC-Data/SGC2026pqqmro_ARMEC_10.anc) |
| Acelerograma ANC — CBOCA | Pereira / Bocatoma (Risaralda) — **dato atípico / no usar en análisis** (ver observación §1) | [SGC2026pqqmro_CBOCA_10.anc](SGC-Data/SGC2026pqqmro_CBOCA_10.anc) · [txt](SGC-Data/SGC2026pqqmro_CBOCA_10.txt) |
| Acelerograma ANC — CCALA | Calarcá (Quindío) | [SGC2026pqqmro_CCALA_10.anc](SGC-Data/SGC2026pqqmro_CCALA_10.anc) |
| Acelerograma ANC — CIRS | Circasia (Quindío) | [SGC2026pqqmro_CIRS_10.anc](SGC-Data/SGC2026pqqmro_CIRS_10.anc) |
| Acelerograma ANC — CTRUJ | Trujillo (Valle); Δt = 0.01 s | [SGC2026pqqmro_CTRUJ_10.anc](SGC-Data/SGC2026pqqmro_CTRUJ_10.anc) |
| Acelerograma ANC — FLND | Filandia (Quindío) | [SGC2026pqqmro_FLND_10.anc](SGC-Data/SGC2026pqqmro_FLND_10.anc) |
| Acelerograma ANC — MAN1C | Manizales (Caldas) | [SGC2026pqqmro_MAN1C_10.anc](SGC-Data/SGC2026pqqmro_MAN1C_10.anc) |
| Acelerograma ANC — SLNT | Salento (Quindío) | [SGC2026pqqmro_SLNT_10.anc](SGC-Data/SGC2026pqqmro_SLNT_10.anc) |
| MiniSEED (formas de onda) | Registros auxiliares en formato MiniSEED | [SGC-Data/](SGC-Data/) (`*.mseed`) |
| Tabla estaciones–PGA | Localización y PGA EW/NS/Z reportados por SGC (79 estaciones) | [table-Estaciones-Localizacion-PGA.csv](Espectros/table-Estaciones-Localizacion-PGA.csv) · [copia SGC-Data](SGC-Data/table-Estaciones-Localizacion-PGA.csv) |
| Espectros SGC (PSA 5 %) | Gráficos oficiales de pseudoaceleración por estación | [Espectros/\*_PSA5.png](Espectros/) |
| Espectros SGC (DRS 5 %) | Gráficos oficiales de desplazamiento espectral por estación | [Espectros/\*_DRS5.png](Espectros/) |
| PSA tabular (ejemplo CIRS) | Serie PSA 5 % exportada | [CIRS_10_PSA5.csv](Espectros/CIRS_10_PSA5.csv) |
| Generalidades SGC | PDF de aceleraciones / contexto del evento | [SGC - Sismo Generalidades-Aceleraciones estacion.pdf](Espectros/SGC%20-%20Sismo%20Generalidades-Aceleraciones%20estacion.pdf) |
| ShakeMap — metadatos | Origen, GMPE, sesgos, PGA/PGV/SA de grilla | [info.json](SGC-Data/info.json) |
| ShakeMap — estaciones | FeatureCollection con amplitudes por canal | [stationlist.json](SGC-Data/stationlist.json) |
| ShakeMap — grilla | Campo de moción del suelo | [grid.xml](SGC-Data/grid.xml) |
| ShakeMap — incertidumbre | Campo de incertidumbre | [uncertainty.xml](SGC-Data/uncertainty.xml) |

**Productos derivados en este proyecto** (no oficiales SGC): señales corregidas y filtradas, espectros recalculados y factores de sitio — ver carpetas [`output/senales/`](output/senales/), [`output/espectros/`](output/espectros/) e informe HTML [`index.html`](index.html).

---

## 3. Metodología de procesamiento de señales

### 3.1 Resumen técnico

Sobre los acelerogramas `.ANC` (aceleración en cm/s², componentes EW, VER y NS) se aplicó la siguiente cadena, implementada en Python con **ObsPy**, **NumPy**, **SciPy** y **Numba**:

1. **Corrección de línea base:** remoción de media (demean), detrend lineal por mínimos cuadrados y ventana coseno (taper 5 %) para forzar extremos ≈ 0 y evitar integración espuria a velocidad/desplazamiento.
2. **Filtrado pasabanda:** Butterworth de 4 polos, banda **0.10–25 Hz**, aplicado en fase cero (`filtfilt`), orientado a conservar el contenido frecuencial relevante para edificaciones y atenuar ruido de muy baja y muy alta frecuencia.
3. **Espectro de respuesta elástico:** oscilador SDOF lineal viscoso con **ζ = 5 %**; integración exacta **Nigam–Jennings (1969)** para \(T = 0\)–\(4\) s (ΔT = 0.01 s). Se reportan \(S_a\), \(S_v\), \(S_d\) y PSA, más la media geométrica horizontal EW–NS.

Documentación detallada: **[docs/metodos_procesamiento_y_espectro.md](docs/metodos_procesamiento_y_espectro.md)**  
Código ejecutable: **[procesar_sismo.py](procesar_sismo.py)**

```bash
python procesar_sismo.py
```

### 3.2 Parámetros e información no incorporados (limitaciones de datos)

Los siguientes aspectos **no se corrigieron ni modelaron** por ausencia o insuficiencia de información en los entregables SGC disponibles:

| Aspecto omitido | Motivo |
|-----------------|--------|
| Función de transferencia / respuesta instrumental | Campo `TIPO DE EQUIPO` vacío o no especificado en los `.ANC` |
| Deconvolución a roca aflorante | Sin perfiles \(V_S(z)\) ni \(V_{S30}\) medidos en cada estación RNAC usada |
| RotD50 / RotD100 por rotación azimutal | No se rotó el par horizontal; se usó media geométrica EW–NS como proxy |
| Corrección por orientación de sensores | Sin metadatos de azimuth de componentes más allá de EW/NS |
| Respuesta no lineal de sitio / degradación de módulo | Requiere ensayo dinámico y modelo constitutivo de suelo; no disponible |
| Geometría de ruptura y directividad | ShakeMap sin falla finita explícita utilizable en este flujo |
| Condiciones de cimentación / caja del instrumento | Sin fichas geotécnicas de instalación |
| Comparación formal SGC vs. espectro propio | Los PSA/DRS oficiales se archivan como referencia visual; el pipeline recalcula espectro de forma independiente |
| Uso de CBOCA como estación representativa de Pereira | Registro atípico frente a daños observados; posible defecto instrumental — **excluir de análisis estadísticos y modelaciones** |

Estas omisiones deben considerarse al usar los espectros para diseño o verificación: el movimiento procesado es el **registrado en la estación**, no necesariamente el de un predio con geología local distinta.

---

## 4. Factores de amplificación por efectos de sitio (resumen)

Factores centrales recomendados para escalar un espectro base en roca/basamento, \(S_{a,\mathrm{sitio}}(T) = F_a(T)\,S_{a,\mathrm{base}}(T)\), orientados a condiciones típicas del Eje Cafetero:

| Condición de sitio | Fa(PGA) | Fa(0.3 s) | Fa(1.0 s) | Fa(3.0 s) | Fv* |
|--------------------|--------:|----------:|----------:|----------:|----:|
| Roca / basamento de referencia | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Corona de laderas | 1.35 | 1.40 | 1.15 | 1.05 | 1.10 |
| Pie de laderas | 1.25 | 1.45 | 1.50 | 1.35 | 1.40 |
| Cenizas volcánicas de bajo espesor (recientes) | 1.40 | 1.70 | 1.25 | 1.05 | 1.15 |
| Cenizas de espesor intermedio/alto (gel siloxano) | 1.55 | 2.10 | 2.00 | 1.60 | 1.90 |
| Depósitos fluvio-lacustres | 1.45 | 1.80 | 2.20 | 2.00 | 2.10 |
| Depósitos fluviotorrenciales (Formación Quindío) | 1.50 | 1.90 | 1.75 | 1.40 | 1.65 |
| Llenos antrópicos | 1.60 | 2.00 | 1.85 | 1.50 | 1.75 |

Guía completa (rangos, interpolación en \(T\), correspondencia NSR-10 y procedimiento de aplicación):  
**[docs/guia_amplificacion_efectos_sitio.md](docs/guia_amplificacion_efectos_sitio.md)** · datos tabulares: [output/factores_amplificacion_sitio.csv](output/factores_amplificacion_sitio.csv)

> Estos factores son **orientativos de ingeniería** y no sustituyen la microzonificación municipal ni un estudio de respuesta de sitio 1D/2D con perfil medido.

---

## 5. Estructura del repositorio

```text
TERREMOTO-2026/
├── SGC-Data/           # Acelerogramas ANC/MiniSEED y ShakeMap SGC
├── Espectros/          # PSA/DRS oficiales SGC (PNG) + tabla PGA
├── output/
│   ├── senales/        # Aceleración corregida/filtrada (CSV, MiniSEED)
│   └── espectros/      # Espectros elásticos recalculados (CSV)
├── docs/               # Metodología y guía de amplificación
├── procesar_sismo.py   # Pipeline de procesamiento
├── index.html          # Informe HTML (tabla estaciones + gráficos SGC)
└── README.md
```

---

## 6. Referencias

1. Servicio Geológico Colombiano (SGC). Red Nacional de Acelerógrafos de Colombia (RNAC). Acelerogramas y espectros del evento **SGC2026pqqmro** (2026-08-10).  
2. Servicio Geológico Colombiano. ShakeMap — metadatos y grillas de moción del suelo (`info.json`, `grid.xml`, `stationlist.json`, `uncertainty.xml`), evento SGC2026pqqmro.  
3. Nigam, N. C. & Jennings, P. C. (1969). *Calculation of Response Spectra from Strong-Motion Earthquake Records.* Bulletin of the Seismological Society of America, 59(2), 909–922.  
4. Butterworth, S. (1930). *On the Theory of Filter Amplifiers.* Wireless Engineer.  
5. Boore, D. M. Trabajos sobre corrección de línea base y filtrado de acelerogramas de movimiento fuerte.  
6. Chopra, A. K. *Dynamics of Structures.* Espectro de respuesta y dinámica de sistemas de un grado de libertad.  
7. The ObsPy Development Team. ObsPy: A Python Framework for Seismology.  
8. Asociación Colombiana de Ingeniería Sísmica (AIS). **NSR-10** — Reglamento Colombiano de Construcción Sismo Resistente, Título A (amenaza, coeficientes de sitio Fa, Fv).  
9. INGEOMINAS / SGC. Estudios de microzonificación sísmica y respuesta de sitio en el Eje Cafetero (Armenia y municipios vecinos), con énfasis en cenizas volcánicas y Formación Quindío.  
10. Documentación interna del proyecto: [metodos_procesamiento_y_espectro.md](docs/metodos_procesamiento_y_espectro.md), [guia_amplificacion_efectos_sitio.md](docs/guia_amplificacion_efectos_sitio.md).

---

*Informe técnico de datos y procesamiento — uso en evaluación de demanda sísmica. Para diseño reglamentario prevalecen NSR vigente y la microzonificación oficial del municipio.*

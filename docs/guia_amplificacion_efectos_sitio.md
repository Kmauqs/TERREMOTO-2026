# Guía de amplificación espectral por efectos de sitio — Eje Cafetero

**Evento de referencia:** SGC2026pqqmro · 10 de agosto de 2026 · M 7.4 · San José del Palmar (Chocó)  
**Uso:** factores para escalar el espectro de respuesta elástico de roca / registro de estación (`Sa_sitio(T) = Fa_sitio(T) · Sa_base(T)`).  
**Amortiguamiento de referencia:** ζ = 5 %.

---

## 1. Alcance y precauciones

Los factores de esta guía son **orientativos de ingeniería** para el Eje Cafetero (depósitos volcánicos, fluviotorrenciales y morfología de ladera). Se sintetizan a partir de:

- NSR-10 (Título A) — coeficientes de sitio `Aa`, `Av`, `Fa`, `Fv` (marco normativo nacional).
- Microzonificaciones y estudios locales (Armenia–Quindío post-1999, Manizales, Pereira–Dosquebradas).
- Comportamiento conocido de cenizas volcánicas meteorizadas con estructura de **gel siloxano** (alta plasticidad, Vs bajas, amplificación de periodos intermedios).

**No sustituyen** un estudio de respuesta de sitio 1D/2D con perfil Vs medido. Para diseño oficial usar NSR vigente + microzonificación municipal aprobada.

**Espectro base recomendado:** media geométrica horizontal (`Sa_RotD50_approx_g` o `PSA_geo_mean_g`) de la estación más representativa del basamento cercano, o espectro de amenaza uniforme en roca (suelo tipo B, Vs30 ≈ 760 m/s).

---

## 2. Definición de factores

| Símbolo | Significado |
|--------|-------------|
| `Fa_PGA` | Amplificación del PGA (T ≈ 0) respecto a roca/basamento |
| `Fa_0.3` | Amplificación de Sa en T = 0.3 s |
| `Fa_1.0` | Amplificación de Sa en T = 1.0 s |
| `Fa_3.0` | Amplificación de Sa en T = 3.0 s |
| `T_pico_sitio` | Periodo donde suele concentrarse el pico de amplificación |
| `Fv*` | Factor tipo “velocidad” (periodos largos), análogo a Fv NSR-10 |

Interpolación sugerida entre nodos (T en segundos):

```
Fa(T) = Fa_PGA                         si T ≤ 0.05
Fa(T) = interp(Fa_PGA, Fa_0.3)         si 0.05 < T ≤ 0.3
Fa(T) = interp(Fa_0.3, Fa_1.0)         si 0.3 < T ≤ 1.0
Fa(T) = interp(Fa_1.0, Fa_3.0)         si 1.0 < T ≤ 3.0
Fa(T) = Fa_3.0                         si 3.0 < T ≤ 4.0
```

(usar interpolación lineal en T, o log-lineal en Sa si se prefiere suavizado).

---

## 3. Parámetros por condición de sitio

Valores centrales y rangos típicos **relativos a roca dura / basamento volcánico sano** (Fa ≈ 1.0).

### 3.1 Corona de laderas

Topografía convexa (crestas, filos). Amplificación topográfica + posible desamplificación de periodos muy largos.

| Parámetro | Valor central | Rango típico | Notas |
|-----------|---------------|--------------|-------|
| Fa_PGA | **1.35** | 1.2 – 1.6 | Pico en altas frecuencias |
| Fa_0.3 | **1.40** | 1.2 – 1.7 | |
| Fa_1.0 | **1.15** | 1.0 – 1.3 | |
| Fa_3.0 | **1.05** | 0.9 – 1.2 | |
| T_pico_sitio | 0.15 – 0.35 s | | Efecto topográfico |
| Fv* | **1.10** | 1.0 – 1.25 | |

**Riesgo asociado:** concentraciones de daño en bordes de meseta; acoplar con evaluación de estabilidad de ladera.

---

### 3.2 Pie de laderas

Zona de transición depósito–ladera; posibles trampas de ondas y suelos coluviales blandos.

| Parámetro | Valor central | Rango típico | Notas |
|-----------|---------------|--------------|-------|
| Fa_PGA | **1.25** | 1.1 – 1.5 | |
| Fa_0.3 | **1.45** | 1.2 – 1.8 | |
| Fa_1.0 | **1.50** | 1.2 – 1.9 | Amplificación de periodos medios |
| Fa_3.0 | **1.35** | 1.1 – 1.7 | |
| T_pico_sitio | 0.4 – 0.9 s | | |
| Fv* | **1.40** | 1.2 – 1.7 | |

**Riesgo asociado:** focos de daño en abanicos coluviales; humedad y espesor variables.

---

### 3.3 Cenizas volcánicas de bajo espesor (recientes)

Mantos de ceniza / lapilli recientes, espesor típico **&lt; 5–8 m** sobre basamento más rígido.

| Parámetro | Valor central | Rango típico | Notas |
|-----------|---------------|--------------|-------|
| Fa_PGA | **1.40** | 1.2 – 1.7 | Resonancia de capa delgada |
| Fa_0.3 | **1.70** | 1.4 – 2.2 | Pico corto–intermedio |
| Fa_1.0 | **1.25** | 1.0 – 1.5 | |
| Fa_3.0 | **1.05** | 0.9 – 1.2 | |
| T_pico_sitio | 0.2 – 0.5 s | ≈ 4H/Vs | H = espesor |
| Fv* | **1.15** | 1.0 – 1.35 | |

**Riesgo asociado:** edificaciones bajas y medianas (1–5 pisos) en resonancia con la capa.

---

### 3.4 Cenizas volcánicas de espesor intermedio o alto  
*(depósitos meteorizados con estructura de gel siloxano)*

Cenizas antiguas alteradas, alta porosidad, comportamiento cohesivo–plástico; Vs30 frecuentemente **180–360 m/s**. Históricamente asociadas a daño severo en Armenia (1999) y zonas análogas del Quindío / norte del Valle / Caldas.

| Parámetro | Valor central | Rango típico | Notas |
|-----------|---------------|--------------|-------|
| Fa_PGA | **1.55** | 1.3 – 2.0 | |
| Fa_0.3 | **2.10** | 1.7 – 2.8 | Fuerte amplificación |
| Fa_1.0 | **2.00** | 1.5 – 2.6 | Periodos de edificaciones medias–altas |
| Fa_3.0 | **1.60** | 1.2 – 2.1 | |
| T_pico_sitio | 0.5 – 1.5 s | Crece con espesor | |
| Fv* | **1.90** | 1.5 – 2.4 | Análogo a suelos blandos NSR |

**Riesgo asociado:** máximo interés para el Eje Cafetero; degradación de rigidez con ciclado; posible licuación cíclica / asentamiento en saturación.

---

### 3.5 Depósitos fluvio-lacustres

Rellenos de cuenca, limos y arcillas lacustres, niveles freáticos altos.

| Parámetro | Valor central | Rango típico | Notas |
|-----------|---------------|--------------|-------|
| Fa_PGA | **1.45** | 1.2 – 1.8 | |
| Fa_0.3 | **1.80** | 1.4 – 2.3 | |
| Fa_1.0 | **2.20** | 1.7 – 2.8 | Dominio de periodos largos |
| Fa_3.0 | **2.00** | 1.5 – 2.6 | |
| T_pico_sitio | 0.8 – 2.5 s | | |
| Fv* | **2.10** | 1.7 – 2.6 | |

**Riesgo asociado:** edificaciones altas y sistemas flexibles; asentamientos diferenciales.

---

### 3.6 Depósitos fluviotorrenciales (Formación Quindío)

Abanicos y flujos de escombros volcanoclásticos (matriz limo–arcillosa + clastos); muy extendidos en Armenia, Calarcá, Circasia, Montenegro y corredores vecinos.

| Parámetro | Valor central | Rango típico | Notas |
|-----------|---------------|--------------|-------|
| Fa_PGA | **1.50** | 1.25 – 1.9 | Heterogeneidad lateral alta |
| Fa_0.3 | **1.90** | 1.5 – 2.5 | |
| Fa_1.0 | **1.75** | 1.3 – 2.3 | |
| Fa_3.0 | **1.40** | 1.1 – 1.9 | |
| T_pico_sitio | 0.35 – 1.0 s | Depende de facies | |
| Fv* | **1.65** | 1.3 – 2.1 | |

**Riesgo asociado:** variabilidad de sitio a sitio; no extrapolable sin control geotécnico local. Facies de matriz fina se acercan al caso 3.4.

---

### 3.7 Llenos antrópicos

Rellenos no ingenieriles, escombros, suelos compactados deficientemente, espesores irregulares.

| Parámetro | Valor central | Rango típico | Notas |
|-----------|---------------|--------------|-------|
| Fa_PGA | **1.60** | 1.3 – 2.2 | Muy variable |
| Fa_0.3 | **2.00** | 1.5 – 2.8 | |
| Fa_1.0 | **1.85** | 1.3 – 2.5 | |
| Fa_3.0 | **1.50** | 1.1 – 2.1 | |
| T_pico_sitio | 0.3 – 1.2 s | | |
| Fv* | **1.75** | 1.3 – 2.3 | |

**Riesgo asociado:** además de amplificación: fallas de apoyo, asentamientos y daño no estructural. Priorizar caracterización in situ; factores anteriores son **límites inferiores de precaución**, no de diseño fino.

---

## 4. Tabla resumen (valores centrales)

| Condición de sitio | Fa_PGA | Fa_0.3 | Fa_1.0 | Fa_3.0 | Fv* | T_pico (s) |
|--------------------|-------:|-------:|-------:|-------:|----:|------------|
| Roca / basamento de referencia | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | — |
| Corona de laderas | 1.35 | 1.40 | 1.15 | 1.05 | 1.10 | 0.15–0.35 |
| Pie de laderas | 1.25 | 1.45 | 1.50 | 1.35 | 1.40 | 0.4–0.9 |
| Cenizas bajo espesor (recientes) | 1.40 | 1.70 | 1.25 | 1.05 | 1.15 | 0.2–0.5 |
| Cenizas intermedio/alto (gel siloxano) | 1.55 | 2.10 | 2.00 | 1.60 | 1.90 | 0.5–1.5 |
| Fluvio-lacustres | 1.45 | 1.80 | 2.20 | 2.00 | 2.10 | 0.8–2.5 |
| Fluviotorrenciales (Fm. Quindío) | 1.50 | 1.90 | 1.75 | 1.40 | 1.65 | 0.35–1.0 |
| Llenos antrópicos | 1.60 | 2.00 | 1.85 | 1.50 | 1.75 | 0.3–1.2 |

Archivo tabular: `output/factores_amplificacion_sitio.csv`.

---

## 5. Procedimiento de aplicación a los CSV de este proyecto

1. Elegir estación base (p. ej. la de menor amplificación aparente o espectro en roca de amenaza).
2. Leer `output/espectros/<ESTACION>_espectro_respuesta_elastico.csv`.
3. Usar columna `PSA_geo_mean_g` (o `Sa_RotD50_approx_g`) como `Sa_base(T)`.
4. Identificar la condición de sitio del predio (geología + morfología + espesor).
5. Obtener `Fa(T)` por interpolación (§2) desde la fila correspondiente (§4).
6. Calcular `Sa_sitio(T) = Fa(T) · Sa_base(T)` para T ∈ [0, 4] s.
7. Para combinación con NSR-10: verificar que el espectro amplificado no sea menor que el espectro de diseño normativo del municipio (tomar envolvente).

**Ejemplo rápido (T = 1.0 s, ceniza gel siloxano):**  
`Sa_sitio(1.0) = 2.00 · Sa_base(1.0)`.

---

## 6. Correspondencia aproximada con NSR-10 (orientativa)

| Condición local | Perfil NSR-10 más cercano | Comentario |
|-----------------|---------------------------|------------|
| Roca / basamento | B | Vs30 ≳ 760 m/s |
| Corona ladera (roca/suelo rígido) | B–C | Sumar factor topográfico |
| Ceniza delgada | C | |
| Fm. Quindío (matriz densa) | C–D | Facies dependiente |
| Ceniza gel siloxano / pie de ladera blando | D | A menudo D |
| Fluvio-lacustre / lleno suelto | D–E | E si Vs30 muy bajo |

Los `Fa`, `Fv` oficiales dependen de `Aa`, `Av` del municipio; usar tablas A.2.4-3 y A.2.4-4 de NSR-10 para diseño reglamentario.

---

## 7. Estaciones procesadas en este repositorio

| Código | Ubicación aprox. | Lat | Lon | Repi (km) |
|--------|------------------|-----|-----|-----------|
| ARMEC | Armenia / área metro | 4.556 | -75.660 | 85 |
| CCALA | Calarcá | 4.509 | -75.628 | 91 |
| CBOCA | Zona Bocatoma / corredor Pereira–Armenia | 4.782 | -75.646 | 75 |
| CIRS | Circasia | 4.643 | -75.606 | 85 |
| CTRUJ | Trujillo (Valle) | 4.219 | -76.322 | 86 |
| FLND | Filandia | 4.686 | -75.619 | 82 |
| MAN1C | Manizales | 5.071 | -75.524 | 85 |
| SLNT | Salento | 4.637 | -75.570 | 89 |

Las estaciones RNAC suelen estar en sitios relativamente controlados; **no** representan automáticamente el sitio de un edificio en ceniza o lleno. Por eso se aplican los factores de esta guía al espectro registrado o al de amenaza en roca.

---

## 8. Referencias de apoyo (consulta)

1. AIS / NSR-10 — Reglamento Colombiano de Construcción Sismo Resistente, Título A.  
2. INGEOMINAS / SGC — Microzonificación sísmica de Armenia y estudios del Eje Cafetero.  
3. Estudios de respuesta de sitio en cenizas volcánicas del Quindío (comportamiento de geles siloxanos / suelos residuales volcánicos).  
4. ShakeMap SGC evento `SGC2026pqqmro` (metadatos en `SGC-Data/info.json`).

---

*Documento generado para el procesamiento del sismo del 10-ago-2026. Revisar con ingeniero geotecnista / sismólogo local antes de uso en diseño.*

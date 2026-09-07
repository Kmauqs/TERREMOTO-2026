# Métodos y modelos de procesamiento de señal y espectro de respuesta

**Proyecto:** Terremoto 10 de agosto de 2026 — Eje Cafetero  
**Evento:** SGC2026pqqmro · M 7.4 · San José del Palmar (Chocó)  
**Implementación:** `procesar_sismo.py` (ObsPy, NumPy, SciPy, Numba)

---

## 1. Objetivo

Documentar los métodos matemáticos y modelos físicos empleados para:

1. Corregir los acelerogramas de la Red Nacional de Acelerógrafos (RNAC / SGC).
2. Filtrar el ruido fuera del rango de interés estructural.
3. Calcular el **espectro de respuesta elástico** para periodos de vibración entre 0 y 4 s.

El flujo produce, por estación, un CSV de aceleración ajustada y un CSV de espectro de respuesta.

---

## 2. Datos de entrada

### 2.1 Formato de registro

Los archivos `.ANC` del Servicio Geológico Colombiano son acelerogramas en texto ASCII con:

| Campo | Descripción |
|-------|-------------|
| Componentes | EW (este–oeste), VER (vertical), NS (norte–sur) |
| Unidades | cm/s² |
| Muestreo típico | Δt = 0.005 s (200 Hz); CTRUJ usa Δt = 0.01 s |
| Duración | ~510 s |
| Etiqueta SGC | “TIPO DE DATOS: NO CORREGIDO” (requiere post-proceso) |

### 2.2 Modelo de la señal bruta

Cada componente se trata como una serie temporal discreta de aceleración del suelo:

\[
a_g[k] = a_g(k\,\Delta t), \quad k = 0,1,\ldots,N-1
\]

No se aplica corrección instrumental de transferencia del sensor en este pipeline: se trabaja directamente con la aceleración reportada por el SGC en cm/s², tras corrección de línea base y filtrado.

### 2.3 Herramientas

| Librería | Uso |
|----------|-----|
| **ObsPy** | Contenedor `Trace`/`Stream`, metadatos, exportación MiniSEED |
| **NumPy / SciPy** | Álgebra, filtro Butterworth, `filtfilt` |
| **Numba** | Aceleración del integrador Nigam–Jennings |

---

## 3. Corrección de línea base (extremos en cero)

### 3.1 Motivación

Un offset o deriva en la aceleración, al integrarse, genera **velocidad y desplazamiento espurios**. El objetivo es una señal que comience y termine cerca de cero, sin alterar el contenido sísmico útil.

### 3.2 Remoción de media (demean)

\[
a^{(1)}[k] = a_g[k] - \bar{a}_g, \qquad \bar{a}_g = \frac{1}{N}\sum_{k=0}^{N-1} a_g[k]
\]

Elimina el sesgo constante (offset de cero del acelerógrafo).

### 3.3 Detrend lineal

Se ajusta una recta por mínimos cuadrados a \(a^{(1)}(t)\) y se resta:

\[
a^{(1)}(t) \approx c_0 + c_1 t \quad\Rightarrow\quad
a^{(2)}(t) = a^{(1)}(t) - (c_0 + c_1 t)
\]

Corrige derivas lentas de línea base incompatibles con un movimiento que debe iniciar y terminar en reposo.

### 3.4 Ventana coseno (taper)

Se multiplica por una ventana que vale 0 en los extremos y 1 en el centro. En cada extremo se usa una fracción \(p = 5\,\%\) de la longitud total:

\[
w[i] =
\begin{cases}
\dfrac{1}{2}\bigl(1 - \cos(\pi i / m)\bigr) & 0 \le i < m \\[6pt]
1 & m \le i < N-m \\[6pt]
\dfrac{1}{2}\bigl(1 - \cos(\pi (N-1-i) / m)\bigr) & N-m \le i < N
\end{cases}
\]

con \(m = \lfloor p\,N\rfloor\). Así:

\[
a^{(3)}[k] = a^{(2)}[k]\, w[k]
\]

Esto fuerza extremos nulos **antes** del filtrado y reduce fugas espectrales (Gibbs) al aplicar el pasabanda.

Tras el filtro se aplica un segundo taper más suave (\(p = 2.5\,\%\)) y una nueva remoción de media residual.

---

## 4. Filtrado de frecuencias

### 4.1 Modelo de filtro: Butterworth pasabanda

Se emplea un filtro **Butterworth de 4 polos**, tipo pasabanda, con bandas de corte:

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| \(f_L\) | 0.10 Hz | Elimina ruido de muy baja frecuencia y deriva residual |
| \(f_H\) | 25 Hz | Elimina ruido de muy alta frecuencia; por encima suele no controlar la respuesta de edificaciones típicas |
| Orden | 4 | Compromiso selectividad / distorsión de fase (mitigada con `filtfilt`) |

La magnitud ideal del Butterworth de orden \(n\) en pasabanda es:

\[
|H(j\omega)| = \frac{1}{\sqrt{1 + \left(\dfrac{\omega^2 - \omega_0^2}{\omega\, B}\right)^{2n}}}
\]

donde \(\omega_0\) y \(B\) definen el centro y el ancho de banda equivalentes a \([f_L,\,f_H]\).

La frecuencia de Nyquist \(f_N = 1/(2\Delta t)\) limita \(f_H\): si hiciera falta, se usa \(\min(25,\,0.45\,f_s)\).

### 4.2 Filtrado de fase cero (`filtfilt`)

En lugar de convolucionar una sola vez (filtro causal), se aplica **adelante y atrás** (`scipy.signal.filtfilt`):

\[
a_{\text{filt}} = \mathcal{F}^{-1}\!\bigl\{ |H(\omega)|^2\, A^{(3)}(\omega) \bigr\}
\quad\text{(equivalente en magnitud; fase neta ≈ 0)}
\]

Ventaja: no desplaza en el tiempo los picos del acelerograma (importante para PGA y sincronismo entre componentes). El orden efectivo en magnitud es el doble del nominal (≈ 8 polos en |H|).

### 4.3 Banda estructural de interés

Para edificaciones con periodos \(T \in [0,\,4]\) s, las frecuencias naturales están en:

\[
f = \frac{1}{T} \in [0.25,\,\infty)~\text{Hz}
\]

La banda 0.1–25 Hz cubre con margen ese rango y suprime:

- **Baja frecuencia:** deriva, ruido ambiental de largo periodo, errores de integración.
- **Alta frecuencia:** ruido electrónico, resonancias instrumentales no estructurales.

---

## 5. Modelo del espectro de respuesta elástico

### 5.1 Oscilador de un grado de libertad (SDOF)

Para cada periodo natural \(T\) y razón de amortiguamiento \(\zeta\), se considera un sistema lineal viscoso forzado por la aceleración del suelo \(a_g(t)\):

\[
\ddot{u}(t) + 2\zeta\omega\,\dot{u}(t) + \omega^2 u(t) = -a_g(t)
\]

donde:

\[
\omega = \frac{2\pi}{T}, \qquad \zeta = 0.05\ \text{(5 \%, estándar en ingeniería sísmica)}
\]

- \(u\): desplazamiento **relativo** masa–base  
- \(\dot{u}\): velocidad relativa  
- Aceleración **absoluta** de la masa: \(\ddot{u}_a = \ddot{u} + a_g = -2\zeta\omega\,\dot{u} - \omega^2 u\)

### 5.2 Definición del espectro

Se barre \(T\) desde 0 hasta 4 s con paso \(\Delta T = 0.01\) s. En cada \(T\):

\[
\begin{aligned}
S_d(T,\zeta) &= \max_t \bigl|u(t)\bigr| \\
S_v(T,\zeta) &= \max_t \bigl|\dot{u}(t)\bigr| \\
S_a(T,\zeta) &= \max_t \bigl|\ddot{u}_a(t)\bigr|
\end{aligned}
\]

Caso límite \(T \to 0\) (estructura infinitamente rígida):

\[
S_a(0) \approx \mathrm{PGA} = \max_t \bigl|a_g(t)\bigr|
\]

También se reporta la **pseudo-aceleración** (común en códigos de diseño):

\[
\mathrm{PSA}(T) = \omega^2 S_d(T)
\]

que coincide aproximadamente con \(S_a\) para \(\zeta\) moderado.

### 5.3 Método de integración: Nigam–Jennings (1969)

Se usa la solución **exacta** del SDOF cuando \(a_g(t)\) se asume **lineal entre muestras** (interpolación lineal por tramos). El estado en el paso \(k+1\) es:

\[
\begin{Bmatrix} u_{k+1} \\ \dot{u}_{k+1} \end{Bmatrix}
=
\mathbf{A}\,
\begin{Bmatrix} u_k \\ \dot{u}_k \end{Bmatrix}
+
\mathbf{B}\,
\begin{Bmatrix} a_g[k] \\ a_g[k+1] \end{Bmatrix}
\]

Las matrices \(\mathbf{A}\) y \(\mathbf{B}\) dependen de \(\omega\), \(\zeta\) y \(\Delta t\). Con \(\omega_d = \omega\sqrt{1-\zeta^2}\) y \(e = e^{-\zeta\omega\Delta t}\):

\[
\begin{aligned}
A_{11} &= e\bigl(\zeta\omega/\omega_d\,\sin\omega_d\Delta t + \cos\omega_d\Delta t\bigr) \\
A_{12} &= e\,(\sin\omega_d\Delta t)/\omega_d \\
A_{21} &= -e\,(\omega^2/\omega_d)\,\sin\omega_d\Delta t \\
A_{22} &= e\bigl(\cos\omega_d\Delta t - \zeta\omega/\omega_d\,\sin\omega_d\Delta t\bigr)
\end{aligned}
\]

(los coeficientes \(B_{ij}\) siguen la formulación clásica de Nigam & Jennings, 1969; ver implementación en `_nj_one_period`).

**Ventajas del método:**

- Exacto para excitación lineal por tramos (no introduce error de discretización del Newmark más allá de esa hipótesis).
- Estable numéricamente en el rango \(T = 0.01\)–\(4\) s con los \(\Delta t\) de la RNAC.
- Estándar de facto en cálculo de espectros de respuesta a partir de acelerogramas.

Condiciones iniciales: \(u(0)=\dot{u}(0)=0\) (sistema en reposo al inicio del registro corregido).

### 5.4 Combinación de componentes horizontales

Para cada periodo se calcula la **media geométrica** de las aceleraciones espectrales EW y NS:

\[
S_a^{H}(T) = \sqrt{\,S_a^{\mathrm{EW}}(T)\cdot S_a^{\mathrm{NS}}(T)\,}
\]

Es una aproximación habitual a una medida horizontal independiente de la orientación (análoga en espíritu a RotD50, sin rotar el registro). Se exporta como `Sa_RotD50_approx_g` / `PSA_geo_mean_g` en los CSV.

La componente vertical se procesa por separado (mismo modelo SDOF).

---

## 6. Flujo completo del procesamiento

```
Archivo .ANC (EW, VER, NS)
        │
        ▼
┌───────────────────────┐
│ 1. Lectura + metadatos│
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 2. Demean             │
│ 3. Detrend lineal     │
│ 4. Taper coseno 5 %   │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 5. Butterworth 4 polos│
│    0.1–25 Hz, filtfilt│
│ 6. Taper 2.5 % + mean │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 7. CSV aceleración    │
│    (+ MiniSEED ObsPy) │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 8. SDOF + Nigam–      │
│    Jennings, ζ=5 %    │
│    T = 0, 0.01, …, 4 s│
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 9. CSV espectro       │
│    Sa, Sv, Sd, PSA    │
│    + media geom. H    │
└───────────────────────┘
```

---

## 7. Parámetros adoptados (resumen)

| Parámetro | Valor | Modelo / método |
|-----------|-------|-----------------|
| Corrección de media | Sí | Resta de valor medio |
| Detrend | Lineal (grado 1) | Mínimos cuadrados |
| Taper | Coseno, 5 % + 2.5 % | Ventana de Tukey parcial |
| Filtro | Butterworth orden 4, pasabanda | SciPy `butter` + `filtfilt` |
| \(f_L\) – \(f_H\) | 0.10 – 25 Hz | Banda estructural / anti-ruido |
| Sistema dinámico | SDOF lineal viscoso | Ecuación de 2.º orden |
| Amortiguamiento \(\zeta\) | 5 % | Convención NSR / ASCE |
| Integración temporal | Nigam–Jennings | Solución exacta tramo a tramo |
| Rango de periodos | 0 – 4 s | Edificaciones típicas a altas |
| Paso \(\Delta T\) | 0.01 s | Resolución del espectro |
| Combinación H | Media geométrica EW–NS | Demanda horizontal escalar |

---

## 8. Unidades de salida

| Magnitud | Unidad en CSV |
|----------|----------------|
| Tiempo | s |
| Aceleración de señal | cm/s² y g (\(g = 981\) cm/s²) |
| \(S_a\) | g |
| \(S_v\) | cm/s |
| \(S_d\) | cm |
| PSA | g |

---

## 9. Limitaciones y alcances

1. **Linealidad:** el espectro es elástico; no modela plastificación ni degradación de rigidez.
2. **Un grado de libertad:** no representa modos superiores ni irregularidades 3D del edificio.
3. **Sin deconvolución de sitio:** el espectro es el del movimiento **en la estación**, no en roca aflorante ni en un predio distinto.
4. **Sin corrección de respuesta del instrumento:** se asume válida la aceleración entregada por el SGC en la banda filtrada.
5. **Amplificación por efectos de sitio locales** (cenizas, laderas, llenos, etc.) se trata en documento aparte: `guia_amplificacion_efectos_sitio.md`.

---

## 10. Referencias metodológicas

1. Nigam, N. C. & Jennings, P. C. (1969). *Calculation of Response Spectra from Strong-Motion Earthquake Records.* Bulletin of the Seismological Society of America, 59(2), 909–922.  
2. Butterworth, S. (1930). *On the Theory of Filter Amplifiers.* Wireless Engineer.  
3. Boore, D. M. (2001, y trabajos posteriores). Procesamiento de acelerogramas: baseline correction y filtrado.  
4. Chopra, A. K. *Dynamics of Structures* — espectro de respuesta y SDOF.  
5. ObsPy Development Team — lectura y manipulación de series sísmicas.  
6. AIS / NSR-10 — amortiguamiento de referencia y uso de espectros en diseño (marco normativo colombiano).

---

## 11. Reproducibilidad

```text
python procesar_sismo.py
```

Entradas: `SGC-Data/*.anc`  
Salidas: `output/senales/`, `output/espectros/`, `output/estaciones_identificadas.json`

Cualquier cambio de \(f_L\), \(f_H\), \(\zeta\) o \(\Delta T\) debe documentarse y regenerar los CSV, pues modifica PGA, forma espectral y demandas de diseño derivadas.

# -*- coding: utf-8 -*-
"""Genera index.html del informe del sismo 10-ago-2026."""
from __future__ import annotations

import csv
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "Espectros" / "table-Estaciones-Localizacion-PGA.csv"
OUT = ROOT / "index.html"

STATIONS = [
    ("ARMEC", "Armenia, Quindío"),
    ("CBOCA", "Pereira / Bocatoma, Risaralda — DATO ATÍPICO"),
    ("CCALA", "Calarcá, Quindío"),
    ("CIRS", "Circasia, Quindío"),
    ("CTRUJ", "Trujillo, Valle del Cauca"),
    ("FLND", "Filandia, Quindío"),
    ("MAN1C", "Manizales, Caldas"),
    ("SLNT", "Salento, Quindío"),
]

ATYPICAL_STATIONS = {"CBOCA"}

HEADERS = [
    "Nombre estación",
    "Red",
    "Código",
    "Latitud (°)",
    "Longitud (°)",
    "Localizador",
    "Elevación (msnm)",
    "Dist. Epi (km)",
    "Dist. Hip (km)",
    "PGA EW (cm/s²)",
    "PGA NS (cm/s²)",
    "PGA Z (cm/s²)",
]


def esc(x: str) -> str:
    return html.escape(str(x) if x is not None else "")


def load_rows() -> list[list[str]]:
    with CSV_PATH.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        return [row for row in reader if row]


def spectrum_section() -> str:
    blocks = []
    for code, place in STATIONS:
        psa = f"Espectros/{code}_10_PSA5.png"
        drs = f"Espectros/{code}_10_DRS5.png"
        anc = f"SGC-Data/SGC2026pqqmro_{code}_10.anc"
        atypical = code in ATYPICAL_STATIONS
        warn = ""
        card_class = "station-card"
        if atypical:
            card_class += " atypical"
            warn = """
        <div class="alert">
          <strong>Observación de calidad:</strong> los datos de CBOCA son un
          <strong>dato atípico</strong> respecto a la propagación del sismo y a los
          daños reales evidenciados en Pereira (ciudad más afectada). La estación
          podría estar defectuosa. <strong>No emplear</strong> estos datos en
          análisis estadísticos ni modelaciones detalladas.
        </div>"""
        blocks.append(
            f"""
      <article class="{card_class}" id="espectro-{code}">
        <h3>{esc(code)} — {esc(place)}</h3>
        {warn}
        <p class="meta">
          Acelerograma:
          <a href="{anc}">SGC2026pqqmro_{code}_10.anc</a>
          · Espectros oficiales SGC (ζ = 5 %)
        </p>
        <div class="spectra-grid">
          <figure>
            <img src="{psa}" alt="PSA 5% estación {code}" loading="lazy" />
            <figcaption>Pseudoaceleración espectral (PSA) — 5 % amortiguamiento</figcaption>
          </figure>
          <figure>
            <img src="{drs}" alt="DRS 5% estación {code}" loading="lazy" />
            <figcaption>Espectro de desplazamiento (DRS) — 5 % amortiguamiento</figcaption>
          </figure>
        </div>
      </article>"""
        )
    return "\n".join(blocks)


def stations_table(rows: list[list[str]]) -> str:
    thead = "".join(f"<th>{esc(h)}</th>" for h in HEADERS)
    body_rows = []
    for row in rows:
        # pad/truncate to 12 cols
        cells = (row + [""] * 12)[:12]
        code = cells[2].strip() if len(cells) > 2 else ""
        classes = []
        if code in {s[0] for s in STATIONS}:
            classes.append("has-waveform")
        if code in ATYPICAL_STATIONS:
            classes.append("atypical-row")
        cls = f' class="{" ".join(classes)}"' if classes else ""
        tds = "".join(f"<td>{esc(c)}</td>" for c in cells)
        body_rows.append(f"<tr{cls}>{tds}</tr>")
    return f"""
    <div class="table-wrap">
      <table>
        <thead><tr>{thead}</tr></thead>
        <tbody>
          {"".join(body_rows)}
        </tbody>
      </table>
    </div>
    <p class="note">Filas en tono cálido: estaciones con acelerograma ANC y espectros PSA/DRS en el repositorio.
    Fila con borde rojo (CBOCA): <strong>dato atípico</strong> — no usar en análisis estadísticos ni modelaciones.</p>
"""


def main() -> None:
    rows = load_rows()
    html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Terremoto 10 ago 2026 — Eje Cafetero | Informe técnico</title>
  <style>
    :root {{
      --ink: #1a1f24;
      --muted: #4a5560;
      --line: #d5dbe3;
      --bg: #f3f1ec;
      --card: #ffffff;
      --accent: #8b4513;
      --accent-soft: #e8d5c4;
      --highlight: #f7f0e8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(ellipse at top, #ebe6dc 0%, var(--bg) 55%),
        var(--bg);
      line-height: 1.55;
    }}
    .wrap {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 2rem 1.25rem 4rem;
    }}
    header.hero {{
      border-bottom: 3px solid var(--accent);
      padding-bottom: 1.25rem;
      margin-bottom: 2rem;
    }}
    header.hero p.kicker {{
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 0.75rem;
      color: var(--accent);
      margin: 0 0 0.4rem;
      font-weight: 700;
    }}
    h1 {{
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(1.6rem, 3vw, 2.2rem);
      margin: 0 0 0.5rem;
      line-height: 1.2;
    }}
    h2 {{
      font-family: Georgia, "Times New Roman", serif;
      font-size: 1.35rem;
      margin: 2.4rem 0 0.85rem;
      padding-top: 0.5rem;
      border-top: 1px solid var(--line);
    }}
    h3 {{
      margin: 0 0 0.4rem;
      font-size: 1.05rem;
    }}
    p, li {{ color: var(--ink); }}
    .muted {{ color: var(--muted); }}
    a {{ color: #6b3a12; }}
    a:hover {{ color: #3d220a; }}
    nav.toc {{
      background: var(--card);
      border: 1px solid var(--line);
      padding: 1rem 1.25rem;
      margin: 1.5rem 0;
    }}
    nav.toc ol {{ margin: 0.4rem 0 0; padding-left: 1.2rem; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
      background: var(--card);
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 0.35rem 0.45rem;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #2c333a;
      color: #fff;
      position: sticky;
      top: 0;
      z-index: 1;
      font-weight: 600;
      white-space: nowrap;
    }}
    tr.has-waveform {{ background: var(--highlight); }}
    tr.atypical-row {{ background: #fde8e4; outline: 2px solid #b33a2b; outline-offset: -2px; }}
    .alert {{
      background: #fde8e4;
      border: 1px solid #b33a2b;
      border-left: 4px solid #b33a2b;
      padding: 0.75rem 1rem;
      margin: 0.6rem 0 1rem;
      font-size: 0.92rem;
    }}
    .station-card.atypical {{
      border-color: #b33a2b;
    }}
    .table-wrap {{
      overflow: auto;
      max-height: 520px;
      border: 1px solid var(--line);
      margin: 0.75rem 0;
    }}
    .note {{
      font-size: 0.9rem;
      color: var(--muted);
    }}
    .station-card {{
      background: var(--card);
      border: 1px solid var(--line);
      padding: 1rem 1.1rem 1.25rem;
      margin: 1.25rem 0;
    }}
    .station-card .meta {{
      font-size: 0.9rem;
      color: var(--muted);
      margin: 0 0 0.9rem;
    }}
    .spectra-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }}
    @media (max-width: 800px) {{
      .spectra-grid {{ grid-template-columns: 1fr; }}
    }}
    figure {{
      margin: 0;
    }}
    figure img {{
      width: 100%;
      height: auto;
      display: block;
      border: 1px solid var(--line);
      background: #fff;
    }}
    figcaption {{
      font-size: 0.8rem;
      color: var(--muted);
      margin-top: 0.35rem;
    }}
    .params {{
      background: var(--card);
      border-left: 4px solid var(--accent);
      padding: 0.85rem 1rem;
      margin: 1rem 0;
    }}
    footer {{
      margin-top: 3rem;
      padding-top: 1rem;
      border-top: 1px solid var(--line);
      font-size: 0.85rem;
      color: var(--muted);
    }}
    code {{
      background: #ece8e1;
      padding: 0.1em 0.35em;
      font-size: 0.92em;
    }}
    ul.compact li {{ margin: 0.25rem 0; }}
  </style>
</head>
<body>
  <div class="wrap">
    <header class="hero">
      <p class="kicker">Ingeniería sísmica · Datos RNAC / SGC</p>
      <h1>Terremoto del 10 de agosto de 2026 — Eje Cafetero (Colombia)</h1>
      <p class="muted">
        Evento <strong>SGC2026pqqmro</strong> · M 7.4 · San José del Palmar (Chocó) ·
        Acelerogramas, espectros oficiales y productos derivados para evaluación de demanda sísmica.
        Versión Markdown: <a href="README.md">README.md</a>
      </p>
    </header>

    <nav class="toc" aria-label="Contenido">
      <strong>Contenido</strong>
      <ol>
        <li><a href="#resumen">Resumen del sismo</a></li>
        <li><a href="#sgc">Información recopilada del SGC</a></li>
        <li><a href="#metodologia">Metodología de procesamiento</a></li>
        <li><a href="#amplificacion">Factores de amplificación por sitio</a></li>
        <li><a href="#estaciones">Estaciones — localización y PGA</a></li>
        <li><a href="#espectros-sgc">Espectros de respuesta obtenidos por el SGC</a></li>
        <li><a href="#referencias">Referencias</a></li>
      </ol>
    </nav>

    <section id="resumen">
      <h2>1. Resumen del sismo</h2>
      <div class="table-wrap" style="max-height:none">
        <table>
          <tbody>
            <tr><th>Código de evento</th><td>SGC2026pqqmro</td></tr>
            <tr><th>Fecha y hora (UTC)</th><td>2026-08-10 · 12:34:27</td></tr>
            <tr><th>Magnitud</th><td><strong>M 7.4</strong></td></tr>
            <tr><th>Epicentro</th><td>San José del Palmar, Chocó</td></tr>
            <tr><th>Latitud / Longitud</th><td>4.99° N / −76.293° W</td></tr>
            <tr><th>Profundidad</th><td>103 km</td></tr>
            <tr><th>Región tectónica</th><td>Subducción — <strong>intraslab</strong> (STREC/ShakeMap SGC)</td></tr>
            <tr><th>Área de interés</th><td>Eje Cafetero (Quindío, Risaralda, Caldas) y municipios aledaños</td></tr>
            <tr><th>Estaciones con forma de onda en el repo</th><td>8 (ARMEC, CBOCA, CCALA, CIRS, CTRUJ, FLND, MAN1C, SLNT)</td></tr>
            <tr><th>Estaciones con PGA reportado por SGC</th><td>{len(rows)} (tabla completa abajo)</td></tr>
          </tbody>
        </table>
      </div>
      <p>
        El evento corresponde a un sismo profundo de placa. En el Eje Cafetero, las distancias
        epicentrales a las estaciones con forma de onda oscilan típicamente entre 75 y 90 km.
        Las PGA horizontales en estaciones confiables alcanzan demandas elevadas
        (FLND, CIRS), coherentes con la severidad del movimiento en el corredor cafetero.
        El ShakeMap SGC reporta, a escala regional, PGA de grilla del orden de ~0.3 g y SA(0.3) hasta ~0.55 g.
      </p>
      <div class="alert" id="obs-cboca">
        <strong>Observación — estación CBOCA (Pereira):</strong>
        los amplitudes registrados en CBOCA constituyen un <strong>dato atípico</strong>
        respecto a la propagación esperada del sismo y a los <strong>daños reales evidenciados
        en Pereira</strong>, ciudad entre las más afectadas. La estación podría estar
        <strong>defectuosa</strong>. <strong>No se recomienda emplear los datos de CBOCA</strong>
        en análisis estadísticos, ajustes de atenuación ni modelaciones detalladas de demanda.
        El registro se conserva solo como archivo fuente SGC, marcado como no confiable.
      </div>
    </section>

    <section id="sgc">
      <h2>2. Información recopilada del Servicio Geológico Colombiano</h2>
      <div class="table-wrap" style="max-height:none">
        <table>
          <thead>
            <tr><th>Producto</th><th>Descripción</th><th>Archivo</th></tr>
          </thead>
          <tbody>
            <tr><td>Acelerogramas ANC</td><td>Ocho estaciones RNAC, componentes EW–VER–NS (cm/s²)</td>
              <td><a href="SGC-Data/">SGC-Data/*.anc</a></td></tr>
            <tr><td>MiniSEED</td><td>Formas de onda auxiliares</td>
              <td><a href="SGC-Data/">SGC-Data/*.mseed</a></td></tr>
            <tr><td>Tabla estaciones–PGA</td><td>Localización y PGA EW/NS/Z ({len(rows)} estaciones)</td>
              <td><a href="Espectros/table-Estaciones-Localizacion-PGA.csv">Espectros/table-Estaciones-Localizacion-PGA.csv</a></td></tr>
            <tr><td>Espectros PSA 5 %</td><td>Gráficos oficiales de pseudoaceleración</td>
              <td><a href="Espectros/">Espectros/*_PSA5.png</a></td></tr>
            <tr><td>Espectros DRS 5 %</td><td>Gráficos oficiales de desplazamiento espectral</td>
              <td><a href="Espectros/">Espectros/*_DRS5.png</a></td></tr>
            <tr><td>PSA tabular CIRS</td><td>Serie PSA exportada</td>
              <td><a href="Espectros/CIRS_10_PSA5.csv">CIRS_10_PSA5.csv</a></td></tr>
            <tr><td>Generalidades SGC</td><td>PDF de aceleraciones / contexto</td>
              <td><a href="Espectros/SGC%20-%20Sismo%20Generalidades-Aceleraciones%20estacion.pdf">PDF generalidades</a></td></tr>
            <tr><td>ShakeMap</td><td>Metadatos, estaciones, grilla e incertidumbre</td>
              <td>
                <a href="SGC-Data/info.json">info.json</a> ·
                <a href="SGC-Data/stationlist.json">stationlist.json</a> ·
                <a href="SGC-Data/grid.xml">grid.xml</a> ·
                <a href="SGC-Data/uncertainty.xml">uncertainty.xml</a>
              </td></tr>
            <tr><td>Productos derivados</td><td>Señales filtradas y espectros recalculados</td>
              <td><a href="output/senales/">output/senales/</a> · <a href="output/espectros/">output/espectros/</a></td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <section id="metodologia">
      <h2>3. Metodología de procesamiento de señales</h2>
      <p>
        Sobre los acelerogramas <code>.ANC</code> se aplicó una cadena de post-proceso orientada a
        ingeniería estructural (ObsPy, NumPy, SciPy, Numba):
      </p>
      <ol>
        <li><strong>Corrección de línea base:</strong> demean, detrend lineal y taper coseno (5 %) para extremos ≈ 0.</li>
        <li><strong>Filtro pasabanda Butterworth</strong> de 4 polos, <strong>0.10–25 Hz</strong>, fase cero (<code>filtfilt</code>).</li>
        <li><strong>Espectro de respuesta elástico</strong> SDOF, ζ = 5 %, método <strong>Nigam–Jennings (1969)</strong>, T = 0–4 s (ΔT = 0.01 s); media geométrica horizontal EW–NS.</li>
      </ol>
      <div class="params">
        <p style="margin:0">
          Documento detallado:
          <a href="docs/metodos_procesamiento_y_espectro.md"><strong>docs/metodos_procesamiento_y_espectro.md</strong></a><br />
          Código:
          <a href="procesar_sismo.py"><strong>procesar_sismo.py</strong></a>
          (<code>python procesar_sismo.py</code>)
        </p>
      </div>
      <h3>Parámetros no incorporados por falta de información</h3>
      <ul class="compact">
        <li>Función de transferencia instrumental (<code>TIPO DE EQUIPO</code> no especificado).</li>
        <li>Deconvolución a roca (sin perfiles V<sub>S</sub> / V<sub>S30</sub> por estación).</li>
        <li>RotD50/100 por rotación azimutal (se usó media geométrica EW–NS).</li>
        <li>Respuesta no lineal de sitio y geometría de ruptura / directividad.</li>
        <li>Condiciones de cimentación o caja del instrumento.</li>
        <li><strong>CBOCA (Pereira):</strong> registro atípico frente a daños observados;
            posible defecto instrumental — excluir de análisis estadísticos y modelaciones
            (ver <a href="#obs-cboca">observación</a>).</li>
      </ul>
      <p class="note">
        El movimiento procesado es el registrado en la estación, no necesariamente el de un predio
        con geología local distinta.
      </p>
    </section>

    <section id="amplificacion">
      <h2>4. Factores de amplificación por efectos de sitio</h2>
      <p>
        Factores centrales recomendados para escalar un espectro base:
        S<sub>a,sitio</sub>(T) = F<sub>a</sub>(T) · S<sub>a,base</sub>(T).
      </p>
      <div class="table-wrap" style="max-height:none">
        <table>
          <thead>
            <tr>
              <th>Condición de sitio</th>
              <th>Fa(PGA)</th><th>Fa(0.3 s)</th><th>Fa(1.0 s)</th><th>Fa(3.0 s)</th><th>Fv*</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Roca / basamento</td><td>1.00</td><td>1.00</td><td>1.00</td><td>1.00</td><td>1.00</td></tr>
            <tr><td>Corona de laderas</td><td>1.35</td><td>1.40</td><td>1.15</td><td>1.05</td><td>1.10</td></tr>
            <tr><td>Pie de laderas</td><td>1.25</td><td>1.45</td><td>1.50</td><td>1.35</td><td>1.40</td></tr>
            <tr><td>Cenizas bajo espesor (recientes)</td><td>1.40</td><td>1.70</td><td>1.25</td><td>1.05</td><td>1.15</td></tr>
            <tr><td>Cenizas intermedio/alto (gel siloxano)</td><td>1.55</td><td>2.10</td><td>2.00</td><td>1.60</td><td>1.90</td></tr>
            <tr><td>Fluvio-lacustres</td><td>1.45</td><td>1.80</td><td>2.20</td><td>2.00</td><td>2.10</td></tr>
            <tr><td>Fluviotorrenciales (Fm. Quindío)</td><td>1.50</td><td>1.90</td><td>1.75</td><td>1.40</td><td>1.65</td></tr>
            <tr><td>Llenos antrópicos</td><td>1.60</td><td>2.00</td><td>1.85</td><td>1.50</td><td>1.75</td></tr>
          </tbody>
        </table>
      </div>
      <p>
        Guía completa:
        <a href="docs/guia_amplificacion_efectos_sitio.md"><strong>docs/guia_amplificacion_efectos_sitio.md</strong></a>
        · CSV: <a href="output/factores_amplificacion_sitio.csv">factores_amplificacion_sitio.csv</a>
      </p>
    </section>

    <section id="estaciones">
      <h2>5. Estaciones sismológicas — localización y PGA (SGC)</h2>
      <p class="muted">
        Fuente:
        <a href="Espectros/table-Estaciones-Localizacion-PGA.csv">table-Estaciones-Localizacion-PGA.csv</a>
        ({len(rows)} estaciones).
      </p>
      {stations_table(rows)}
    </section>

    <section id="espectros-sgc">
      <h2>6. Espectros de respuesta obtenidos por el SGC</h2>
      <p>
        Gráficos oficiales de <strong>PSA</strong> (pseudoaceleración) y <strong>DRS</strong>
        (desplazamiento espectral) al 5 % de amortiguamiento, para las estaciones con forma de onda
        en este repositorio. Archivos en <a href="Espectros/">Espectros/</a>.
      </p>
      {spectrum_section()}
    </section>

    <section id="referencias">
      <h2>7. Referencias</h2>
      <ol>
        <li>Servicio Geológico Colombiano (SGC). Red Nacional de Acelerógrafos (RNAC). Acelerogramas y espectros del evento <strong>SGC2026pqqmro</strong> (2026-08-10).</li>
        <li>SGC. ShakeMap — <code>info.json</code>, <code>grid.xml</code>, <code>stationlist.json</code>, <code>uncertainty.xml</code>.</li>
        <li>Nigam, N. C. &amp; Jennings, P. C. (1969). <em>Calculation of Response Spectra from Strong-Motion Earthquake Records.</em> BSSA, 59(2), 909–922.</li>
        <li>Butterworth, S. (1930). <em>On the Theory of Filter Amplifiers.</em> Wireless Engineer.</li>
        <li>Boore, D. M. Trabajos sobre corrección de línea base y filtrado de acelerogramas.</li>
        <li>Chopra, A. K. <em>Dynamics of Structures.</em></li>
        <li>The ObsPy Development Team. ObsPy: A Python Framework for Seismology.</li>
        <li>AIS. <strong>NSR-10</strong> — Reglamento Colombiano de Construcción Sismo Resistente, Título A.</li>
        <li>INGEOMINAS / SGC. Microzonificación y respuesta de sitio en el Eje Cafetero.</li>
        <li>Documentación del proyecto:
          <a href="docs/metodos_procesamiento_y_espectro.md">metodología</a>,
          <a href="docs/guia_amplificacion_efectos_sitio.md">amplificación por sitio</a>.
        </li>
      </ol>
    </section>

    <footer>
      Informe técnico de datos y procesamiento — evaluación de demanda sísmica.
      Para diseño reglamentario prevalecen NSR vigente y la microzonificación oficial del municipio.
      · <a href="README.md">README.md</a>
    </footer>
  </div>
</body>
</html>
"""
    OUT.write_text(html_doc, encoding="utf-8")
    print(f"Wrote {OUT} with {len(rows)} stations")


if __name__ == "__main__":
    main()

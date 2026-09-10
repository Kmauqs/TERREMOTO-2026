# -*- coding: utf-8 -*-
"""Genera index.html del informe del sismo 10-ago-2026 y figuras de §6.1."""
from __future__ import annotations

import csv
import html
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "Espectros" / "table-Estaciones-Localizacion-PGA.csv"
OUT = ROOT / "index.html"
FIG_DIR = ROOT / "output" / "figuras"
SENALES_DIR = ROOT / "output" / "senales"
ESPECTROS_DIR = ROOT / "output" / "espectros"

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

# Estilo alineado con NSR-10 (consolidado / portada NEXUS)
_COLORS = {
    "EW": "#0a6e99",
    "NS": "#063c5b",
    "VER": "#5a6d7c",
    "GEO": "#14283b",
    "grid": "#cbd9e0",
    "ink": "#14283b",
    "danger": "#9b0d18",
    "fig_bg": "#edf3f5",
}

# Colores llamativos solo para espectros de respuesta
_SPECTRUM_COLORS = {
    "EW": "#e000a8",   # magenta
    "NS": "#1a5cff",   # azul
    "VER": "#00a86b",  # verde
}


def esc(x: str) -> str:
    return html.escape(str(x) if x is not None else "")


def load_rows() -> list[list[str]]:
    with CSV_PATH.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        return [row for row in reader if row]


def _downsample(n: int, max_pts: int = 8000) -> slice:
    if n <= max_pts:
        return slice(None)
    step = max(1, n // max_pts)
    return slice(None, None, step)


def _style_axes(ax: plt.Axes) -> None:
    ax.set_facecolor("#ffffff")
    ax.grid(True, color=_COLORS["grid"], linewidth=0.6, alpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=8)


SIGNAL_T_MAX_S = 300.0


def plot_signal(code: str, atypical: bool) -> Path | None:
    csv_path = SENALES_DIR / f"{code}_aceleracion_ajustada.csv"
    if not csv_path.is_file():
        print(f"  [omitido] señal no encontrada: {csv_path.name}")
        return None

    data = np.genfromtxt(csv_path, delimiter=",", names=True)
    t = data["time_s"]
    mask = t <= SIGNAL_T_MAX_S + 1e-9
    t = t[mask]
    ew = data["acc_EW_g"][mask]
    ns = data["acc_NS_g"][mask]
    ver = data["acc_VER_g"][mask]
    sl = _downsample(len(t))
    t = t[sl]
    ew = ew[sl]
    ns = ns[sl]
    ver = ver[sl]

    fig, axes = plt.subplots(3, 1, figsize=(9.5, 6.2), sharex=True, constrained_layout=True)
    series = (
        ("EW", ew, _COLORS["EW"]),
        ("NS", ns, _COLORS["NS"]),
        ("VER", ver, _COLORS["VER"]),
    )
    for ax, (label, y, color) in zip(axes, series):
        ax.plot(t, y, color=color, linewidth=0.55)
        ax.set_xlim(0, SIGNAL_T_MAX_S)
        ax.set_ylabel(f"{label} (g)", fontsize=9)
        _style_axes(ax)
        pga = float(np.max(np.abs(y)))
        ax.set_title(f"PGA {label} ≈ {pga:.3f} g", loc="right", fontsize=8, color=_COLORS["VER"])

    axes[-1].set_xlabel("Tiempo (s)", fontsize=9)
    title = f"{code} — aceleración depurada (línea base + filtro 0.1–25 Hz)"
    if atypical:
        title += "  ·  DATO ATÍPICO — NO USAR"
    fig.suptitle(
        title,
        fontsize=11,
        fontweight="bold",
        color=_COLORS["danger"] if atypical else _COLORS["ink"],
    )

    out = FIG_DIR / f"{code}_senal_depurada.png"
    fig.savefig(out, dpi=140, facecolor=_COLORS["fig_bg"], edgecolor="none")
    plt.close(fig)
    return out


def plot_spectrum(code: str, atypical: bool) -> Path | None:
    csv_path = ESPECTROS_DIR / f"{code}_espectro_respuesta_elastico.csv"
    if not csv_path.is_file():
        print(f"  [omitido] espectro no encontrado: {csv_path.name}")
        return None

    data = np.genfromtxt(csv_path, delimiter=",", names=True)
    T = data["T_s"]
    mask = T <= 4.0 + 1e-9
    T = T[mask]
    sa_ew = data["Sa_EW_g"][mask]
    sa_ns = data["Sa_NS_g"][mask]
    sa_ver = data["Sa_VER_g"][mask]
    sa_geo = data["Sa_RotD50_approx_g"][mask]
    psa_geo = data["PSA_geo_mean_g"][mask]

    fig, ax = plt.subplots(figsize=(9.5, 4.6), constrained_layout=True)
    ax.plot(T, sa_ew, color=_SPECTRUM_COLORS["EW"], linewidth=1.35, label=r"$S_a$ EW")
    ax.plot(T, sa_ns, color=_SPECTRUM_COLORS["NS"], linewidth=1.35, label=r"$S_a$ NS")
    ax.plot(T, sa_ver, color=_SPECTRUM_COLORS["VER"], linewidth=1.35, label=r"$S_a$ V")
    ax.plot(
        T,
        sa_geo,
        color=_COLORS["GEO"],
        linewidth=1.8,
        label=r"$S_a$ media geom. H (EW–NS)",
    )
    ax.plot(
        T,
        psa_geo,
        color="#0b698f",
        linewidth=1.0,
        linestyle="--",
        alpha=0.85,
        label="PSA media geom. H",
    )
    ax.set_xlim(0, 4)
    ax.set_xlabel("Periodo T (s)", fontsize=9)
    ax.set_ylabel(r"Aceleración espectral $S_a$ / PSA (g)", fontsize=9)
    _style_axes(ax)
    ax.legend(fontsize=8, frameon=True, fancybox=False, edgecolor=_COLORS["grid"])

    title = f"{code} — espectro de respuesta elástico (ζ = 5 %, Nigam–Jennings)"
    if atypical:
        title += "  ·  DATO ATÍPICO — NO USAR"
    ax.set_title(
        title,
        fontsize=11,
        fontweight="bold",
        color=_COLORS["danger"] if atypical else _COLORS["ink"],
    )

    out = FIG_DIR / f"{code}_espectro_respuesta.png"
    fig.savefig(out, dpi=140, facecolor=_COLORS["fig_bg"], edgecolor="none")
    plt.close(fig)
    return out


def generate_figures() -> dict[str, dict[str, Path]]:
    """Genera PNG de señal y espectro por estación. Devuelve rutas relativas al repo."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, Path]] = {}
    print(f"Generando figuras en {FIG_DIR.relative_to(ROOT)} …")
    for code, _place in STATIONS:
        atypical = code in ATYPICAL_STATIONS
        sig = plot_signal(code, atypical)
        sp = plot_spectrum(code, atypical)
        results[code] = {}
        if sig is not None:
            results[code]["signal"] = sig.relative_to(ROOT).as_posix()
        if sp is not None:
            results[code]["spectrum"] = sp.relative_to(ROOT).as_posix()
        print(f"  {code}: señal={'ok' if sig else '—'}  espectro={'ok' if sp else '—'}")
    return results


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


def analysis_limitations_table() -> str:
    """Tabla de limitaciones alineada con docs/metodos y README §3.2."""
    rows = [
        (
            "Corrección de línea base",
            "Demean + detrend lineal + taper coseno (5 %; post-filtro 2.5 %). "
            "No elimina por sí sola errores instrumentales severos.",
        ),
        (
            "Filtro pasabanda",
            "Butterworth 4 polos, <strong>0.10–25 Hz</strong>, fase cero (<code>filtfilt</code>). "
            "Contenido fuera de banda atenuado; no es deconvolución instrumental.",
        ),
        (
            "Espectro elástico SDOF",
            "Oscilador lineal viscoso con <strong>ζ = 5 %</strong>; no modela plastificación "
            "ni degradación de rigidez.",
        ),
        (
            "Integración temporal",
            "Método exacto <strong>Nigam–Jennings (1969)</strong> para excitación lineal por tramos; "
            "T = 0–4 s, ΔT = 0.01 s.",
        ),
        (
            "Combinación horizontal",
            "Media geométrica EW–NS (proxy tipo RotD50). "
            "<strong>No</strong> se calculó RotD50/RotD100 por rotación azimutal.",
        ),
        (
            "Función de transferencia del instrumento",
            "<strong>No aplicada</strong>: campo <code>TIPO DE EQUIPO</code> vacío o no especificado "
            "en los <code>.ANC</code>.",
        ),
        (
            "Deconvolución a roca / sitio",
            "<strong>No aplicada</strong>: sin perfiles V<sub>S</sub>(z) ni V<sub>S30</sub> medidos "
            "por estación. El espectro es el del movimiento <em>en la estación</em>.",
        ),
        (
            "Orientación de sensores",
            "Sin corrección adicional de azimuth más allá de las etiquetas EW/NS del SGC.",
        ),
        (
            "Respuesta no lineal de sitio",
            "No modelada (requiere ensayo dinámico y modelo constitutivo de suelo).",
        ),
        (
            "Geometría de ruptura / directividad",
            "No incorporada; ShakeMap sin falla finita explícita utilizable en este flujo.",
        ),
        (
            "Comparación formal SGC vs. espectro propio",
            "Los PSA/DRS oficiales (§6) son referencia visual; el pipeline recalcula el espectro "
            "de forma independiente (§6.1).",
        ),
        (
            "Estación CBOCA (Pereira)",
            "<strong>Dato atípico / no usar</strong> en análisis estadísticos, GMPE ni modelaciones. "
            "Amplitudes incongruentes con daños observados en Pereira "
            "(ver <a href=\"#obs-cboca\">observación</a>).",
        ),
    ]
    body = "".join(
        f"<tr><td>{aspect}</td><td>{detail}</td></tr>" for aspect, detail in rows
    )
    return f"""
      <div class="table-wrap" style="max-height:none">
        <table>
          <thead>
            <tr><th>Aspecto / limitación</th><th>Alcance de los datos mostrados</th></tr>
          </thead>
          <tbody>
            {body}
          </tbody>
        </table>
      </div>
      <p class="note">
        Detalle metodológico:
        <a href="docs/metodos_procesamiento_y_espectro.md">docs/metodos_procesamiento_y_espectro.md</a>
        · Resumen en <a href="README.md">README.md</a> (§3).
      </p>
"""


def analysis_section(figures: dict[str, dict[str, Path | str]]) -> str:
    blocks = []
    for code, place in STATIONS:
        atypical = code in ATYPICAL_STATIONS
        card_class = "station-card atypical" if atypical else "station-card"
        warn = ""
        if atypical:
            warn = """
        <div class="alert">
          <strong>Observación de calidad:</strong> CBOCA es un
          <strong>dato atípico</strong> respecto a la propagación del sismo y a los
          daños reales en Pereira. La estación podría estar defectuosa.
          <strong>No emplear</strong> estas señales ni espectros en análisis estadísticos
          ni modelaciones detalladas de demanda.
        </div>"""

        sig_csv = f"output/senales/{code}_aceleracion_ajustada.csv"
        sp_csv = f"output/espectros/{code}_espectro_respuesta_elastico.csv"
        figs = figures.get(code, {})
        sig_img = figs.get("signal", f"output/figuras/{code}_senal_depurada.png")
        sp_img = figs.get("spectrum", f"output/figuras/{code}_espectro_respuesta.png")

        blocks.append(
            f"""
      <article class="{card_class}" id="analisis-{code}">
        <h3>{esc(code)} — {esc(place)}</h3>
        {warn}
        <p class="meta">
          Señal depurada:
          <a href="{sig_csv}">{code}_aceleracion_ajustada.csv</a>
          · Espectro elástico (este análisis):
          <a href="{sp_csv}">{code}_espectro_respuesta_elastico.csv</a>
        </p>
        <div class="spectra-grid">
          <figure>
            <img src="{sig_img}" alt="Señal depurada estación {code}" loading="lazy" />
            <figcaption>
              Aceleración depurada (EW, NS, VER) tras corrección de línea base y filtro 0.1–25 Hz
            </figcaption>
          </figure>
          <figure>
            <img src="{sp_img}" alt="Espectro de respuesta estación {code}" loading="lazy" />
            <figcaption>
              Espectro de respuesta elástico S<sub>a</sub> / PSA (ζ = 5 %, T = 0–4 s) — Nigam–Jennings
            </figcaption>
          </figure>
        </div>
      </article>"""
        )

    return f"""
    <section id="analisis-propio">
      <h2>6.1 Señales depuradas y Espectros de Respuesta obtenidos mediante este análisis</h2>
      <p>
        Productos derivados del pipeline del proyecto (<a href="procesar_sismo.py">procesar_sismo.py</a>):
        acelerogramas corregidos/filtrados y espectros de respuesta elásticos recalculados
        (ζ = 5 %, Nigam–Jennings). Figuras en
        <a href="output/figuras/">output/figuras/</a>; CSV en
        <a href="output/senales/">output/senales/</a> y
        <a href="output/espectros/">output/espectros/</a>.
      </p>
      <h3>Limitaciones de los datos mostrados</h3>
      <p class="muted">
        Los gráficos y CSV de esta sección reflejan el movimiento <strong>en la estación</strong>
        tras el post-proceso indicado. No sustituyen microzonificación ni estudio de sitio local.
      </p>
      {analysis_limitations_table()}
      {"".join(blocks)}
    </section>
"""


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
    <p class="note">Filas en tono cielo: estaciones con acelerograma ANC y espectros PSA/DRS en el repositorio.
    Fila con borde rojo (CBOCA): <strong>dato atípico</strong> — no usar en análisis estadísticos ni modelaciones.</p>
"""


def main() -> None:
    rows = load_rows()
    figures = generate_figures()
    html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Terremoto 10 ago 2026 — Eje Cafetero | Informe técnico</title>
  <meta name="description" content="Informe técnico del sismo M 7.4 del 10 de agosto de 2026 (SGC2026pqqmro) — Eje Cafetero. Productos SGC, espectros y procesamiento." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Source+Code+Pro:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --ink: #14283b;
      --navy: #063c5b;
      --blue: #0a6e99;
      --sky: #e9f4f8;
      --gold: #d9a441;
      --line: #cbd9e0;
      --paper: #fff;
      --muted: #5a6d7c;
      --danger: #9b0d18;
      --danger-bg: #fde8e8;
      --highlight: #edf6f9;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: #edf3f5;
      font: 15px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif;
    }}
    header.site {{
      padding: 18px 30px 16px;
      color: #fff;
      background: linear-gradient(115deg, #063c5b, #0b698f);
    }}
    header.site h1 {{
      margin: 0;
      font-size: clamp(1.35rem, 2.8vw, 2.1rem);
      letter-spacing: -0.03em;
      line-height: 1.2;
      font-weight: 700;
    }}
    header.site > p {{
      max-width: 1100px;
      margin: 6px 0 0;
      color: #e4f3f9;
    }}
    header.site a {{ color: #d5ecf4; }}
    header.site a:hover {{ color: #fff; }}
    .home-link {{
      display: inline-block;
      margin: 0 0 8px;
      color: #d5ecf4;
      text-decoration: none;
      font-family: "Source Code Pro", ui-monospace, monospace;
      font-size: 0.82rem;
      font-weight: 600;
      letter-spacing: 0.04em;
    }}
    .home-link:hover {{ color: #fff; text-decoration: underline; }}
    .wrap {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 14px 20px 36px;
    }}
    h2 {{
      font-size: 1.15rem;
      margin: 1.75rem 0 0.85rem;
      color: var(--navy);
    }}
    h3 {{
      margin: 0 0 0.4rem;
      font-size: 1.02rem;
      color: var(--navy);
    }}
    p, li {{ color: var(--ink); }}
    .muted {{ color: var(--muted); font-size: 0.9rem; }}
    a {{ color: #075c86; }}
    a:hover {{ color: var(--navy); }}
    nav.toc {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 10px;
      box-shadow: 0 2px 10px #1232;
      padding: 1rem 1.25rem;
      margin: 0 0 1.25rem;
    }}
    nav.toc strong {{
      font-family: "Source Code Pro", ui-monospace, monospace;
      font-size: 0.78rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
    }}
    nav.toc ol {{ margin: 0.5rem 0 0; padding-left: 1.2rem; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.91rem;
      background: var(--paper);
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #edf6f9;
      color: var(--navy);
      position: sticky;
      top: 0;
      z-index: 1;
      font-weight: 700;
      white-space: nowrap;
    }}
    tr.has-waveform {{ background: var(--highlight); }}
    tr.atypical-row {{
      background: var(--danger-bg);
      outline: 2px solid var(--danger);
      outline-offset: -2px;
    }}
    .alert {{
      background: var(--danger-bg);
      border: 1px solid #f7c1c1;
      border-left: 4px solid var(--danger);
      border-radius: 3px;
      padding: 11px 12px;
      margin: 0.6rem 0 1rem;
      font-size: 0.92rem;
      color: var(--danger);
    }}
    .alert strong {{ color: var(--danger); }}
    .station-card.atypical {{
      border-color: var(--danger);
      box-shadow: 0 0 0 1px var(--danger);
    }}
    .table-wrap {{
      overflow: auto;
      max-height: 520px;
      border: 1px solid var(--line);
      border-radius: 8px;
      margin: 0.75rem 0;
      background: var(--paper);
    }}
    .note {{
      font-size: 0.9rem;
      color: var(--muted);
    }}
    .station-card {{
      background: #fbfdfe;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
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
      gap: 12px;
    }}
    @media (max-width: 800px) {{
      header.site {{ padding: 16px 16px 14px; }}
      .wrap {{ padding: 12px 12px 28px; }}
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
      border-radius: 6px;
      background: #fff;
    }}
    figcaption {{
      font-size: 0.8rem;
      color: var(--muted);
      margin-top: 0.35rem;
    }}
    .params {{
      background: #fff5d8;
      border-left: 4px solid var(--gold);
      border-radius: 3px;
      padding: 11px 12px;
      margin: 1rem 0;
    }}
    footer {{
      margin-top: 2.5rem;
      padding-top: 1rem;
      border-top: 1px solid var(--line);
      font-size: 0.8rem;
      color: var(--muted);
    }}
    footer strong {{
      font-family: "Source Code Pro", ui-monospace, monospace;
      color: var(--navy);
      font-weight: 700;
    }}
    code {{
      background: var(--sky);
      padding: 0.1em 0.35em;
      border-radius: 3px;
      font-size: 0.92em;
      font-family: "Source Code Pro", ui-monospace, monospace;
    }}
    ul.compact li {{ margin: 0.25rem 0; }}
    /* Capítulo 7 — herramienta espectros */
    .ch7-grid {{
      display: grid;
      grid-template-columns: minmax(260px, 340px) 1fr;
      gap: 1.1rem;
      align-items: start;
    }}
    @media (max-width: 900px) {{
      .ch7-grid {{ grid-template-columns: 1fr; }}
    }}
    .ch7-panel {{
      background: #fbfdfe;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0.9rem 1rem;
      box-shadow: 0 2px 10px #1232;
    }}
    .ch7-panel label {{
      display: block;
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--navy);
      margin: 0.55rem 0 0.2rem;
    }}
    .ch7-panel select, .ch7-panel input[type="number"] {{
      width: 100%;
      padding: 0.35rem 0.45rem;
      border: 1px solid var(--line);
      border-radius: 4px;
      background: #fff;
      color: var(--ink);
      font-size: 0.9rem;
    }}
    .ch7-check {{
      display: flex;
      gap: 0.45rem;
      align-items: flex-start;
      font-size: 0.86rem;
      margin: 0.45rem 0;
      font-weight: 500;
      color: var(--ink);
    }}
    .ch7-check input {{ margin-top: 0.2rem; }}
    .ch7-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-top: 0.85rem;
    }}
    .ch7-actions button {{
      background: var(--navy);
      color: #fff;
      border: none;
      border-radius: 4px;
      padding: 0.45rem 0.8rem;
      font-size: 0.88rem;
      cursor: pointer;
    }}
    .ch7-actions button.secondary {{
      background: #fff;
      color: var(--navy);
      border: 1px solid var(--navy);
    }}
    .ch7-actions button:hover {{ filter: brightness(1.08); }}
    .ch7-charts {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 0.9rem;
    }}
    .ch7-chart-box {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0.5rem;
      height: 340px;
    }}
    .ch7-legend-colors {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem 1.1rem;
      font-size: 0.82rem;
      margin: 0.6rem 0 1rem;
    }}
    .ch7-legend-colors span::before {{
      content: "";
      display: inline-block;
      width: 14px;
      height: 3px;
      margin-right: 0.35rem;
      vertical-align: middle;
      background: currentColor;
    }}
    .c-nsr {{ color: #c62828; }}
    .c-nsrr {{ color: #111; }}
    .c-micro {{ color: #ef6c00; }}
    .c-ew {{ color: #e000a8; }}
    .c-ns {{ color: #1a5cff; }}
    .c-v {{ color: #00a86b; }}
  </style>
</head>
<body>
  <header class="site">
    <a class="home-link" href="https://kmauqs.github.io/NSR-10/index.html">NEXUS CREATIO — Inicio</a>
    <h1>Terremoto del 10 de agosto de 2026 — Eje Cafetero (Colombia)</h1>
    <p>
      Evento <strong>SGC2026pqqmro</strong> · M 7.4 · San José del Palmar (Chocó) ·
      Acelerogramas, espectros oficiales y productos derivados para evaluación de demanda sísmica.
      Versión Markdown: <a href="README.md">README.md</a>
      · Marco 03 · Informe de evento
    </p>
  </header>
  <div class="wrap">
    <nav class="toc" aria-label="Contenido">
      <strong>Contenido</strong>
      <ol>
        <li><a href="#resumen">Resumen del sismo</a></li>
        <li><a href="#sgc">Información recopilada del SGC</a></li>
        <li><a href="#metodologia">Metodología de procesamiento</a></li>
        <li><a href="#amplificacion">Factores de amplificación por sitio</a></li>
        <li><a href="#estaciones">Estaciones — localización y PGA</a></li>
        <li><a href="#espectros-sgc">Espectros de respuesta obtenidos por el SGC</a></li>
        <li><a href="#analisis-propio">Señales depuradas y espectros de este análisis (6.1)</a></li>
        <li><a href="#herramienta-espectros">Herramienta de espectros de diseño NSR-10 (7)</a></li>
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
              <td><a href="output/senales/">output/senales/</a> · <a href="output/espectros/">output/espectros/</a> · <a href="output/figuras/">output/figuras/</a></td></tr>
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

{analysis_section(figures)}

    <section id="herramienta-espectros">
      <h2>7. Herramienta — espectros elásticos de diseño (NSR-10 A.2.6)</h2>
      <p>
        Genera el <strong>espectro elástico de aceleraciones de diseño</strong> y el
        <strong>espectro elástico de desplazamientos (m) de diseño</strong> según el
        numeral <strong>A.2.6</strong> de la NSR-10, a partir de <em>Aa</em>, <em>Av</em>
        del Apéndice A-4, coeficientes <em>Fa</em>/<em>Fv</em> (tablas A.2.4-3 y A.2.4-4),
        coeficiente de importancia <em>I</em> (A.2.5) y, cuando aplique, parámetros de
        microzonificación. Los desplazamientos por sismo se obtienen del espectro de
        desplazamientos <em>Sd</em>. Opcionalmente se reduce el espectro por el
        coeficiente de disipación de energía <em>R</em> (fuerzas de diseño del sistema
        principal) y se superponen espectros del evento SGC2026pqqmro.
      </p>
      <p class="muted">
        Base de municipios: Apéndice A-4 (misma fuente que
        <a href="https://kmauqs.github.io/NSR-10/consolidado-ley-400-nsr10.html" target="_blank" rel="noopener">consolidado NSR-10</a>).
        Microzonificación y PSA SGC: <a href="Espectros/ESPECTROS-SGC-SGC2026pqqmro.xlsx">ESPECTROS-SGC-SGC2026pqqmro.xlsx</a>.
        Requiere abrir el informe mediante un servidor local (<code>fetch</code> de JSON).
      </p>
      <div class="ch7-legend-colors">
        <span class="c-nsr">NSR-10 sin reducir</span>
        <span class="c-nsrr">NSR-10 / R</span>
        <span class="c-micro">Microzonificación</span>
        <span class="c-ew">Sa EW (2026)</span>
        <span class="c-ns">Sa NS (2026)</span>
        <span class="c-v">Sa V (2026)</span>
      </div>
      <div class="ch7-grid">
        <div class="ch7-panel">
          <label for="ch7-dept">Departamento</label>
          <select id="ch7-dept"></select>
          <label for="ch7-mun">Municipio</label>
          <select id="ch7-mun"></select>
          <label for="ch7-uso">Grupo de uso (A.2.5) — coeficiente I</label>
          <select id="ch7-uso"></select>
          <label for="ch7-perfil">Tipo de perfil de suelo (tabla A.2.4-1)</label>
          <select id="ch7-perfil"></select>
          <div id="ch7-micro-wrap" hidden>
            <p class="muted" id="ch7-micro-fuente" style="margin:0.6rem 0 0.2rem"></p>
            <label class="ch7-check"><input type="checkbox" id="ch7-use-micro" /> Usar espectro de microzonificación (naranja)</label>
            <label for="ch7-micro-zona">Zona / tipo de suelo (microzonificación)</label>
            <select id="ch7-micro-zona"></select>
          </div>
          <label class="ch7-check"><input type="checkbox" id="ch7-apply-R" checked /> Aplicar coeficiente de disipación R (A.3 / uso en fuerzas de diseño)</label>
          <label for="ch7-R">Coeficiente R</label>
          <input type="number" id="ch7-R" min="1" max="8" step="0.5" value="3.5" />
          <label class="ch7-check"><input type="checkbox" id="ch7-show-proc" /> Mostrar espectros de respuesta procesados (10-ago-2026, §6.1)</label>
          <label for="ch7-proc-station">Estación (procesados)</label>
          <select id="ch7-proc-station"></select>
          <label class="ch7-check"><input type="checkbox" id="ch7-show-sgc" /> Mostrar espectros automáticos SGC (Excel PSA)</label>
          <label for="ch7-sgc-station">Estación (SGC)</label>
          <select id="ch7-sgc-station"></select>
          <div class="ch7-actions">
            <button type="button" id="ch7-update">Actualizar gráficos</button>
            <button type="button" id="ch7-download" class="secondary">Descargar CSV</button>
          </div>
          <div id="ch7-params" style="margin-top:0.75rem"></div>
          <p class="muted" id="ch7-status">Cargando datos…</p>
        </div>
        <div class="ch7-charts">
          <div class="ch7-chart-box"><canvas id="ch7-chart-sa" aria-label="Espectro de aceleraciones"></canvas></div>
          <div class="ch7-chart-box"><canvas id="ch7-chart-sd" aria-label="Espectro de desplazamientos"></canvas></div>
        </div>
      </div>
      <p class="note" style="margin-top:0.8rem">
        El CSV exportado tiene en la primera columna el periodo <code>T_s</code> y en las
        columnas siguientes las ordenadas elásticas mostradas (Sa en g, Sd en m), incluyendo
        NSR-10, NSR-10/R, microzonificación y, si aplica, componentes de estaciones 2026.
        CBOCA permanece excluida del modo “todas” por ser dato atípico.
      </p>
    </section>

    <section id="referencias">
      <h2>8. Referencias</h2>
      <ol>
        <li>Servicio Geológico Colombiano (SGC). Red Nacional de Acelerógrafos (RNAC). Acelerogramas y espectros del evento <strong>SGC2026pqqmro</strong> (2026-08-10).</li>
        <li>SGC. ShakeMap — <code>info.json</code>, <code>grid.xml</code>, <code>stationlist.json</code>, <code>uncertainty.xml</code>.</li>
        <li>Nigam, N. C. &amp; Jennings, P. C. (1969). <em>Calculation of Response Spectra from Strong-Motion Earthquake Records.</em> BSSA, 59(2), 909–922.</li>
        <li>Butterworth, S. (1930). <em>On the Theory of Filter Amplifiers.</em> Wireless Engineer.</li>
        <li>Boore, D. M. Trabajos sobre corrección de línea base y filtrado de acelerogramas.</li>
        <li>Chopra, A. K. <em>Dynamics of Structures.</em></li>
        <li>The ObsPy Development Team. ObsPy: A Python Framework for Seismology.</li>
        <li>AIS. <strong>NSR-10</strong> — Reglamento Colombiano de Construcción Sismo Resistente, Título A (en particular A.2.4–A.2.6, A.2.5, Apéndice A-4).</li>
        <li>INGEOMINAS / SGC. Microzonificación y respuesta de sitio en el Eje Cafetero.</li>
        <li>Documentación del proyecto:
          <a href="docs/metodos_procesamiento_y_espectro.md">metodología</a>,
          <a href="docs/guia_amplificacion_efectos_sitio.md">amplificación por sitio</a>.
        </li>
        <li>Datos tabulares de apoyo: <a href="Espectros/ESPECTROS-SGC-SGC2026pqqmro.xlsx">ESPECTROS-SGC-SGC2026pqqmro.xlsx</a>; municipios A-4 en <code>output/data/municipios_nsr10.json</code>.</li>
      </ol>
    </section>

    <footer>
      <strong>NEXUS CREATIO</strong> · Informe técnico de datos y procesamiento — evaluación de demanda sísmica.
      Para diseño reglamentario prevalecen NSR vigente y la microzonificación oficial del municipio.
      · <a href="README.md">README.md</a>
      · <a href="https://kmauqs.github.io/NSR-10/index.html">Portada NSR-10</a>
    </footer>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <script src="js/espectro-diseno-nsr10.js"></script>
</body>
</html>
"""
    OUT.write_text(html_doc, encoding="utf-8")
    print(f"Wrote {OUT} with {len(rows)} stations and {len(figures)} analysis cards")


if __name__ == "__main__":
    main()

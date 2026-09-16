"""
Procesamiento de acelerogramas SGC (.ANC y MiniSEED) — Sismo 10-ago-2026 Eje Cafetero.
Evento: SGC2026pqqmro | M7.4 | San José del Palmar - Chocó

AVISO DE CALIDAD: la estación CBOCA (Pereira) produce amplitudes atípicas respecto
a la propagación del sismo y a los daños reales en Pereira (ciudad más afectada).
Puede estar defectuosa; NO usar CBOCA en análisis estadísticos ni modelaciones
detalladas. Ver README.md y docs/metodos_procesamiento_y_espectro.md §9.1.

Pipeline:
  1) Lectura de estaciones .ANC y/o MiniSEED (ObsPy)
  2) Corrección de línea base (demean + detrend + taper) → extremos ~0
  3) Filtro pasabanda Butterworth 0.10–25 Hz (ruido fuera del rango estructural)
  4) Export CSV de aceleración ajustada
  5) Espectro de respuesta elástico (ζ=5%, T=0–4 s) → CSV por estación

Prioridad: si hay .ANC y MiniSEED para la misma estación, se usa el .ANC.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from numba import njit
from obspy import Stream, Trace, UTCDateTime, read
from scipy.signal import butter, filtfilt

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "SGC-Data"
OUT_SENALES = ROOT / "output" / "senales"
OUT_ESPECTROS = ROOT / "output" / "espectros"
OUT_META = ROOT / "output"

EVENT_ORIGIN = UTCDateTime("2026-08-10T12:34:27.000000Z")
DAMPING = 0.05
T_MAX = 4.0
DT_SPECTRUM = 0.01  # paso de periodo (s)
FREQ_LOW = 0.10  # Hz — corta deriva / ruido de muy baja frecuencia
FREQ_HIGH = 25.0  # Hz — elimina ruido de muy alta frecuencia
TAPER_PCT = 0.05  # 5% cosine taper en cada extremo
G_CMS2 = 981.0  # cm/s^2 por g
# Ventana de análisis para MiniSEED largos (s antes / después del origen o del pico)
MSEED_PRE_EVENT_S = 30.0
MSEED_POST_EVENT_S = 480.0
MSEED_WINDOW_S = MSEED_PRE_EVENT_S + MSEED_POST_EVENT_S
# Sensibilidad opcional: cuentas → cm/s^2 (data_cms2 = data_counts / MSEED_COUNTS_PER_CMS2).
# None = asumir que el MiniSEED ya está en cm/s^2 (o unidades coherentes tras demean).
MSEED_COUNTS_PER_CMS2: float | None = None

# Estaciones con registro no confiable para análisis / modelación
ATYPICAL_STATIONS = {
    "CBOCA": (
        "Dato atípico respecto a propagación del sismo y daños reales en Pereira "
        "(ciudad más afectada). Estación posiblemente defectuosa. "
        "No emplear en análisis estadísticos ni modelaciones detalladas."
    ),
}

# Mapeo de códigos de canal SEED → componente de ingeniería
_CHAN_EW = {"HNE", "BHE", "EHE", "HHE", "ENE", "HN1", "BH1", "E"}
_CHAN_NS = {"HNN", "BHN", "EHN", "HHN", "ENN", "HN2", "BH2", "N"}
_CHAN_VER = {"HNZ", "BHZ", "EHZ", "HHZ", "ENZ", "Z"}



def parse_anc(path: Path) -> dict:
    """Lee un archivo .ANC del SGC (aceleración en cm/s^2, columnas EW, VER, NS)."""
    text = path.read_text(encoding="latin-1", errors="replace")
    lines = text.splitlines()

    meta: dict = {"path": str(path), "filename": path.name}
    data_start = 0
    for i, line in enumerate(lines):
        if "EW" in line and "VER" in line and "NS" in line:
            data_start = i + 1
            break
        key_match = re.match(
            r"^(CODIGO DE LA ESTACION|ESTACION|LATITUD DE LA ESTACION \(GRADOS\)|"
            r"LONGITUD DE LA ESTACION \(GRADOS\)|DISTANCIA EPICENTRAL|"
            r"DISTANCIA HIPOCENTRAL|INTERVALO DE MUESTREO \(SEGUNDOS\)|"
            r"NUMERO DE DATOS|DURACION \(SEGUNDOS\)|UNIDADES)\s*:?\s*(.*)$",
            line.strip(),
            re.IGNORECASE,
        )
        if key_match:
            key, val = key_match.group(1).upper(), key_match.group(2).strip()
            meta[key] = val

    station = meta.get("CODIGO DE LA ESTACION") or meta.get("ESTACION", path.stem)
    station = station.strip().split()[0]

    dt = float(str(meta.get("INTERVALO DE MUESTREO (SEGUNDOS)", "0.005")).replace(",", "."))
    n_expected = int(float(str(meta.get("NUMERO DE DATOS", "0")).replace(",", ".")))

    ew, ver, ns = [], [], []
    for line in lines[data_start:]:
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            ew.append(float(parts[0]))
            ver.append(float(parts[1]))
            ns.append(float(parts[2]))
        except ValueError:
            continue

    ew_a = np.asarray(ew, dtype=np.float64)
    ver_a = np.asarray(ver, dtype=np.float64)
    ns_a = np.asarray(ns, dtype=np.float64)

    if n_expected and len(ew_a) != n_expected:
        print(f"  [aviso] {station}: {len(ew_a)} muestras vs {n_expected} en cabecera")

    lat = float(str(meta.get("LATITUD DE LA ESTACION (GRADOS)", "nan")).split()[0])
    lon = float(str(meta.get("LONGITUD DE LA ESTACION (GRADOS)", "nan")).split()[0])
    repi = str(meta.get("DISTANCIA EPICENTRAL", "")).replace("km", "").strip()
    rhyp = str(meta.get("DISTANCIA HIPOCENTRAL", "")).replace("km", "").strip()

    return {
        "station": station,
        "lat": lat,
        "lon": lon,
        "repi_km": float(repi) if repi else None,
        "rhyp_km": float(rhyp) if rhyp else None,
        "dt": dt,
        "npts": len(ew_a),
        "duration_s": (len(ew_a) - 1) * dt,
        "units": meta.get("UNIDADES", "cm/s^2"),
        "ew": ew_a,
        "ver": ver_a,
        "ns": ns_a,
        "filename": path.name,
        "source_format": "ANC",
    }


def _channel_component(code: str) -> str | None:
    """Clasifica canal SEED en ew / ns / ver."""
    c = (code or "").upper().strip()
    if c in _CHAN_EW:
        return "ew"
    if c in _CHAN_NS:
        return "ns"
    if c in _CHAN_VER:
        return "ver"
    if len(c) >= 1:
        last = c[-1]
        if last in ("E", "1"):
            return "ew"
        if last in ("N", "2"):
            return "ns"
        if last in ("Z", "3"):
            return "ver"
    return None


def _band_rank(channel: str) -> int:
    """Prioriza acelerógrafos (HN/BN/EN) sobre velocímetros (HH/BH/EH)."""
    c = channel.upper()
    if c.startswith(("HN", "BN", "EN")):
        return 0
    if c.startswith(("HH", "BH", "EH")):
        return 1
    return 2


def _pick_component_traces(traces: list[Trace]) -> dict[str, Trace] | None:
    """Elige un trío EW/NS/VER priorizando HN* y location '10'."""
    by_comp: dict[str, list[Trace]] = defaultdict(list)
    for tr in traces:
        comp = _channel_component(tr.stats.channel)
        if comp:
            by_comp[comp].append(tr)
    if not all(k in by_comp for k in ("ew", "ns", "ver")):
        return None

    def score(tr: Trace) -> tuple:
        loc = tr.stats.location or ""
        return (_band_rank(tr.stats.channel), 0 if loc in ("10", "00", "") else 1, loc, tr.stats.channel)

    return {comp: sorted(cands, key=score)[0] for comp, cands in by_comp.items()}


def _align_three(tr_ew: Trace, tr_ns: Trace, tr_ver: Trace) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, UTCDateTime]:
    """Recorta al intervalo común y remuestrea a la delta mínima si hace falta."""
    st = Stream([tr_ew.copy(), tr_ns.copy(), tr_ver.copy()])
    st.merge(method=1, fill_value="interpolate")
    start = max(tr.stats.starttime for tr in st)
    end = min(tr.stats.endtime for tr in st)
    if end <= start:
        raise ValueError("Sin solape temporal entre componentes MiniSEED")
    st.trim(start, end, pad=False)
    dt = min(tr.stats.delta for tr in st)
    for tr in st:
        if abs(tr.stats.delta - dt) > 1e-9:
            tr.interpolate(sampling_rate=1.0 / dt, method="lanczos", a=4)
    n = min(tr.stats.npts for tr in st)
    for tr in st:
        tr.data = tr.data[:n]
    ordered: dict[str, np.ndarray] = {}
    for tr in st:
        comp = _channel_component(tr.stats.channel)
        if comp:
            ordered[comp] = tr.data.astype(np.float64)
    return ordered["ew"], ordered["ver"], ordered["ns"], float(dt), start


def _window_arrays(
    ew: np.ndarray,
    ver: np.ndarray,
    ns: np.ndarray,
    dt: float,
    start: UTCDateTime,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """
    Recorta ventana de análisis:
    - si el origen del evento cae en el registro → [t0-pre, t0+post]
    - si no → ventana de MSEED_WINDOW_S centrada en el pico de |acc| horizontal
    """
    n = len(ew)
    duration = (n - 1) * dt
    end = start + duration
    note = "full"

    if start <= EVENT_ORIGIN <= end:
        i0 = max(0, int((EVENT_ORIGIN - MSEED_PRE_EVENT_S - start) / dt))
        i1 = min(n, int((EVENT_ORIGIN + MSEED_POST_EVENT_S - start) / dt))
        note = f"event_window [{EVENT_ORIGIN - MSEED_PRE_EVENT_S} .. {EVENT_ORIGIN + MSEED_POST_EVENT_S}]"
    else:
        # pico en media geométrica aproximada |ew|+|ns|
        env = np.abs(ew) + np.abs(ns)
        peak = int(np.argmax(env))
        half = int(MSEED_WINDOW_S / (2 * dt))
        i0 = max(0, peak - half)
        i1 = min(n, i0 + int(MSEED_WINDOW_S / dt))
        i0 = max(0, i1 - int(MSEED_WINDOW_S / dt))
        note = (
            f"peak_window (origen {EVENT_ORIGIN} fuera del registro "
            f"{start} .. {end}); centrado en muestra {peak}"
        )

    if i1 - i0 < int(5.0 / dt):
        raise ValueError(f"Ventana MiniSEED demasiado corta ({i1 - i0} muestras)")

    return ew[i0:i1].copy(), ver[i0:i1].copy(), ns[i0:i1].copy(), note


def parse_mseed(path: Path) -> list[dict]:
    """
    Lee un archivo MiniSEED (posiblemente multi-estación) y devuelve registros
    con la misma estructura que parse_anc (aceleración EW/VER/NS).
    """
    st = read(str(path))
    by_station: dict[str, list[Trace]] = defaultdict(list)
    for tr in st:
        by_station[tr.stats.station].append(tr)

    records: list[dict] = []
    for station, traces in sorted(by_station.items()):
        picked = _pick_component_traces(traces)
        if not picked:
            print(f"  [aviso] {path.name} / {station}: no se halló trío EW-NS-VER; omitido")
            continue
        try:
            ew, ver, ns, dt, start = _align_three(picked["ew"], picked["ns"], picked["ver"])
            ew, ver, ns, win_note = _window_arrays(ew, ver, ns, dt, start)
        except Exception as exc:
            print(f"  [aviso] {path.name} / {station}: {exc}; omitido")
            continue

        raw_mean = float(np.mean(np.abs(ew)))
        count_like = raw_mean > 1.0e4
        if MSEED_COUNTS_PER_CMS2 and MSEED_COUNTS_PER_CMS2 > 0:
            ew = ew / MSEED_COUNTS_PER_CMS2
            ver = ver / MSEED_COUNTS_PER_CMS2
            ns = ns / MSEED_COUNTS_PER_CMS2
            units = "cm/s^2"
        else:
            units = "cm/s^2 (asumido)"
            if count_like:
                units = "counts->demean (verificar sensibilidad)"

        records.append(
            {
                "station": station,
                "lat": float("nan"),
                "lon": float("nan"),
                "repi_km": None,
                "rhyp_km": None,
                "dt": dt,
                "npts": len(ew),
                "duration_s": (len(ew) - 1) * dt,
                "units": units,
                "ew": ew,
                "ver": ver,
                "ns": ns,
                "filename": path.name,
                "source_format": "MiniSEED",
                "mseed_window": win_note,
                "network": picked["ew"].stats.network,
                "location": picked["ew"].stats.location,
                "mseed_count_like": count_like and not (MSEED_COUNTS_PER_CMS2 and MSEED_COUNTS_PER_CMS2 > 0),
                "mseed_raw_mean_abs": raw_mean,
            }
        )
    return records


def discover_input_records() -> list[dict]:
    """Descubre .ANC y MiniSEED; si hay ambas para una estación, prioriza .ANC."""
    anc_files: list[Path] = []
    seen_anc: set[str] = set()
    for p in sorted(DATA_DIR.glob("*.anc")) + sorted(DATA_DIR.glob("*.ANC")):
        key = p.name.lower()
        if key not in seen_anc:
            seen_anc.add(key)
            anc_files.append(p)

    mseed_files: list[Path] = []
    seen_mseed: set[str] = set()
    for pattern in ("*.mseed", "*.MSEED", "*.miniseed", "*.MiniSEED"):
        for p in sorted(DATA_DIR.glob(pattern)):
            key = p.name.lower()
            if key not in seen_mseed:
                seen_mseed.add(key)
                mseed_files.append(p)

    by_station: dict[str, dict] = {}
    for path in anc_files:
        rec = parse_anc(path)
        by_station[rec["station"]] = rec
        print(f"  [ANC] {rec['station']} <- {path.name}")

    for path in mseed_files:
        print(f"  [MSEED] leyendo {path.name}...")
        for rec in parse_mseed(path):
            stn = rec["station"]
            if stn in by_station and by_station[stn].get("source_format") == "ANC":
                print(f"  [MSEED] {stn}: omitido (ya hay .ANC)")
                continue
            if stn in by_station and by_station[stn].get("source_format") == "MiniSEED":
                print(f"  [MSEED] {stn}: reemplaza registro previo de {by_station[stn]['filename']}")
            if rec.get("mseed_count_like"):
                print(
                    f"  [aviso] {stn}: amplitudes tipicas de cuentas "
                    f"(media |EW|~{rec.get('mseed_raw_mean_abs', 0):.0f}). "
                    "Sin respuesta instrumental; se demeanea en el pipeline. "
                    "Defina MSEED_COUNTS_PER_CMS2 si conoce la sensibilidad."
                )
            by_station[stn] = rec
            print(f"  [MSEED] {stn} <- {path.name} | {rec.get('mseed_window', '')}")

    return [by_station[k] for k in sorted(by_station)]



def cosine_taper(n: int, pct: float = TAPER_PCT) -> np.ndarray:
    """Ventana coseno en ambos extremos (fracción pct de la longitud total en cada lado)."""
    w = np.ones(n, dtype=np.float64)
    m = max(1, int(n * pct))
    if 2 * m >= n:
        m = max(1, n // 10)
    ramp = 0.5 * (1.0 - np.cos(np.pi * np.arange(m) / m))
    w[:m] = ramp
    w[-m:] = ramp[::-1]
    return w


def baseline_and_filter(acc: np.ndarray, dt: float) -> np.ndarray:
    """
    Corrección para que la señal comience y termine cerca de cero, y filtrado.

    1. Remoción de media (evita offset constante → falsa velocidad/desplazamiento).
    2. Detrend lineal (elimina deriva de línea base).
    3. Taper coseno 5% (fuerza extremos a cero antes del filtrado).
    4. Pasabanda Butterworth 4 polos, 0.10–25 Hz (filtfilt, fase cero).
    5. Segundo taper suave para asegurar extremos ~0 tras el filtro.
    """
    y = acc.astype(np.float64).copy()
    y -= np.mean(y)
    # detrend lineal
    t = np.arange(len(y), dtype=np.float64) * dt
    p = np.polyfit(t, y, 1)
    y -= np.polyval(p, t)
    y *= cosine_taper(len(y), TAPER_PCT)

    fs = 1.0 / dt
    # Asegurar Nyquist > FREQ_HIGH
    f_hi = min(FREQ_HIGH, 0.45 * fs)
    f_lo = FREQ_LOW
    if f_lo >= f_hi:
        raise ValueError(f"Banda inválida: {f_lo}–{f_hi} Hz (fs={fs})")

    # ObsPy bandpass (Butterworth, corners=4) vía filtfilt equivalente
    nyq = 0.5 * fs
    b, a = butter(4, [f_lo / nyq, f_hi / nyq], btype="band")
    y = filtfilt(b, a, y)
    y *= cosine_taper(len(y), TAPER_PCT * 0.5)
    # Forzar media residual ~0
    y -= np.mean(y)
    return y


def to_obspy_stream(rec: dict, components: dict[str, np.ndarray]) -> Stream:
    """Construye Stream ObsPy (útil para inspección / export MiniSEED opcional)."""
    st = Stream()
    chan_map = {"ew": "HNE", "ver": "HNZ", "ns": "HNN"}
    for key, data in components.items():
        tr = Trace(data=data.astype(np.float64))
        tr.stats.network = "CM"
        tr.stats.station = rec["station"]
        tr.stats.channel = chan_map[key]
        tr.stats.delta = rec["dt"]
        tr.stats.starttime = EVENT_ORIGIN
        tr.stats.sampling_rate = 1.0 / rec["dt"]
        tr.stats.calib = 1.0
        st.append(tr)
    return st


@njit(cache=True)
def _nj_one_period(acc: np.ndarray, dt: float, T: float, z: float) -> tuple[float, float, float]:
    """Nigam-Jennings (1969) para un periodo: retorna Sa, Sv, Sd."""
    w = 2.0 * np.pi / T
    wd = w * np.sqrt(1.0 - z * z)
    e = np.exp(-z * w * dt)
    sin_wd = np.sin(wd * dt)
    cos_wd = np.cos(wd * dt)

    a11 = e * (z * w / wd * sin_wd + cos_wd)
    a12 = e * (sin_wd / wd)
    a21 = -e * (w * w / wd) * sin_wd
    a22 = e * (cos_wd - z * w / wd * sin_wd)

    w2 = w * w
    w3 = w2 * w
    b11 = (
        e * (((2 * z * z - 1) / (w2 * dt) + z / w) * sin_wd / wd + (2 * z / (w3 * dt) + 1 / w2) * cos_wd)
        - 2 * z / (w3 * dt)
    )
    b12 = (
        -e * (((2 * z * z - 1) / (w2 * dt) + z / w) * sin_wd / wd + (2 * z / (w3 * dt)) * cos_wd)
        - 1 / w2
        + 2 * z / (w3 * dt)
    )
    b21 = (
        e * ((2 * z * z - 1) / (w2 * dt) * cos_wd - ((2 * z * z - 1) / (w * dt) + z) * sin_wd / wd)
        + (1 - 2 * z * z) / (w2 * dt)
    )
    b22 = (
        -e * ((2 * z * z - 1) / (w2 * dt) * cos_wd - ((2 * z * z - 1) / (w * dt)) * sin_wd / wd)
        - (1 - 2 * z * z) / (w2 * dt)
    )

    u = 0.0
    v = 0.0
    u_max = 0.0
    v_max = 0.0
    a_max = 0.0
    n = acc.shape[0]
    for k in range(n - 1):
        ag0 = acc[k]
        ag1 = acc[k + 1]
        u_new = a11 * u + a12 * v + b11 * ag0 + b12 * ag1
        v_new = a21 * u + a22 * v + b21 * ag0 + b22 * ag1
        a_abs = abs(-2.0 * z * w * v_new - w2 * u_new)
        au = abs(u_new)
        av = abs(v_new)
        if au > u_max:
            u_max = au
        if av > v_max:
            v_max = av
        if a_abs > a_max:
            a_max = a_abs
        u = u_new
        v = v_new
    return a_max, v_max, u_max


def elastic_response_spectrum(
    acc: np.ndarray,
    dt: float,
    periods: np.ndarray,
    damping: float = DAMPING,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Espectro de respuesta elastico (SDOF) — Nigam-Jennings.

    Sa = max|aceleracion absoluta|, Sv = max|vel|, Sd = max|desp|.
    Unidades coherentes con acc (cm/s2 -> Sd en cm, Sv en cm/s, Sa en cm/s2).
    """
    sa = np.zeros(len(periods), dtype=np.float64)
    sv = np.zeros(len(periods), dtype=np.float64)
    sd = np.zeros(len(periods), dtype=np.float64)
    pga = float(np.max(np.abs(acc)))
    acc64 = np.ascontiguousarray(acc, dtype=np.float64)

    for i, T in enumerate(periods):
        if T < 1e-6:
            sa[i] = pga
            continue
        sa[i], sv[i], sd[i] = _nj_one_period(acc64, dt, float(T), damping)

    return sa, sv, sd


def geometric_mean_horizontal(sa_ew: np.ndarray, sa_ns: np.ndarray) -> np.ndarray:
    """Media geométrica de componentes horizontales (práctica habitual en ingeniería)."""
    return np.sqrt(np.abs(sa_ew) * np.abs(sa_ns))


def write_signal_csv(path: Path, t: np.ndarray, ew: np.ndarray, ver: np.ndarray, ns: np.ndarray) -> None:
    header = (
        "time_s,acc_EW_cm_s2,acc_VER_cm_s2,acc_NS_cm_s2,"
        "acc_EW_g,acc_VER_g,acc_NS_g"
    )
    data = np.column_stack([t, ew, ver, ns, ew / G_CMS2, ver / G_CMS2, ns / G_CMS2])
    np.savetxt(path, data, delimiter=",", header=header, comments="", fmt="%.8e")


def write_spectrum_csv(
    path: Path,
    periods: np.ndarray,
    sa_ew,
    sv_ew,
    sd_ew,
    sa_ns,
    sv_ns,
    sd_ns,
    sa_ver,
    sv_ver,
    sd_ver,
    sa_rotD50,
) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "T_s",
                "Sa_EW_g",
                "Sv_EW_cm_s",
                "Sd_EW_cm",
                "Sa_NS_g",
                "Sv_NS_cm_s",
                "Sd_NS_cm",
                "Sa_VER_g",
                "Sv_VER_cm_s",
                "Sd_VER_cm",
                "Sa_RotD50_approx_g",
                "PSA_EW_g",
                "PSA_NS_g",
                "PSA_geo_mean_g",
            ]
        )
        for i, T in enumerate(periods):
            omega = 2.0 * np.pi / T if T > 1e-6 else np.inf
            psa_ew = (omega**2 * sd_ew[i]) / G_CMS2 if T > 1e-6 else sa_ew[i] / G_CMS2
            psa_ns = (omega**2 * sd_ns[i]) / G_CMS2 if T > 1e-6 else sa_ns[i] / G_CMS2
            psa_geo = np.sqrt(abs(psa_ew) * abs(psa_ns))
            w.writerow(
                [
                    f"{T:.4f}",
                    f"{sa_ew[i] / G_CMS2:.8e}",
                    f"{sv_ew[i]:.8e}",
                    f"{sd_ew[i]:.8e}",
                    f"{sa_ns[i] / G_CMS2:.8e}",
                    f"{sv_ns[i]:.8e}",
                    f"{sd_ns[i]:.8e}",
                    f"{sa_ver[i] / G_CMS2:.8e}",
                    f"{sv_ver[i]:.8e}",
                    f"{sd_ver[i]:.8e}",
                    f"{sa_rotD50[i] / G_CMS2:.8e}",
                    f"{psa_ew:.8e}",
                    f"{psa_ns:.8e}",
                    f"{psa_geo:.8e}",
                ]
            )


def process_all() -> None:
    OUT_SENALES.mkdir(parents=True, exist_ok=True)
    OUT_ESPECTROS.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("SISMO 10-ago-2026 | SGC2026pqqmro | M7.4 San José del Palmar - Chocó")
    print(f"Filtro: Butterworth 4 polos, {FREQ_LOW}-{FREQ_HIGH} Hz | damping={DAMPING*100:.0f}%")
    print(f"Entrada: .ANC y MiniSEED en {DATA_DIR} (prioridad .ANC si hay ambas)")
    print("=" * 72)

    print("\nDescubrimiento de registros...")
    records = discover_input_records()
    if not records:
        raise SystemExit(f"No se encontraron .ANC ni MiniSEED en {DATA_DIR}")

    periods = np.arange(0.0, T_MAX + 0.5 * DT_SPECTRUM, DT_SPECTRUM)
    catalog = []

    for rec in records:
        stn = rec["station"]
        src = rec.get("source_format", "?")
        print(f"\n>>> {rec['filename']} [{src}] -> {stn}")
        lat_s = f"{rec['lat']:.5f}" if rec["lat"] == rec["lat"] else "n/d"
        lon_s = f"{rec['lon']:.5f}" if rec["lon"] == rec["lon"] else "n/d"
        print(
            f"    Estacion {stn} | lat={lat_s}, lon={lon_s} | "
            f"Repi={rec['repi_km']} km | dt={rec['dt']} s | n={rec['npts']} | unidades={rec['units']}"
        )
        if rec.get("mseed_window"):
            print(f"    Ventana MiniSEED: {rec['mseed_window']}")

        ew = baseline_and_filter(rec["ew"], rec["dt"])
        ver = baseline_and_filter(rec["ver"], rec["dt"])
        ns = baseline_and_filter(rec["ns"], rec["dt"])

        # Actualizar npts/duration tras ventana MiniSEED
        rec["npts"] = len(ew)
        rec["duration_s"] = (len(ew) - 1) * rec["dt"]

        ends = {
            "EW": (ew[0], ew[-1]),
            "VER": (ver[0], ver[-1]),
            "NS": (ns[0], ns[-1]),
        }
        for comp, (a0, a1) in ends.items():
            print(f"    Extremos {comp}: inicio={a0:.3e}, fin={a1:.3e} cm/s2")

        t = np.arange(len(ew), dtype=np.float64) * rec["dt"]
        csv_sig = OUT_SENALES / f"{stn}_aceleracion_ajustada.csv"
        write_signal_csv(csv_sig, t, ew, ver, ns)
        print(f"    Senal -> {csv_sig.name}")

        print("    Calculando espectro de respuesta elastico...")
        sa_ew, sv_ew, sd_ew = elastic_response_spectrum(ew, rec["dt"], periods, DAMPING)
        sa_ns, sv_ns, sd_ns = elastic_response_spectrum(ns, rec["dt"], periods, DAMPING)
        sa_ver, sv_ver, sd_ver = elastic_response_spectrum(ver, rec["dt"], periods, DAMPING)
        sa_geo = geometric_mean_horizontal(sa_ew, sa_ns)

        csv_sp = OUT_ESPECTROS / f"{stn}_espectro_respuesta_elastico.csv"
        write_spectrum_csv(
            csv_sp,
            periods,
            sa_ew,
            sv_ew,
            sd_ew,
            sa_ns,
            sv_ns,
            sd_ns,
            sa_ver,
            sv_ver,
            sd_ver,
            sa_geo,
        )
        print(f"    Espectro -> {csv_sp.name}")

        pga_ew = float(np.max(np.abs(ew))) / G_CMS2
        pga_ns = float(np.max(np.abs(ns))) / G_CMS2
        pga_ver = float(np.max(np.abs(ver))) / G_CMS2
        sa_peak = float(np.max(sa_geo[1:])) / G_CMS2 if len(sa_geo) > 1 else 0.0
        t_peak = float(periods[1 + int(np.argmax(sa_geo[1:]))]) if len(sa_geo) > 1 else 0.0

        quality_flag = "ATYPICAL_DO_NOT_USE" if stn in ATYPICAL_STATIONS else "OK"
        quality_note = ATYPICAL_STATIONS.get(stn)
        if quality_note:
            print(f"    [CALIDAD] {stn}: ATYPICAL_DO_NOT_USE — no usar en analisis")

        catalog.append(
            {
                "station": stn,
                "latitude": rec["lat"] if rec["lat"] == rec["lat"] else None,
                "longitude": rec["lon"] if rec["lon"] == rec["lon"] else None,
                "repi_km": rec["repi_km"],
                "rhyp_km": rec["rhyp_km"],
                "dt_s": rec["dt"],
                "npts": rec["npts"],
                "duration_s": rec["duration_s"],
                "units_raw": rec["units"],
                "source_format": src,
                "filter_Hz": f"{FREQ_LOW}-{FREQ_HIGH}",
                "damping": DAMPING,
                "PGA_EW_g": round(pga_ew, 6),
                "PGA_NS_g": round(pga_ns, 6),
                "PGA_VER_g": round(pga_ver, 6),
                "PGA_H_geo_g": round(float(np.sqrt(pga_ew * pga_ns)), 6),
                "Sa_peak_H_geo_g": round(sa_peak, 6),
                "T_Sa_peak_s": round(t_peak, 4),
                "quality_flag": quality_flag,
                "quality_note": quality_note,
                "signal_csv": str(csv_sig.relative_to(ROOT)),
                "spectrum_csv": str(csv_sp.relative_to(ROOT)),
                "source_file": rec["filename"],
                "mseed_window": rec.get("mseed_window"),
            }
        )

        st = to_obspy_stream(rec, {"ew": ew, "ver": ver, "ns": ns})
        mseed_path = OUT_SENALES / f"{stn}_aceleracion_ajustada.mseed"
        st.write(str(mseed_path), format="MSEED")
        print(f"    MiniSEED -> {mseed_path.name}")

    # Resumen estaciones
    summary_path = OUT_META / "estaciones_identificadas.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "event_id": "SGC2026pqqmro",
                "origin_time_utc": "2026-08-10T12:34:27Z",
                "magnitude": 7.4,
                "location": "San José del Palmar - Chocó, Colombia",
                "hypocenter": {"lat": 4.99, "lon": -76.293, "depth_km": 103.0},
                "processing": {
                    "baseline": "demean + detrend lineal + taper coseno 5%",
                    "filter": f"Butterworth bandpass 4 polos, {FREQ_LOW}-{FREQ_HIGH} Hz, zero-phase",
                    "response_spectrum": (
                        f"Nigam-Jennings (numba), damping={DAMPING}, "
                        f"T=0-{T_MAX}s, dT={DT_SPECTRUM}s"
                    ),
                    "input_formats": [".ANC", "MiniSEED"],
                    "mseed_priority": "ANC sobre MiniSEED si ambas existen para la misma estacion",
                    "mseed_window_s": MSEED_WINDOW_S,
                    "acceleration_units_csv": "cm/s^2 y g",
                    "spectrum_units": "Sa en g; Sv en cm/s; Sd en cm",
                },
                "n_stations": len(catalog),
                "stations": catalog,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    # CSV resumen
    resum_csv = OUT_META / "resumen_estaciones.csv"
    with resum_csv.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "station",
            "source_format",
            "latitude",
            "longitude",
            "repi_km",
            "rhyp_km",
            "dt_s",
            "npts",
            "PGA_EW_g",
            "PGA_NS_g",
            "PGA_VER_g",
            "PGA_H_geo_g",
            "Sa_peak_H_geo_g",
            "T_Sa_peak_s",
            "quality_flag",
        ]
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in catalog:
            w.writerow(row)

    print("\n" + "=" * 72)
    print(f"Estaciones procesadas: {len(catalog)}")
    for c in catalog:
        repi = c["repi_km"]
        repi_s = f"{repi:5.1f} km" if isinstance(repi, (int, float)) else "  n/d"
        print(
            f"  {c['station']:6s}  [{c.get('source_format', '?'):8s}]  Repi={repi_s}  "
            f"PGA_H={c['PGA_H_geo_g']:.4f} g  Sa_peak={c['Sa_peak_H_geo_g']:.4f} g @ T={c['T_Sa_peak_s']} s"
        )
    print(f"\nResumen: {summary_path}")
    print(f"Resumen CSV: {resum_csv}")
    print("=" * 72)


if __name__ == "__main__":
    process_all()

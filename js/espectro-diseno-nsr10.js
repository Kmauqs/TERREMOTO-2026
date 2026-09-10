/**
 * Capítulo 7 — Herramienta de espectros de diseño NSR-10 (A.2.6)
 * y comparación con espectros del sismo SGC2026pqqmro.
 */
(function () {
  "use strict";

  const G = 9.81; // m/s²
  const COLORS = {
    nsr: "#c62828", // rojo — NSR-10 sin reducir
    nsrR: "#111111", // negro — NSR-10 / R
    micro: "#ef6c00", // naranja — microzonificación
    EW: "#e000a8",
    NS: "#1a5cff",
    VER: "#00a86b",
    GEO: "#14283b",
  };

  const FA_TABLE = {
    // Aa: 0.1, 0.2, 0.3, 0.4, 0.5 — Tabla A.2.4-3
    A: [0.8, 0.8, 0.8, 0.8, 0.8],
    B: [1.0, 1.0, 1.0, 1.0, 1.0],
    C: [1.2, 1.2, 1.1, 1.0, 1.0],
    D: [1.6, 1.4, 1.2, 1.1, 1.0],
    E: [2.5, 1.7, 1.2, 0.9, 0.9],
  };
  const FV_TABLE = {
    // Av: 0.1 … 0.5 — Tabla A.2.4-4
    A: [0.8, 0.8, 0.8, 0.8, 0.8],
    B: [1.0, 1.0, 1.0, 1.0, 1.0],
    C: [1.7, 1.6, 1.5, 1.4, 1.3],
    D: [2.4, 2.0, 1.8, 1.6, 1.5],
    E: [3.5, 3.2, 2.8, 2.4, 2.4],
  };
  const AA_COLS = [0.1, 0.2, 0.3, 0.4, 0.5];

  const USAGE = [
    { id: "I", I: 1.0, label: "Grupo I — ocupación normal (I = 1.00)" },
    { id: "II", I: 1.1, label: "Grupo II — ocupación especial (I = 1.10)" },
    {
      id: "III",
      I: 1.25,
      label: "Grupo III — atención a la comunidad (I = 1.25)",
    },
    { id: "IV", I: 1.5, label: "Grupo IV — indispensables (I = 1.50)" },
  ];

  const state = {
    munData: null,
    micro: null,
    sgc: null,
    proc: null,
    chartSa: null,
    chartSd: null,
    lastExport: null,
  };

  function interpTable(tableRow, intensity) {
    const x = Math.min(0.5, Math.max(0.1, intensity));
    let i = 0;
    while (i < AA_COLS.length - 1 && AA_COLS[i + 1] < x) i++;
    if (i >= AA_COLS.length - 1) return tableRow[tableRow.length - 1];
    const x0 = AA_COLS[i];
    const x1 = AA_COLS[i + 1];
    const y0 = tableRow[i];
    const y1 = tableRow[i + 1];
    return y0 + ((y1 - y0) * (x - x0)) / (x1 - x0);
  }

  function faFv(perfil, Aa, Av) {
    if (perfil === "F") {
      return { Fa: null, Fv: null, note: "Perfil F requiere estudio geotécnico de sitio (NSR-10)." };
    }
    return {
      Fa: interpTable(FA_TABLE[perfil], Aa),
      Fv: interpTable(FV_TABLE[perfil], Av),
      note: null,
    };
  }

  /** Espectro elástico NSR-10 A.2.6 (incluye rama T < T0). */
  function spectrumNSR10(Aa, Av, Fa, Fv, I, Tmax, dT) {
    const To = (0.1 * Av * Fv) / (Aa * Fa);
    const Tc = (0.48 * Av * Fv) / (Aa * Fa);
    const TL = 2.4 * Fv;
    const SaMax = 2.5 * Aa * Fa * I;
    const T = [];
    const Sa = [];
    for (let t = 0; t <= Tmax + 1e-12; t = +(t + dT).toFixed(4)) {
      let sa;
      if (t < To) {
        sa = SaMax * (0.4 + (0.6 * t) / To);
      } else if (t <= Tc) {
        sa = SaMax;
      } else if (t <= TL) {
        sa = (1.2 * Av * Fv * I) / t;
      } else {
        sa = (1.2 * Av * Fv * TL * I) / (t * t);
      }
      T.push(t);
      Sa.push(sa);
    }
    return { T, Sa, To, Tc, TL, SaMax, Aa, Av, Fa, Fv, I };
  }

  /** Micro tipo NSR (To,Tc,TL,Aa,Fa,Fv dados por zona). */
  function spectrumFromParams(p, I, Tmax, dT) {
    const Aa = p.Aa;
    const Fa = p.Fa;
    const To = p.To;
    const Tc = p.Tc;
    const TL = p.TL;
    const SaMax = 2.5 * Aa * Fa * I;
    const T = [];
    const Sa = [];
    for (let t = 0; t <= Tmax + 1e-12; t = +(t + dT).toFixed(4)) {
      let sa;
      if (t < To) sa = SaMax * (0.4 + (0.6 * t) / Math.max(To, 1e-6));
      else if (t <= Tc) sa = SaMax;
      else if (t <= TL) sa = (SaMax * Tc) / t;
      else sa = (SaMax * Tc * TL) / (t * t);
      T.push(t);
      Sa.push(sa);
    }
    return { T, Sa, To, Tc, TL, SaMax, Aa, Fa, Fv: p.Fv, I };
  }

  /** Armenia zonas numéricas (Sa*, Am, An, Fv). */
  function spectrumArmeniaNum(p, I, Tmax, dT) {
    const To = p.To;
    const Tc = p.Tc;
    const TL = p.TL;
    const SaStar = p.Sa_star * I;
    const Am = p.Am * I;
    const An = p.An;
    const Fv = p.Fv;
    const T = [];
    const Sa = [];
    for (let t = 0; t <= Tmax + 1e-12; t = +(t + dT).toFixed(4)) {
      let sa;
      if (t < To) sa = Am + ((SaStar - Am) * t) / Math.max(To, 1e-6);
      else if (t <= Tc) sa = SaStar;
      else if (t <= TL) sa = (An * Fv * I) / t;
      else sa = (An * Fv * TL * I) / (t * t);
      T.push(t);
      Sa.push(sa);
    }
    return { T, Sa, To, Tc, TL, SaMax: SaStar, I };
  }

  /** Manizales (Am, An, Fa, Fv). */
  function spectrumManizales(p, I, Tmax, dT) {
    const To = p.To;
    const Tc = p.Tc;
    const TL = p.TL;
    const Am = p.Am;
    const An = p.An;
    const Fv = p.Fv;
    const SaMax = 2.5 * Am * I;
    const T = [];
    const Sa = [];
    for (let t = 0; t <= Tmax + 1e-12; t = +(t + dT).toFixed(4)) {
      let sa;
      if (t < To) sa = Am * I + ((SaMax - Am * I) * t) / Math.max(To, 1e-6);
      else if (t <= Tc) sa = SaMax;
      else if (t <= TL) sa = (An * Fv * I) / t;
      else sa = (An * Fv * TL * I) / (t * t);
      T.push(t);
      Sa.push(sa);
    }
    return { T, Sa, To, Tc, TL, SaMax, I };
  }

  function saToSd(T, Sa) {
    // Sd [m] = Sa[g] * g * T² / (4π²)
    const k = G / (4 * Math.PI * Math.PI);
    return Sa.map((sa, i) => sa * k * T[i] * T[i]);
  }

  function $(id) {
    return document.getElementById(id);
  }

  function fillSelect(sel, items, getVal, getLabel, placeholder) {
    sel.innerHTML = "";
    if (placeholder) {
      const o = document.createElement("option");
      o.value = "";
      o.textContent = placeholder;
      sel.appendChild(o);
    }
    items.forEach((it) => {
      const o = document.createElement("option");
      o.value = getVal(it);
      o.textContent = getLabel(it);
      sel.appendChild(o);
    });
  }

  function currentMunicipio() {
    const dept = $("ch7-dept").value;
    const mun = $("ch7-mun").value;
    return state.munData.municipios.find(
      (m) => m.departamento === dept && m.municipio === mun
    );
  }

  function norm(s) {
    return String(s || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function microKeyForMun(m) {
    if (!m || !state.micro) return null;
    const munN = norm(m.municipio);
    const deptN = norm(m.departamento);
    for (const [k, v] of Object.entries(state.micro)) {
      if (norm(v.municipio) === munN && (norm(v.departamento) === deptN || deptN.includes(norm(v.departamento)) || norm(v.departamento).includes(deptN))) {
        return k;
      }
    }
    for (const key of Object.keys(state.micro)) {
      if (norm(key) === munN) return key;
    }
    return null;
  }

  function updateMunList() {
    const dept = $("ch7-dept").value;
    const list = state.munData.municipios
      .filter((m) => m.departamento === dept)
      .sort((a, b) => a.municipio.localeCompare(b.municipio, "es"));
    fillSelect(
      $("ch7-mun"),
      list,
      (m) => m.municipio,
      (m) => `${m.municipio} (Aa=${m.Aa}, Av=${m.Av})`,
      "— Municipio —"
    );
    updateMicroUI();
    updateParams();
  }

  function updateMicroUI() {
    const m = currentMunicipio();
    const key = microKeyForMun(m);
    const wrap = $("ch7-micro-wrap");
    const zonaSel = $("ch7-micro-zona");
    if (!key) {
      wrap.hidden = true;
      $("ch7-use-micro").checked = false;
      return;
    }
    wrap.hidden = false;
    const zonas = Object.keys(state.micro[key].zonas).sort((a, b) =>
      a.localeCompare(b, "es", { numeric: true })
    );
    fillSelect(
      zonaSel,
      zonas,
      (z) => z,
      (z) => `Zona ${z}`,
      "— Zona de microzonificación —"
    );
    $("ch7-micro-fuente").textContent = state.micro[key].fuente || "";
  }

  function updateParams() {
    const m = currentMunicipio();
    const perfil = $("ch7-perfil").value;
    const uso = USAGE.find((u) => u.id === $("ch7-uso").value) || USAGE[0];
    const box = $("ch7-params");
    if (!m) {
      box.innerHTML = "<p class='muted'>Seleccione departamento y municipio.</p>";
      return;
    }
    const { Fa, Fv, note } = faFv(perfil, m.Aa, m.Av);
    let html = `<ul class="compact">
      <li><strong>Aa</strong> = ${m.Aa} · <strong>Av</strong> = ${m.Av} · Amenaza: ${m.zona_amenaza}</li>
      <li><strong>I</strong> = ${uso.I.toFixed(2)} (Grupo ${uso.id})</li>`;
    if (Fa != null) {
      const To = (0.1 * m.Av * Fv) / (m.Aa * Fa);
      const Tc = (0.48 * m.Av * Fv) / (m.Aa * Fa);
      const TL = 2.4 * Fv;
      html += `<li><strong>Fa</strong> = ${Fa.toFixed(3)} · <strong>Fv</strong> = ${Fv.toFixed(3)} (perfil ${perfil})</li>
        <li><strong>T₀</strong> = ${To.toFixed(3)} s · <strong>Tc</strong> = ${Tc.toFixed(3)} s · <strong>TL</strong> = ${TL.toFixed(3)} s</li>`;
    } else {
      html += `<li class="alert" style="list-style:none">${note}</li>`;
    }
    html += "</ul>";
    box.innerHTML = html;
  }

  function buildDatasets() {
    const m = currentMunicipio();
    const perfil = $("ch7-perfil").value;
    const uso = USAGE.find((u) => u.id === $("ch7-uso").value) || USAGE[0];
    const R = Math.max(1, parseFloat($("ch7-R").value) || 1);
    const applyR = $("ch7-apply-R").checked;
    const Tmax = 4.0;
    const dT = 0.02;
    const datasetsSa = [];
    const datasetsSd = [];
    const exportCols = { T_s: [] };

    if (!m) return { datasetsSa, datasetsSd, exportCols };

    const { Fa, Fv, note } = faFv(perfil, m.Aa, m.Av);
    if (Fa == null) {
      $("ch7-params").innerHTML += `<p class="alert">${note}</p>`;
    } else {
      const sp = spectrumNSR10(m.Aa, m.Av, Fa, Fv, uso.I, Tmax, dT);
      exportCols.T_s = sp.T.slice();
      exportCols.Sa_NSR10_g = sp.Sa.slice();
      exportCols.Sd_NSR10_m = saToSd(sp.T, sp.Sa);
      datasetsSa.push({
        label: "NSR-10 Sa (sin reducir)",
        data: sp.T.map((t, i) => ({ x: t, y: sp.Sa[i] })),
        borderColor: COLORS.nsr,
        backgroundColor: COLORS.nsr,
        borderWidth: 2.2,
        pointRadius: 0,
        tension: 0,
      });
      datasetsSd.push({
        label: "NSR-10 Sd (sin reducir)",
        data: sp.T.map((t, i) => ({ x: t, y: exportCols.Sd_NSR10_m[i] })),
        borderColor: COLORS.nsr,
        borderWidth: 2.2,
        pointRadius: 0,
        tension: 0,
      });
      if (applyR) {
        const saR = sp.Sa.map((v) => v / R);
        const sdR = saToSd(sp.T, saR);
        exportCols[`Sa_NSR10_R${R}_g`] = saR;
        exportCols[`Sd_NSR10_R${R}_m`] = sdR;
        datasetsSa.push({
          label: `NSR-10 Sa / R (R=${R})`,
          data: sp.T.map((t, i) => ({ x: t, y: saR[i] })),
          borderColor: COLORS.nsrR,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0,
        });
        datasetsSd.push({
          label: `NSR-10 Sd / R (R=${R})`,
          data: sp.T.map((t, i) => ({ x: t, y: sdR[i] })),
          borderColor: COLORS.nsrR,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0,
        });
      }
    }

    // Microzonificación
    if ($("ch7-use-micro").checked) {
      const key = microKeyForMun(m);
      const zid = $("ch7-micro-zona").value;
      if (key && zid && state.micro[key].zonas[zid]) {
        const zp = state.micro[key].zonas[zid];
        let spM;
        if (zp.tipo === "manizales") spM = spectrumManizales(zp, uso.I, Tmax, dT);
        else if (zp.tipo === "armenia_num") spM = spectrumArmeniaNum(zp, uso.I, Tmax, dT);
        else spM = spectrumFromParams(zp, uso.I, Tmax, dT);
        const sdM = saToSd(spM.T, spM.Sa);
        exportCols.Sa_Micro_g = alignTo(exportCols.T_s, spM.T, spM.Sa);
        exportCols.Sd_Micro_m = alignTo(exportCols.T_s, spM.T, sdM);
        datasetsSa.push({
          label: `Microzonificación ${key} zona ${zid}`,
          data: spM.T.map((t, i) => ({ x: t, y: spM.Sa[i] })),
          borderColor: COLORS.micro,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0,
        });
        datasetsSd.push({
          label: `Micro Sd ${key} zona ${zid}`,
          data: spM.T.map((t, i) => ({ x: t, y: sdM[i] })),
          borderColor: COLORS.micro,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0,
        });
      }
    }

    // Procesados 2026
    if ($("ch7-show-proc").checked && state.proc) {
      const stSel = $("ch7-proc-station").value;
      const codes =
        stSel === "ALL"
          ? Object.keys(state.proc).filter((c) => c !== "CBOCA")
          : [stSel];
      codes.forEach((code) => {
        const sp = state.proc[code];
        if (!sp) return;
        const comps = [
          ["EW", sp.Sa_EW_g, COLORS.EW],
          ["NS", sp.Sa_NS_g, COLORS.NS],
          ["V", sp.Sa_VER_g, COLORS.VER],
        ];
        comps.forEach(([lab, arr, col]) => {
          datasetsSa.push({
            label: `${code} proc. ${lab}`,
            data: sp.T_s.map((t, i) => ({ x: t, y: arr[i] })),
            borderColor: col,
            borderWidth: stSel === "ALL" ? 1 : 1.5,
            pointRadius: 0,
            tension: 0,
            borderDash: code === "CBOCA" ? [4, 3] : undefined,
          });
          const sd = saToSd(sp.T_s, arr);
          datasetsSd.push({
            label: `${code} Sd proc. ${lab}`,
            data: sp.T_s.map((t, i) => ({ x: t, y: sd[i] })),
            borderColor: col,
            borderWidth: stSel === "ALL" ? 1 : 1.5,
            pointRadius: 0,
            tension: 0,
          });
          if (stSel !== "ALL" && exportCols.T_s.length) {
            exportCols[`Sa_${code}_${lab}_g`] = alignTo(exportCols.T_s, sp.T_s, arr);
            exportCols[`Sd_${code}_${lab}_m`] = alignTo(exportCols.T_s, sp.T_s, sd);
          }
        });
      });
    }

    // SGC automáticos
    if ($("ch7-show-sgc").checked && state.sgc) {
      const stSel = $("ch7-sgc-station").value;
      const codes = stSel === "ALL" ? Object.keys(state.sgc) : [stSel];
      codes.forEach((code) => {
        const sp = state.sgc[code];
        if (!sp) return;
        const comps = [
          ["EW", sp.Sa_EW_g, COLORS.EW],
          ["NS", sp.Sa_NS_g, COLORS.NS],
          ["V", sp.Sa_VER_g, COLORS.VER],
        ];
        comps.forEach(([lab, arr, col]) => {
          datasetsSa.push({
            label: `${code} SGC ${lab}`,
            data: sp.T_s.map((t, i) => ({ x: t, y: arr[i] })),
            borderColor: col,
            borderWidth: 1.2,
            pointRadius: 0,
            tension: 0,
            borderDash: [6, 3],
          });
          const sd = saToSd(sp.T_s, arr);
          datasetsSd.push({
            label: `${code} Sd SGC ${lab}`,
            data: sp.T_s.map((t, i) => ({ x: t, y: sd[i] })),
            borderColor: col,
            borderWidth: 1.2,
            pointRadius: 0,
            tension: 0,
            borderDash: [6, 3],
          });
          if (stSel !== "ALL" && exportCols.T_s.length) {
            exportCols[`Sa_SGC_${code}_${lab}_g`] = alignTo(exportCols.T_s, sp.T_s, arr);
            exportCols[`Sd_SGC_${code}_${lab}_m`] = alignTo(exportCols.T_s, sp.T_s, sd);
          }
        });
      });
    }

    if (!exportCols.T_s.length && datasetsSa[0]) {
      exportCols.T_s = datasetsSa[0].data.map((p) => p.x);
    }

    return { datasetsSa, datasetsSd, exportCols };
  }

  function alignTo(Tref, Tsrc, Ysrc) {
    // nearest-neighbor sample onto Tref
    return Tref.map((t) => {
      let best = 0;
      let bd = Infinity;
      for (let i = 0; i < Tsrc.length; i++) {
        const d = Math.abs(Tsrc[i] - t);
        if (d < bd) {
          bd = d;
          best = i;
        }
      }
      return Ysrc[best];
    });
  }

  function renderCharts() {
    const { datasetsSa, datasetsSd, exportCols } = buildDatasets();
    state.lastExport = exportCols;
    const common = {
      type: "line",
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 12, font: { size: 10 } } },
          title: { display: false },
        },
        scales: {
          x: {
            type: "linear",
            title: { display: true, text: "Periodo T (s)" },
            min: 0,
            max: 4,
          },
          y: { title: { display: true, text: "" }, beginAtZero: true },
        },
      },
    };

    if (state.chartSa) state.chartSa.destroy();
    if (state.chartSd) state.chartSd.destroy();

    const optSa = JSON.parse(JSON.stringify(common));
    optSa.data = { datasets: datasetsSa };
    optSa.options.scales.y.title.text = "Sa (g)";
    optSa.options.plugins.title = {
      display: true,
      text: "Espectro elástico de aceleraciones de diseño",
      color: "#063c5b",
    };
    state.chartSa = new Chart($("ch7-chart-sa"), optSa);

    const optSd = JSON.parse(JSON.stringify(common));
    optSd.data = { datasets: datasetsSd };
    optSd.options.scales.y.title.text = "Sd (m)";
    optSd.options.plugins.title = {
      display: true,
      text: "Espectro elástico de desplazamientos de diseño",
      color: "#063c5b",
    };
    state.chartSd = new Chart($("ch7-chart-sd"), optSd);
  }

  function downloadCSV() {
    const cols = state.lastExport;
    if (!cols || !cols.T_s || !cols.T_s.length) {
      alert("Genere primero los espectros (seleccione municipio y pulse Actualizar).");
      return;
    }
    const keys = Object.keys(cols);
    const lines = [keys.join(",")];
    const n = cols.T_s.length;
    for (let i = 0; i < n; i++) {
      lines.push(keys.map((k) => (cols[k][i] != null ? Number(cols[k][i]).toExponential(6) : "")).join(","));
    }
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "espectros_diseno_NSR10_SGC2026pqqmro.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  async function loadJSON(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error("No se pudo cargar " + path);
    return res.json();
  }

  async function init() {
    try {
      const [mun, micro, sgc, proc] = await Promise.all([
        loadJSON("output/data/municipios_nsr10.json"),
        loadJSON("output/data/microzonificacion.json"),
        loadJSON("output/data/sgc_psa_2026.json"),
        loadJSON("output/data/espectros_procesados_2026.json"),
      ]);
      state.munData = mun;
      state.micro = micro;
      state.sgc = sgc;
      state.proc = proc;

      fillSelect(
        $("ch7-dept"),
        mun.departamentos,
        (d) => d,
        (d) => d,
        "— Departamento —"
      );
      fillSelect(
        $("ch7-uso"),
        USAGE,
        (u) => u.id,
        (u) => u.label
      );
      fillSelect(
        $("ch7-perfil"),
        ["A", "B", "C", "D", "E", "F"],
        (p) => p,
        (p) => `Perfil ${p}` + (p === "F" ? " (estudio de sitio)" : "")
      );
      $("ch7-perfil").value = "D";
      $("ch7-uso").value = "I";

      const procStations = Object.keys(proc).sort();
      fillSelect(
        $("ch7-proc-station"),
        ["ALL"].concat(procStations),
        (s) => s,
        (s) => (s === "ALL" ? "Todas las estaciones (excepto CBOCA atípica)" : s + (proc[s].quality_flag === "ATYPICAL_DO_NOT_USE" ? " — ATÍPICA" : ""))
      );
      const sgcStations = Object.keys(sgc).sort();
      fillSelect(
        $("ch7-sgc-station"),
        ["ALL"].concat(sgcStations),
        (s) => s,
        (s) => (s === "ALL" ? "Todas (SGC automático)" : s)
      );

      // Prefer Quindío / Armenia if available
      const prefDept = mun.departamentos.find((d) => /quind/i.test(d));
      if (prefDept) {
        $("ch7-dept").value = prefDept;
        updateMunList();
        const arm = [...$("ch7-mun").options].find((o) => /armenia/i.test(o.value));
        if (arm) $("ch7-mun").value = arm.value;
      }

      $("ch7-dept").addEventListener("change", updateMunList);
      $("ch7-mun").addEventListener("change", () => {
        updateMicroUI();
        updateParams();
      });
      ["ch7-uso", "ch7-perfil", "ch7-R", "ch7-apply-R", "ch7-use-micro", "ch7-micro-zona", "ch7-show-proc", "ch7-proc-station", "ch7-show-sgc", "ch7-sgc-station"].forEach((id) => {
        const el = $(id);
        if (el) el.addEventListener("change", () => {
          updateParams();
          renderCharts();
        });
      });
      $("ch7-update").addEventListener("click", () => {
        updateParams();
        renderCharts();
      });
      $("ch7-download").addEventListener("click", downloadCSV);

      updateParams();
      renderCharts();
      $("ch7-status").textContent = "Listo — datos NSR-10 y espectros 2026 cargados.";
    } catch (err) {
      console.error(err);
      $("ch7-status").textContent =
        "Error cargando datos. Abra el informe vía servidor local (fetch no funciona en file://). Detalle: " +
        err.message;
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

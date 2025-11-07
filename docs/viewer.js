(() => {
  const $ = (id) => document.getElementById(id);
  const statusEl = $("status");
  const listEl = $("dashList");
  const chartTitleEl = $("chartTitle");
  const chartMetaEl = $("chartMeta");
  const chartCanvas = $("chart");
  const embedContainer = $("embedContainer");
  const loadBtn = $("loadBtn");
  const manifestInput = $("manifestUrl");

  let manifest = null;
  let chart = null;

  function setStatus(text, isError = false) {
    statusEl.textContent = text;
    statusEl.className = isError ? "status error" : "status";
  }

  async function fetchJson(url) {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`Napaka pri prenosu: ${res.status} ${res.statusText}`);
    return res.json();
  }

  function renderList(items) {
    listEl.innerHTML = "";
    items.forEach((d, idx) => {
      const el = document.createElement("div");
      el.className = "item";
      el.innerHTML = `<strong>${d.title || `Dashboard ${idx+1}`}</strong>` +
        `<small>${d.description || ""}</small>` +
        (d.source_url ? `<small>Vir: ${d.source_url}</small>` : "");
      el.addEventListener("click", () => drawDashboard(d));
      listEl.appendChild(el);
    });
  }

  async function drawDashboard(d) {
    try {
      chartTitleEl.textContent = d.title || "Nadzorna plošča";
      chartMetaEl.innerHTML = "";

      // Če je viz tip iframe, vgradi zunanji dashboard
      if (d.viz_type === "iframe" && (d.embed_url || d.external_url)) {
        // Posodobi meta
        const meta = [
          { k: "Vizualizacija", v: "iframe" },
          { k: "Vir", v: (d.embed_url || d.external_url) },
        ];
        meta.forEach(m => {
          const md = document.createElement("div");
          md.innerHTML = `<div style="color:#9fb0c1;font-size:12px">${m.k}</div><div style="font-weight:600">${m.v || "-"}</div>`;
          chartMetaEl.appendChild(md);
        });

        // Skrij canvas, pokaži embed container
        if (chart) { chart.destroy(); chart = null; }
        chartCanvas.style.display = "none";
        embedContainer.style.display = "block";
        embedContainer.innerHTML = "";
        const frame = document.createElement("iframe");
        frame.src = d.embed_url || d.external_url;
        frame.setAttribute("title", d.title || "Vgrajeni dashboard");
        frame.style.width = "100%";
        frame.style.height = "100%";
        frame.style.border = "0";
        embedContainer.appendChild(frame);
        setStatus("Vgrajeno (iframe).");
        return;
      }

      // Sicer nariši Chart.js iz podatkovnega vira
      const meta = [
        { k: "Vizualizacija", v: d.viz_type },
        { k: "X os", v: d.x_field },
        { k: "Y os", v: d.y_field },
      ];
      meta.forEach(m => {
        const md = document.createElement("div");
        md.innerHTML = `<div style="color:#9fb0c1;font-size:12px">${m.k}</div><div style="font-weight:600">${m.v || "-"}</div>`;
        chartMetaEl.appendChild(md);
      });

      const data = await fetchJson(d.source_url);

      const labels = data.map(r => r[d.x_field]);
      const values = data.map(r => Number(r[d.y_field] ?? 0));

      const dsColor = "#4fb3ff";
      const config = {
        type: d.viz_type || "bar",
        data: {
          labels,
          datasets: [{
            label: d.title || "Podatki",
            data: values,
            backgroundColor: d.viz_type === "pie" ? labels.map(() => dsColor) : dsColor,
            borderColor: dsColor,
          }],
        },
        options: {
          plugins: {
            legend: { display: d.viz_type === "pie" },
            title: { display: false },
          },
          scales: {
            x: { ticks: { color: "#9fb0c1" }, grid: { color: "#1f2633" } },
            y: { ticks: { color: "#9fb0c1" }, grid: { color: "#1f2633" } },
          },
        },
      };

      // Pokaži canvas, skrij embed
      embedContainer.style.display = "none";
      chartCanvas.style.display = "block";
      if (chart) chart.destroy();
      chart = new Chart(chartCanvas, config);
      setStatus("Narisano.");
    } catch (err) {
      console.error(err);
      setStatus(`Napaka: ${err.message}`, true);
    }
  }

  async function loadManifest(url) {
    try {
      setStatus("Nalagam manifest...");
      manifest = await fetchJson(url);
      if (!manifest || !Array.isArray(manifest.dashboards)) throw new Error("Neveljaven manifest format.");
      renderList(manifest.dashboards);
      setStatus(`Naloženih ${manifest.dashboards.length} plošč.`);
    } catch (err) {
      console.error("Primarni manifest ni uspel:", err);
      // Fallback: poskusi 'main' vejo, če je prvotni URL iz funkcionalne veje
      try {
        const fallback = "https://raw.githubusercontent.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/main/dashboards/manifest.json";
        setStatus("Primarni URL ni uspel, poskušam fallback na main...");
        manifest = await fetchJson(fallback);
        if (!manifest || !Array.isArray(manifest.dashboards)) throw new Error("Neveljaven manifest format (fallback).");
        manifestInput.value = fallback;
        renderList(manifest.dashboards);
        setStatus(`Naloženih ${manifest.dashboards.length} plošč (fallback).`);
      } catch (err2) {
        console.error("Fallback manifest ni uspel:", err2);
        setStatus(`Napaka pri manifestu: ${err.message} | Fallback: ${err2.message}`, true);
      }
    }
  }

  loadBtn.addEventListener("click", () => {
    const url = manifestInput.value.trim();
    if (!url) {
      setStatus("Prosimo, prilepite Raw URL do manifest.json.", true);
      return;
    }
    loadManifest(url);
  });

  // Privzeti manifest URL (GitHub Raw) in samodejno nalaganje
  try {
    const primary = "https://raw.githubusercontent.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/feat/20-dashboards/dashboards/manifest.json";
    manifestInput.value = primary;
    if (manifestInput.value) {
      loadManifest(manifestInput.value);
    }
  } catch (e) {
    // tiho nadaljuj
  }
})();
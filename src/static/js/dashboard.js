(function () {
  const { esc, apiJson, setFeedback, formatNumber } = window.NagasakiApp;
  const catalog = window.__CATALOG__ || [];
  const initial = window.__INITIAL__ || {};

  const msg = document.getElementById("msg");
  const selType = document.getElementById("sel-type");
  const selEntity = document.getElementById("sel-entity");
  const selAttr = document.getElementById("sel-attr");
  const selMetric = document.getElementById("sel-metric");
  const kpiGrid = document.getElementById("kpi-grid");
  const insightBanner = document.getElementById("insight-banner");
  const insightText = document.getElementById("insight-text");
  const chartTitle = document.getElementById("chart-title");
  const chartSubtitle = document.getElementById("chart-subtitle");
  const rankingList = document.getElementById("ranking-list");
  const linkCompare = document.getElementById("link-compare");
  const explorer = document.getElementById("explorer");

  let seriesChart = null;
  let debounceTimer = null;

  const chartStatsBar = document.getElementById("chart-stats-bar");

  function chartVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function buildChartOptions(attr) {
    const tick = chartVar("--chart-tick") || "#a89cc8";
    const grid = chartVar("--chart-grid") || "rgba(168,85,247,0.1)";
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: chartVar("--chart-legend") || "#c4b5fd",
            font: { family: "DM Sans", size: 11 },
            boxWidth: 14,
          },
        },
        tooltip: {
          backgroundColor: chartVar("--chart-tooltip-bg") || "#1a0f2e",
          titleColor: chartVar("--chart-tooltip-title") || "#f5f0ff",
          bodyColor: chartVar("--chart-tooltip-body") || "#e9d5ff",
          callbacks: {
            label(ctx) {
              const v = ctx.parsed.y;
              if (v == null) return ctx.dataset.label;
              return `${ctx.dataset.label}: ${formatNumber(v)}`;
            },
          },
        },
      },
      scales: {
        x: {
          ticks: { color: tick, maxTicksLimit: 12, maxRotation: 0 },
          grid: { color: grid },
          title: { display: true, text: "Tiempo (UTC)", color: tick, font: { size: 11 } },
        },
        y: {
          beginAtZero: attr === "powerKw" || attr === "flowVehH" || attr === "irradianceWm2",
          ticks: {
            color: tick,
            callback: (v) => formatNumber(v),
          },
          grid: { color: grid },
          title: { display: true, text: attrLabel(attr), color: tick, font: { size: 11 } },
        },
      },
    };
  }

  function chartDatasetColors() {
    return {
      band: chartVar("--chart-band") || "rgba(167, 139, 250, 0.18)",
      series: chartVar("--chart-series") || "#c4b5fd",
      rolling: chartVar("--chart-rolling") || "#f472b6",
      mean: chartVar("--chart-mean") || "#34d399",
      median: chartVar("--chart-median") || "#fbbf24",
    };
  }

  function renderChartSummary(summary) {
    if (!summary || !chartStatsBar) return;
    chartStatsBar.innerHTML = [
      ["Mín", summary.min],
      ["Máx", summary.max],
      ["Media", summary.mean],
      ["Mediana", summary.median],
      ["Puntos", summary.count],
    ]
      .map(([label, val]) => `<span class="chart-stat-pill">${label}: <strong>${formatNumber(val)}</strong></span>`)
      .join("");
  }

  function entityById(id) {
    return catalog.find((e) => e.entityId === id);
  }

  function catalogTypes() {
    const seen = new Map();
    catalog.forEach((e) => {
      if (!seen.has(e.type)) seen.set(e.type, e.typeLabel || e.type);
    });
    return [...seen.entries()].map(([type, label]) => ({ type, label }));
  }

  function entitiesOfType(type) {
    return catalog.filter((e) => e.type === type);
  }

  function syncSelectTitle(sel) {
    if (!sel || sel.selectedIndex < 0) return;
    const opt = sel.options[sel.selectedIndex];
    sel.title = opt ? opt.textContent.trim() : "";
  }

  function syncFilterSelectTitles() {
    [selType, selEntity, selAttr, selMetric].forEach(syncSelectTitle);
  }

  function fillEntitySelect() {
    const list = entitiesOfType(selType.value);
    const prev = selEntity.value;
    selEntity.innerHTML = list
      .map(
        (e) =>
          `<option value="${esc(e.entityId)}">${esc(e.displayName)}</option>`
      )
      .join("");
    if (list.some((e) => e.entityId === prev)) selEntity.value = prev;
    else if (list.length) selEntity.value = list[0].entityId;
    syncSelectTitle(selEntity);
    fillAttributes();
  }

  function initTypeAndEntity() {
    const types = catalogTypes();
    if (types.length && selType.options.length === 0) {
      selType.innerHTML = types
        .map((t) => `<option value="${esc(t.type)}">${esc(t.label)}</option>`)
        .join("");
    }
    const startId = initial.entityId || selEntity.value;
    const startEnt = entityById(startId);
    if (startEnt && [...selType.options].some((o) => o.value === startEnt.type)) {
      selType.value = startEnt.type;
    }
    fillEntitySelect();
    if (startId && [...selEntity.options].some((o) => o.value === startId)) {
      selEntity.value = startId;
      fillAttributes();
    }
  }

  function selectEntityById(id) {
    const ent = entityById(id);
    if (!ent) return;
    if (selType.value !== ent.type) {
      selType.value = ent.type;
      fillEntitySelect();
    }
    selEntity.value = id;
    fillAttributes();
  }

  function displayName(id) {
    const e = entityById(id);
    return e ? e.displayName : id;
  }

  function attrLabel(attr) {
    const e = entityById(selEntity.value);
    if (e && e.attributeLabels && e.attributeLabels[attr]) return e.attributeLabels[attr];
    return initial.attributeLabels?.[attr] || attr;
  }

  function currentQuery() {
    return {
      entityId: selEntity.value,
      attribute: selAttr.value,
      metric: selMetric.value,
    };
  }

  function fillAttributes() {
    const ent = entityById(selEntity.value);
    const attrs = ent ? ent.attributes : [];
    const prev = selAttr.value;
    selAttr.innerHTML = attrs
      .map((a) => {
        const label = ent.attributeLabels?.[a] || a;
        return `<option value="${esc(a)}">${esc(label)}</option>`;
      })
      .join("");
    if (attrs.includes(prev)) selAttr.value = prev;
    else if (attrs.length) selAttr.value = attrs[0];
    syncSelectTitle(selAttr);
  }

  function updateCompareLink() {
    const q = currentQuery();
    const p = new URLSearchParams({
      attribute: q.attribute,
      metric: q.metric,
      entityIds: `${q.entityId},urn:nagasaki:solar:plant-2`,
    });
    linkCompare.href = `/compare?${p}`;
  }

  function renderKpis(labeled) {
    if (!labeled?.length) {
      kpiGrid.innerHTML = "";
      return;
    }
    kpiGrid.innerHTML = labeled
      .map(
        (row) =>
          `<div class="kpi-card"><span class="kpi-label">${esc(row.label)}</span>` +
          `<span class="kpi-value">${esc(row.value)}</span></div>`
      )
      .join("");
  }

  function renderRanking(rankingPayload, selectedId) {
    if (rankingPayload.error) {
      rankingList.innerHTML = `<li class="empty-hint">${esc(rankingPayload.error)}</li>`;
      return;
    }
    const label = rankingPayload.metricLabel || rankingPayload.metric;
    rankingList.innerHTML = (rankingPayload.ranking || [])
      .map((row, idx) => {
        const name = displayName(row.entityId);
        const sel = row.entityId === selectedId ? " is-selected" : "";
        return (
          `<li class="ranking-item${sel}" data-entity-id="${esc(row.entityId)}" tabindex="0">` +
          `<span class="ranking-rank">${idx + 1}</span>` +
          `<span class="ranking-name">${esc(name)}</span>` +
          `<span class="ranking-value">${esc(formatNumber(row.metric))}</span></li>`
        );
      })
      .join("");
    bindRanking();
  }

  function bindRanking() {
    rankingList.querySelectorAll(".ranking-item").forEach((li) => {
      const go = () => {
        const id = li.getAttribute("data-entity-id");
        if (!id) return;
        selectEntityById(id);
        scheduleRefresh();
      };
      li.addEventListener("click", go);
      li.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          go();
        }
      });
    });
  }

  async function refreshChart() {
    const q = currentQuery();
    const wrap = document.getElementById("series-chart-wrap");
    wrap.setAttribute("aria-busy", "true");
    const { data } = await apiJson(`/api/series?${new URLSearchParams(q)}`);
    wrap.setAttribute("aria-busy", "false");
    if (data.error) return;

    renderChartSummary(data.summary);

    const labels = (data.timestamps || []).map((t) => {
      const d = new Date(t);
      return d.toLocaleString("es-ES", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
    });
    const ctx = document.getElementById("series-chart");
    const c = chartDatasetColors();
    if (seriesChart) seriesChart.destroy();
    seriesChart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Máximo",
            data: data.maxLine,
            borderColor: "transparent",
            backgroundColor: c.band,
            pointRadius: 0,
            borderWidth: 0,
            fill: false,
            order: 4,
          },
          {
            label: "Rango mín–máx",
            data: data.minLine,
            borderColor: "transparent",
            backgroundColor: c.band,
            pointRadius: 0,
            borderWidth: 0,
            fill: "-1",
            order: 3,
          },
          {
            label: attrLabel(q.attribute),
            data: data.values,
            borderColor: c.series,
            backgroundColor: "transparent",
            fill: false,
            tension: 0.2,
            pointRadius: 3,
            pointHoverRadius: 5,
            borderWidth: 2.5,
            order: 1,
          },
          {
            label: `Media móvil (${data.rollingWindow || 3})`,
            data: data.rollingMean,
            borderColor: c.rolling,
            borderDash: [5, 4],
            pointRadius: 0,
            tension: 0.3,
            borderWidth: 1.5,
            order: 0,
          },
          {
            label: "Media global",
            data: data.meanLine,
            borderColor: c.mean,
            borderDash: [2, 3],
            pointRadius: 0,
            borderWidth: 1.5,
            order: 2,
          },
          {
            label: "Mediana",
            data: data.medianLine,
            borderColor: c.median,
            borderDash: [8, 4],
            pointRadius: 0,
            borderWidth: 1,
            order: 2,
          },
        ],
      },
      options: buildChartOptions(q.attribute),
    });
  }

  async function refreshAll() {
    const q = currentQuery();
    explorer?.classList.add("loading-overlay");
    chartTitle.textContent = attrLabel(q.attribute);
    chartSubtitle.textContent = `${displayName(q.entityId)} · ${q.metric ? "" : ""}${selMetric.selectedOptions[0]?.text || q.metric}`;

    try {
      const { data } = await apiJson(`/api/stats?${new URLSearchParams(q)}`);
      const stats = data.stats || {};
      if (stats.error) {
        setFeedback(msg, stats.error, true);
        insightBanner.hidden = true;
        renderKpis([]);
      } else {
        setFeedback(msg, "");
        insightText.textContent = stats.insight || "";
        insightBanner.hidden = !stats.insight;
        renderKpis(stats.labeledStats || []);
      }
      renderRanking(data.ranking || {}, q.entityId);
      await refreshChart();
      updateCompareLink();
      await refreshAlerts(q);

      const url = new URL(window.location.href);
      Object.entries(q).forEach(([k, v]) => url.searchParams.set(k, v));
      history.replaceState(null, "", url);
    } catch {
      setFeedback(msg, "No se pudieron cargar los datos. Prueba otra magnitud.", true);
    } finally {
      explorer?.classList.remove("loading-overlay");
    }
  }

  async function refreshAlerts(q) {
    if (!insightText || !insightBanner) return;
    try {
      const { data } = await apiJson(
        `/api/alerts/check?${new URLSearchParams({ entityId: q.entityId, attribute: q.attribute })}`
      );
      const extra = (data.messages || []).join(" ");
      if (!extra) return;
      const prev = insightText.textContent.trim();
      insightText.textContent = prev ? `${prev} — ${extra}` : extra;
      insightBanner.hidden = false;
    } catch {
      /* sin alertas o error de red: no bloquea el panel */
    }
  }

  function scheduleRefresh() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => refreshAll(), 280);
  }

  selType?.addEventListener("change", () => {
    fillEntitySelect();
    syncSelectTitle(selType);
    scheduleRefresh();
  });

  [selEntity, selAttr, selMetric].forEach((el) =>
    el?.addEventListener("change", () => {
      syncSelectTitle(el);
      scheduleRefresh();
    })
  );

  document.getElementById("btn-save-view")?.addEventListener("click", async () => {
    const name = document.getElementById("view-name").value.trim();
    if (!name) {
      setFeedback(msg, "Escribe un nombre para la vista.", true);
      return;
    }
    const { data } = await apiJson("/api/views", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, ...currentQuery() }),
    });
    setFeedback(msg, data.error || "Vista guardada. La verás en «Vistas».", Boolean(data.error));
  });

  document.getElementById("btn-save-bookmark")?.addEventListener("click", async () => {
    const label = document.getElementById("bm-label").value.trim();
    const q = currentQuery();
    const { data } = await apiJson("/api/bookmarks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        label: label || displayName(q.entityId),
        entityId: q.entityId,
        attribute: q.attribute,
        defaultMetric: q.metric,
      }),
    });
    setFeedback(msg, data.error || "Marcador guardado. Las notas pueden referenciarlo.", Boolean(data.error));
  });

  document.getElementById("btn-save-note")?.addEventListener("click", async () => {
    const text = document.getElementById("note-text").value.trim();
    if (!text) {
      setFeedback(msg, "Escribe el texto de la nota.", true);
      return;
    }
    const { data } = await apiJson("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, ...currentQuery() }),
    });
    const okMsg = data.item?.bookmark_id
      ? "Nota guardada y enlazada al marcador de esta fuente."
      : "Nota guardada con el contexto actual.";
    setFeedback(msg, data.error || okMsg, Boolean(data.error));
  });

  initTypeAndEntity();
  if (initial.attribute && [...selAttr.options].some((o) => o.value === initial.attribute)) {
    selAttr.value = initial.attribute;
  }
  syncFilterSelectTitles();
  updateCompareLink();
  bindRanking();
  refreshChart().catch(() => {});

  window.addEventListener("nagasaki-theme", () => {
    if (seriesChart) refreshChart().catch(() => {});
  });
})();

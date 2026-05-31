(function (global) {
  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  async function apiJson(url, opts = {}) {
    const res = await fetch(url, opts);
    const data = await res.json();
    return { res, data };
  }

  function setFeedback(el, text, isError = false) {
    if (!el) return;
    el.textContent = text;
    el.dataset.variant = isError ? "error" : "ok";
  }

  /** Formato legible para números en tablas y gráficos. */
  function formatNumber(value, decimals) {
    if (value == null || value === "") return "—";
    const n = Number(value);
    if (Number.isNaN(n)) return String(value);
    if (decimals != null) return n.toLocaleString("es-ES", { maximumFractionDigits: decimals });
    if (Math.abs(n) >= 100) return n.toLocaleString("es-ES", { maximumFractionDigits: 0 });
    if (Math.abs(n) >= 10) return n.toLocaleString("es-ES", { maximumFractionDigits: 1 });
    return n.toLocaleString("es-ES", { maximumFractionDigits: 2 });
  }

  global.NagasakiApp = { esc, apiJson, setFeedback, formatNumber };
})(window);

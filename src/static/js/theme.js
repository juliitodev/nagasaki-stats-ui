/**
 * Tema de interfaz (localStorage + select en barra superior).
 */
(function () {
  const KEY = "nagasaki-theme";
  const DEFAULT = "dark";

  const VALID = new Set(["dark", "light", "slate"]);

  function apply(theme) {
    let t = theme || DEFAULT;
    if (!VALID.has(t)) t = DEFAULT;
    /* Pico solo entiende dark|light; slate usa paleta oscura de Pico + variables propias */
    document.documentElement.setAttribute("data-theme", t === "light" ? "light" : "dark");
    if (t === "slate") {
      document.documentElement.setAttribute("data-app-theme", "slate");
    } else {
      document.documentElement.removeAttribute("data-app-theme");
    }
    const meta = document.querySelector('meta[name="color-scheme"]');
    if (meta) meta.setAttribute("content", t === "light" ? "light" : "dark");
    localStorage.setItem(KEY, t);
    const sel = document.getElementById("theme-select");
    if (sel && sel.value !== t) sel.value = t;
    window.dispatchEvent(new CustomEvent("nagasaki-theme", { detail: t }));
  }

  apply(localStorage.getItem(KEY) || DEFAULT);

  document.getElementById("theme-select")?.addEventListener("change", (e) => {
    apply(e.target.value);
  });

  window.NagasakiTheme = { apply };
})();

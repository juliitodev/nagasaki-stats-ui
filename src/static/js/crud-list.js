/**
 * Borrado en listados (vistas, marcadores, notas) sin recargar la página.
 */
(function () {
  const root = document.querySelector("[data-crud-list]");
  if (!root) return;

  const msg = document.getElementById("msg");
  const { apiJson, setFeedback } = window.NagasakiApp;

  root.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-delete-url]");
    if (!btn) return;
    const card = btn.closest("[data-card]");
    const url = btn.getAttribute("data-delete-url");
    btn.disabled = true;
    try {
      const { res, data } = await apiJson(url, { method: "DELETE" });
      if (!res.ok) {
        setFeedback(msg, data.error || "No se pudo eliminar.", true);
        btn.disabled = false;
        return;
      }
      card?.remove();
      if (!root.querySelector("[data-card]")) {
        const empty = document.getElementById("crud-empty");
        if (empty) empty.style.display = "";
      }
      setFeedback(msg, "Eliminado.", false);
    } catch {
      setFeedback(msg, "Error de red. Inténtalo otra vez.", true);
      btn.disabled = false;
    }
  });
})();

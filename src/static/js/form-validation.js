(function () {
  function showError(msg) {
    var dv = document.getElementById("dvError");
    if (!dv) return;
    dv.textContent = msg;
    dv.hidden = false;
  }

  function hideError() {
    var dv = document.getElementById("dvError");
    if (!dv) return;
    dv.textContent = "";
    dv.hidden = true;
  }

  function validateLogin() {
    hideError();
    var user = document.getElementById("edUsername");
    var pass = document.getElementById("edPassword");
    if (!user || !pass) return true;
    if (!user.value.trim()) {
      showError("Introduce el usuario.");
      user.focus();
      return false;
    }
    if (!pass.value.trim()) {
      showError("Introduce la contraseña.");
      pass.focus();
      return false;
    }
    return true;
  }

  function validateAlert() {
    var dv = document.getElementById("dvError");
    if (!dv) return true;
    hideError();
    var minEl = document.getElementById("alert-min");
    var maxEl = document.getElementById("alert-max");
    if (!minEl || !maxEl) return true;
    var minRaw = minEl.value.trim();
    var maxRaw = maxEl.value.trim();
    if (!minRaw && !maxRaw) {
      dv.hidden = false;
      dv.textContent = "Indica al menos un mínimo o un máximo.";
      minEl.focus();
      return false;
    }
    if (minRaw && maxRaw && Number(minRaw) > Number(maxRaw)) {
      dv.hidden = false;
      dv.textContent = "El mínimo no puede ser mayor que el máximo.";
      maxEl.focus();
      return false;
    }
    return true;
  }

  window.showError = showError;
  window.hideError = hideError;
  window.validateLogin = validateLogin;
  window.validateAlert = validateAlert;
})();

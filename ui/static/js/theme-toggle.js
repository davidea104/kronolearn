(function () {
  var STORAGE_KEY = "kronolearn:theme";
  var root = document.documentElement;

  function currentTheme() {
    return root.dataset.theme === "dark" ? "dark" : "light";
  }

  function applyTheme(theme) {
    var isDark = theme === "dark";
    if (isDark) {
      root.dataset.theme = "dark";
    } else {
      delete root.dataset.theme;
    }
    var actionLabel = isDark ? "Cambiar a modo claro" : "Cambiar a modo oscuro";
    document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
      button.setAttribute("aria-pressed", isDark ? "true" : "false");
      button.setAttribute("aria-label", actionLabel);
      var icon = button.querySelector("[data-theme-toggle-icon]");
      if (icon) {
        icon.textContent = isDark ? "☀️" : "🌙";
      }
      var label = button.querySelector("[data-theme-toggle-label]");
      if (label) {
        label.textContent = isDark ? "Modo claro" : "Modo oscuro";
      }
    });
  }

  function persistTheme(theme) {
    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch (error) {
      /* localStorage no disponible: el tema sigue aplicado en esta vista */
    }
  }

  function handleToggleClick() {
    var next = currentTheme() === "dark" ? "light" : "dark";
    applyTheme(next);
    persistTheme(next);
  }

  function handleStorageEvent(event) {
    if (event.key !== STORAGE_KEY) {
      return;
    }
    applyTheme(event.newValue === "dark" ? "dark" : "light");
  }

  document.addEventListener("DOMContentLoaded", function () {
    applyTheme(currentTheme());
    document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
      button.addEventListener("click", handleToggleClick);
    });
  });

  window.addEventListener("storage", handleStorageEvent);
})();

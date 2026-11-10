/* Small progressive enhancements. Every page also works without JavaScript. */
(function () {
  "use strict";
  var root = document.documentElement;
  var body = document.body;

  // Theme toggle (the initial theme is applied by the inline script in <head>).
  document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
    button.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) {}
    });
  });

  // Mobile sidebar drawer.
  document.querySelectorAll("[data-sidebar-open]").forEach(function (el) {
    el.addEventListener("click", function () { body.classList.add("sidebar-open"); });
  });
  document.querySelectorAll("[data-sidebar-close]").forEach(function (el) {
    el.addEventListener("click", function () { body.classList.remove("sidebar-open"); });
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") body.classList.remove("sidebar-open");
  });

  // Ask before submitting destructive forms.
  document.addEventListener("submit", function (event) {
    var message = event.target.getAttribute("data-confirm");
    if (message && !window.confirm(message)) event.preventDefault();
  });

  // Filter dropdowns apply immediately.
  document.querySelectorAll("form[data-autosubmit] select").forEach(function (select) {
    select.addEventListener("change", function () { select.form.submit(); });
  });

  // Flash message: auto-hide, and drop ?msg= from the address bar so a refresh doesn't repeat it.
  var flash = document.querySelector("[data-flash]");
  if (flash) {
    var hide = function () {
      flash.classList.add("is-hiding");
      setTimeout(function () { flash.remove(); }, 300);
    };
    var close = flash.querySelector("[data-flash-close]");
    if (close) close.addEventListener("click", hide);
    setTimeout(hide, 3500);
  }
  var url = new URL(window.location.href);
  if (url.searchParams.has("msg")) {
    url.searchParams.delete("msg");
    window.history.replaceState(null, "", url.pathname + url.search + url.hash);
  }
})();

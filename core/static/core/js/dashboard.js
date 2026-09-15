/*
 * GELETRIC — interacciones del dashboard.
 * Sin dependencias externas. Los datos llegan desde el template vía
 * {{ ...|json_script:"id" }}; este archivo solo sabe dibujar y reaccionar.
 */
(function (window) {
  "use strict";

  // ---------- menú lateral: drawer en mobile, "pineado" en desktop ----------
  function initSidebarToggle() {
    var sidebar = document.getElementById("sidebar");
    var scrim = document.getElementById("scrim");
    var menuBtn = document.getElementById("menu-btn");
    if (!sidebar || !scrim || !menuBtn) return;

    var PIN_KEY = "geletric-sidebar-pinned";

    function close() {
      sidebar.classList.remove("open");
      scrim.classList.remove("open");
    }

    // En desktop, el sidebar ya se expande solo con :hover/:focus-within
    // (ver dashboard.css); "pinear" lo deja expandido aunque el mouse no
    // esté encima, y se guarda para que se mantenga al navegar entre
    // páginas (base.html restaura la clase antes del primer render, igual
    // que initBrandPicker con el color del sistema).
    function setPinned(pinned) {
      sidebar.classList.toggle("pinned", pinned);
      menuBtn.setAttribute("aria-pressed", pinned ? "true" : "false");
      try { localStorage.setItem(PIN_KEY, pinned ? "1" : "0"); } catch (e) {}
    }

    menuBtn.addEventListener("click", function () {
      // En mobile (drawer) esto abre el menú; en desktop, pinea/despinea
      // el sidebar expandido. Ambos operan sobre el mismo elemento sin
      // pisarse: cada comportamiento queda acotado por su media query en
      // dashboard.css, así que no hace falta detectar el viewport acá.
      sidebar.classList.add("open");
      scrim.classList.add("open");
      setPinned(!sidebar.classList.contains("pinned"));
    });
    scrim.addEventListener("click", close);
    sidebar.querySelectorAll(".nav-item").forEach(function (el) {
      el.addEventListener("click", close);
    });

    // sincroniza aria-pressed con la clase que base.html ya aplicó
    // (o no) antes de este script correr.
    menuBtn.setAttribute("aria-pressed", sidebar.classList.contains("pinned") ? "true" : "false");
  }

  function readJSON(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  // ---------- gráfico de línea (consumo) ----------
  function initLineChart(dataElId, mountElId) {
    var series = readJSON(dataElId);
    var wrap = document.getElementById(mountElId);
    if (!series || !series.length || !wrap) return;

    var values = series.map(function (d) { return d.value; });
    var w = 640, h = 220, padL = 34, padR = 12, padT = 16, padB = 26;
    var min = Math.min.apply(null, values) * 0.92;
    var max = Math.max.apply(null, values) * 1.06;
    var n = values.length;
    var x = function (i) { return padL + (w - padL - padR) * (i / (n - 1)); };
    var y = function (v) { return padT + (h - padT - padB) * (1 - (v - min) / (max - min)); };

    var linePts = values.map(function (v, i) { return x(i) + "," + y(v); }).join(" ");
    var areaPts = "M" + x(0) + "," + (h - padB) + " L" +
      values.map(function (v, i) { return x(i) + "," + y(v); }).join(" L") +
      " L" + x(n - 1) + "," + (h - padB) + " Z";

    var gridLines = "";
    for (var g = 0; g <= 3; g++) {
      var gy = padT + (h - padT - padB) * (g / 3);
      gridLines += '<line x1="' + padL + '" y1="' + gy + '" x2="' + (w - padR) + '" y2="' + gy + '" stroke="var(--border)" stroke-width="1"/>';
    }
    var xLabels = series.map(function (d, i) {
      return '<text x="' + x(i) + '" y="' + (h - 6) + '" font-size="11" fill="var(--text-muted)" text-anchor="middle" font-family="var(--font-body)">' + d.label + '</text>';
    }).join("");
    var dots = values.map(function (v, i) {
      return '<circle class="pt" data-i="' + i + '" cx="' + x(i) + '" cy="' + y(v) + '" r="3.2" fill="var(--surface)" stroke="var(--brand-blue)" stroke-width="2"/>';
    }).join("");
    var lastI = n - 1;

    var svg = '<svg viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Evolución del consumo de energía en megavatios hora, últimos seis meses">' +
      gridLines +
      '<defs><linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0%" stop-color="var(--brand-blue)" stop-opacity="0.22"/>' +
      '<stop offset="100%" stop-color="var(--brand-blue)" stop-opacity="0"/>' +
      '</linearGradient></defs>' +
      '<path d="' + areaPts + '" fill="url(#areaGrad)"/>' +
      '<polyline points="' + linePts + '" fill="none" stroke="var(--brand-blue)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>' +
      dots +
      '<circle cx="' + x(lastI) + '" cy="' + y(values[lastI]) + '" r="5.5" fill="var(--brand-blue)" stroke="var(--surface)" stroke-width="2.5"/>' +
      xLabels +
      '<line id="hoverLine" x1="0" y1="' + padT + '" x2="0" y2="' + (h - padB) + '" stroke="var(--border-strong)" stroke-width="1" opacity="0"/>' +
      '</svg>';

    wrap.innerHTML = svg + '<div class="chart-tooltip" id="chart-tooltip"></div>';
    var svgEl = wrap.querySelector("svg");
    var tooltip = document.getElementById("chart-tooltip");
    var hoverLine = document.getElementById("hoverLine");

    function showAt(i) {
      var cx = x(i), cy = y(values[i]);
      hoverLine.setAttribute("x1", cx);
      hoverLine.setAttribute("x2", cx);
      hoverLine.setAttribute("opacity", 1);
      var rect = svgEl.getBoundingClientRect();
      var scale = rect.width / w;
      tooltip.style.left = cx * scale + "px";
      tooltip.style.top = cy * scale + "px";
      tooltip.style.opacity = 1;
      tooltip.innerHTML = series[i].label + " — <b>" + values[i].toLocaleString("es-AR") + " MWh</b>";
    }
    svgEl.addEventListener("mousemove", function (e) {
      var rect = svgEl.getBoundingClientRect();
      var relX = ((e.clientX - rect.left) / rect.width) * w;
      var idx = Math.round((relX - padL) / ((w - padL - padR) / (n - 1)));
      idx = Math.max(0, Math.min(n - 1, idx));
      showAt(idx);
    });
    svgEl.addEventListener("mouseleave", function () {
      tooltip.style.opacity = 0;
      hoverLine.setAttribute("opacity", 0);
    });
  }

  // ---------- donut (estado de la red) ----------
  function initDonutChart(dataElId, mountElId) {
    var segments = readJSON(dataElId);
    var mount = document.getElementById(mountElId);
    if (!segments || !segments.length || !mount) return;

    var total = segments.reduce(function (a, b) { return a + b.value; }, 0);
    var r = 46, cx = 60, cy = 60, sw = 15;
    var circ = 2 * Math.PI * r;
    var offset = 0;

    var segs = segments.map(function (s) {
      var frac = s.value / total;
      var seg = '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="var(' + s.var + ')" stroke-width="' + sw + '" ' +
        'stroke-dasharray="' + (frac * circ - 2) + " " + circ + '" stroke-dashoffset="' + -offset + '" transform="rotate(-90 ' + cx + " " + cy + ')" stroke-linecap="round"/>';
      offset += frac * circ;
      return seg;
    }).join("");

    var pct = Math.round((segments[0].value / total) * 100);
    mount.innerHTML =
      '<svg viewBox="0 0 120 120" width="150" height="150" role="img" aria-label="Estado de la red: ' + pct + '% ' + segments[0].label.toLowerCase() + '">' +
      '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="var(--surface-2)" stroke-width="' + sw + '"/>' +
      segs +
      '<text x="' + cx + '" y="' + (cy - 3) + '" text-anchor="middle" class="donut-center"><tspan class="pct">' + pct + '%</tspan></text>' +
      '<text x="' + cx + '" y="' + (cy + 13) + '" text-anchor="middle" class="donut-center"><tspan class="lbl">' + segments[0].label.toUpperCase() + '</tspan></text>' +
      '</svg>';
  }

  // ---------- solapas (ficha del asociado y similares) ----------
  function initTabs(navSelector, panelsSelector) {
    var nav = document.querySelector(navSelector);
    var panelsWrap = document.querySelector(panelsSelector);
    if (!nav || !panelsWrap) return;
    var buttons = nav.querySelectorAll("[data-tab]");
    var panels = panelsWrap.querySelectorAll("[data-panel]");

    function activate(id) {
      buttons.forEach(function (b) {
        var isActive = b.dataset.tab === id;
        b.classList.toggle("active", isActive);
        b.setAttribute("aria-selected", isActive ? "true" : "false");
      });
      panels.forEach(function (p) {
        p.hidden = p.dataset.panel !== id;
      });
    }
    buttons.forEach(function (b) {
      b.addEventListener("click", function () { activate(b.dataset.tab); });
    });
  }

  // ---------- selector de color del sistema (azul / verde) ----------
  function initBrandPicker() {
    var KEY = "geletric-brand-color";
    var buttons = document.querySelectorAll(".brand-swatch");
    if (!buttons.length) return;

    function apply(color) {
      if (color === "green") {
        document.documentElement.setAttribute("data-brand", "green");
      } else {
        document.documentElement.removeAttribute("data-brand");
        color = "blue";
      }
      buttons.forEach(function (b) {
        b.setAttribute("aria-pressed", b.dataset.brand === color ? "true" : "false");
      });
      try { localStorage.setItem(KEY, color); } catch (e) {}
    }

    buttons.forEach(function (b) {
      b.addEventListener("click", function () { apply(b.dataset.brand); });
    });
    // el <head> ya aplicó la preferencia guardada antes del primer render;
    // acá solo sincronizamos el estado visual (aria-pressed) de los botones.
    apply(document.documentElement.getAttribute("data-brand") === "green" ? "green" : "blue");
  }

  window.Dashboard = {
    initLineChart: initLineChart,
    initDonutChart: initDonutChart,
    initTabs: initTabs,
  };

  document.addEventListener("DOMContentLoaded", function () {
    initSidebarToggle();
    initBrandPicker();
  });
})(window);

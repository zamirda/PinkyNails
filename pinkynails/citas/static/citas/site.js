(function () {
  var $ = function (i) { return document.getElementById(i); };
  var J = function (i) { return JSON.parse($(i).textContent); };
  var S = J("slots-data"), L = J("dias-data"), FX = J("fx-data");
  var dt = null, sel = null;

  function chip(txt, on, fn) {
    var b = document.createElement("button");
    b.type = "button"; b.className = "slot"; b.textContent = txt;
    b.setAttribute("aria-pressed", on); b.onclick = fn;
    return b;
  }
  function days() {
    var box = $("days"); box.innerHTML = "";
    var ks = Object.keys(S).sort();
    if (!ks.length) { box.textContent = "No hay horas libres por ahora."; dt = null; return; }
    if (ks.indexOf(dt) < 0) dt = ks[0];
    ks.forEach(function (k) {
      box.appendChild(chip(L[k], k === dt, function () { dt = k; sel = null; days(); slots(); }));
    });
  }
  function slots() {
    var box = $("slots"); box.innerHTML = "";
    if (!dt) return;
    S[dt].forEach(function (s) {
      box.appendChild(chip(s.t, sel === s.v, function () { sel = s.v; slots(); }));
    });
  }
  function say(t, err, link) {
    var m = $("msg"); m.textContent = t; m.className = "msg show" + (err ? " err" : "");
    if (link) {
      var a = document.createElement("a");
      a.href = link; a.target = "_blank"; a.rel = "noopener"; a.textContent = "Confirmar asistencia por WhatsApp";
      m.appendChild(a);
    }
  }
  $("book").onclick = function () {
    var nm = $("nm").value.trim(), tel = $("tel").value.trim();
    if (!dt || sel === null || !nm || !tel) { say("Escoge un día, una hora y escribe tu nombre y WhatsApp.", true); return; }
    var f = new FormData();
    f.append("servicio", $("svc").value); f.append("fecha", dt); f.append("hora", sel);
    f.append("nombre", nm); f.append("telefono", tel);
    var b = $("book"); b.disabled = true;
    fetch("/agendar/", { method: "POST", body: f, headers: { "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value } })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        b.disabled = false;
        if (!j.ok) {
          say(j.error, true);
          if (S[dt]) { S[dt] = S[dt].filter(function (s) { return s.v !== sel; }); if (!S[dt].length) delete S[dt]; }
          sel = null; days(); slots(); return;
        }
        say(j.mensaje, false, j.wa_url);
        S[dt] = S[dt].filter(function (s) { return s.v !== sel; });
        if (!S[dt].length) delete S[dt];
        sel = null; $("nm").value = ""; $("tel").value = ""; days(); slots();
      })
      .catch(function () { b.disabled = false; say("No se pudo agendar. Revisa tu conexión.", true); });
  };
  days(); slots();

  // Adornos de temporada que caen suavemente
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    FX.forEach(function (em) {
      for (var i = 0; i < 7; i++) {
        var x = document.createElement("span");
        x.className = "fx"; x.textContent = em; x.setAttribute("aria-hidden", "true");
        x.style.cssText = "left:" + (Math.random() * 96) + "vw;font-size:" + (14 + Math.random() * 16) +
          "px;animation-duration:" + (9 + Math.random() * 9) + "s;animation-delay:-" + (Math.random() * 12) + "s";
        document.body.appendChild(x);
      }
    });
  }
})();

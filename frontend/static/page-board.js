/* Board page: metrics, the four send stages, quick grabs, the full board table. */
JH.ready(function (D) {
  "use strict";
  var el = JH.el, clear = JH.clear, $ = JH.$;
  var state = { filter: "all", query: "" };

  /* ---------------- metrics ---------------- */
  (function metrics() {
    var host = $("metrics"), s = D.stats, by = s.by_stage || {};
    clear(host);
    [["On the board", s.total, s.companies + " companies", ""],
     ["CV delivered", by.delivered || 0, by.delivered === 1 ? "one human has it" : "reached a human", "ok"],
     ["In flight", by.inflight || 0, "invite sent, no answer", "warm"],
     ["Packet ready", by.ready || 0, "written, not sent", ""],
     ["No CV out", by.cold || 0, (by.cold || 0) + " of " + s.total + " roles", "hot"],
     ["Warm paths", s.warm, "someone inside", ""]
    ].forEach(function (t) {
      var d = el("div", "metric " + t[3]);
      d.appendChild(el("span", "k", t[0]));
      d.appendChild(el("span", "v", String(t[1])));
      d.appendChild(el("span", "s", t[2]));
      host.appendChild(d);
    });
  })();

  /* ---------------- stages ---------------- */
  function stage(id, title, chipCls, chipText) {
    var root = el("div", "stage");
    var head = el("div", "stage-head");
    head.appendChild(el("span", "stage-id", id));
    head.appendChild(el("h3", null, title));
    var chip = el("span", "chip " + chipCls, chipText);
    head.appendChild(chip);
    var body = el("div", "stage-body");
    root.appendChild(head); root.appendChild(body);
    return { root: root, body: body, chip: chip };
  }
  function task(title, desc, chipText, chipCls) {
    var t = el("div", "tsk"), inner = el("div"), th = el("div", "th");
    th.appendChild(document.createTextNode(title));
    if (chipText) th.appendChild(el("span", "chip " + (chipCls || "c-mute"), chipText));
    inner.appendChild(th);
    inner.appendChild(el("div", "td", desc));
    t.appendChild(inner);
    return t;
  }
  function leg(parent, k, v, cls) {
    var l = el("div", "leg");
    l.appendChild(el("span", "lk", k));
    l.appendChild(el("span", "lv" + (cls ? " " + cls : ""), v));
    parent.appendChild(l);
  }
  function inviteUnit(inv) {
    var unit = el("div", "unit"), top = el("div", "unit-top");
    top.appendChild(el("span", "who", inv.person));
    top.appendChild(el("span", "role", inv.role));
    top.appendChild(el("span", "sp"));
    var done = inv.status === "followed_up";
    top.appendChild(el("span", "chip " + (done ? "c-good" : "c-mute"), done ? "CV delivered" : "waiting"));
    unit.appendChild(top);

    var track = el("div", "track");
    leg(track, "invited", JH.clock(inv.requested_at) + " · " + JH.ago(inv.requested_at));
    if (inv.accepted_at) {
      leg(track, "accepted", JH.clock(inv.accepted_at) + " · " +
        JH.span(new Date(inv.accepted_at) - new Date(inv.requested_at)) + " later", "hit");
    } else { leg(track, "accepted", "not yet", "pend"); }
    if (inv.followed_up_at) {
      leg(track, "CV sent", JH.day(inv.followed_up_at) + " " + JH.clock(inv.followed_up_at), "hit");
    } else { leg(track, "CV sends", "3–20 h after accept", "pend"); }
    unit.appendChild(track);
    return unit;
  }

  (function stages() {
    var host = $("stages");
    clear(host);
    var inv = D.invites || [];
    var pending = inv.filter(function (i) { return i.status === "pending"; });
    var delivered = inv.filter(function (i) { return i.status === "followed_up"; });
    var cold = D.board.filter(function (r) { return r.stage === "cold"; });
    var ready = D.board.filter(function (r) { return r.stage === "ready"; });

    var a = stage("A", "You", "c-warn", (ready.length + 2) + " open");
    var tl = el("div", "tasklist");
    ready.forEach(function (r) {
      var p = JH.packetFor(r.company);
      tl.appendChild(task("Apply to " + r.company + " yourself",
        "Packet built" + (p ? " · ATS " + p.ats : "") + ". LinkedIn Easy Apply, which the robot cannot drive. " +
        "Grab the PDF from Jobs & CV and upload it.", "time-sensitive", "c-warn"));
    });
    tl.appendChild(task("Fix your LinkedIn headline",
      'It still reads "currently persuading my BTECH" — a typo in the field recruiters search on. Replacement text is in the Downloads page.'));
    tl.appendChild(task("Tick or skip the Slack cards",
      "A ✅ releases a send. An untouched card is a stalled application. Then run stage 1 from the Run it page."));
    a.body.appendChild(tl);
    host.appendChild(a.root);

    var b = stage("B", "Invited, no answer yet", "c-warn", pending.length + " pending");
    if (!pending.length) b.body.appendChild(el("p", "lede", "Nothing awaiting an accept."));
    pending.forEach(function (i) { b.body.appendChild(inviteUnit(i)); });
    b.body.appendChild(el("p", "lede",
      "The request carries no note on purpose: a request with a note is capped at three a month, while a message to someone who accepted is uncapped."));
    host.appendChild(b.root);

    var c = stage("C", "Accepted — CV out", "c-good", delivered.length + " delivered");
    if (!delivered.length) c.body.appendChild(el("p", "lede", "Nobody has accepted yet."));
    delivered.forEach(function (i) { c.body.appendChild(inviteUnit(i)); });
    host.appendChild(c.root);

    var d = stage("D", "No CV out yet", "c-mute", "");
    var groups = {};
    cold.concat(ready).forEach(function (r) {
      var g = groups[r.company] || (groups[r.company] =
        { company: r.company, roles: 0, best: 0, warm: false, hint: false });
      g.roles++;
      if ((r.fit || 0) > g.best) g.best = r.fit || 0;
      if (r.warm) g.warm = true;
      if (r.warm_hinted) g.hint = true;
    });
    var arr = Object.keys(groups).map(function (k) { return groups[k]; })
      .sort(function (x, y) { return y.best - x.best; });
    d.chip.textContent = arr.length + " companies · " + cold.concat(ready).length + " roles";

    var wrap = el("div", "tablewrap"), tbl = document.createElement("table");
    tbl.innerHTML = "<thead><tr><th>Company</th><th>Roles</th><th>Best fit</th><th>Warm</th><th>Packet</th></tr></thead>";
    var tb = document.createElement("tbody");
    arr.forEach(function (g) {
      var tr = tb.insertRow();
      var c1 = tr.insertCell(); c1.className = "job"; c1.textContent = g.company;
      var c2 = tr.insertCell(); c2.className = "co";
      c2.textContent = g.roles === 1 ? "1 role" : g.roles + " roles";
      tr.insertCell().appendChild(JH.fitCell(g.best));
      var c4 = tr.insertCell();
      if (g.warm) c4.appendChild(JH.star(true));
      else if (g.hint) c4.appendChild(JH.star(false));
      else { c4.className = "tiny"; c4.textContent = "—"; }
      var c5 = tr.insertCell(); c5.className = "linkcell";
      var p = JH.packetFor(g.company);
      if (p) c5.appendChild(JH.link("/download/packet/" + p.slug + ".zip", "Get packet"));
      else { c5.className = "tiny linkcell"; c5.textContent = "nothing written yet"; }
    });
    tbl.appendChild(tb); wrap.appendChild(tbl);
    d.body.appendChild(wrap);
    host.appendChild(d.root);
  })();

  /* ---------------- quick grabs ---------------- */
  (function quick() {
    var host = $("quickGrabs");
    clear(host);
    function grab(name, meta, desc, buttons) {
      var g = el("div", "grab"), t = el("div", "gt");
      t.appendChild(el("span", "gname", name));
      t.appendChild(el("span", "gmeta", meta));
      g.appendChild(t);
      g.appendChild(el("p", "lede", desc));
      var row = el("div", "grow");
      buttons.forEach(function (b) { row.appendChild(b); });
      g.appendChild(row);
      host.appendChild(g);
    }
    grab("Everything, zipped", "all CVs + drafts",
      "Every CV, every message, the highlight reel and the LinkedIn profile pack.",
      [JH.link("/download/all.zip", "Download .zip", "btn btn-sm btn-primary")]);

    (D.packets || []).forEach(function (p) {
      var btns = [];
      if (p.cv.has_pdf) btns.push(JH.link("/download/cv/" + p.cv.stem + ".pdf", "CV .pdf", "btn btn-sm btn-primary"));
      btns.push(JH.link("/download/packet/" + p.slug + ".zip", "Packet .zip"));
      grab(p.company, "ATS " + p.ats + (p.cv.pdf_kb ? " · " + p.cv.pdf_kb + " KB" : ""), p.role, btns);
    });

    var gb = [];
    if (D.generalCv.has_pdf) gb.push(JH.link("/download/cv/" + D.generalCv.stem + ".pdf", "CV .pdf", "btn btn-sm btn-primary"));
    gb.push(JH.link(D.generalCv.url, "On GitHub"));
    grab("General CV", "the one in every message",
      "Untailored. The only CV a recruiter is ever linked to.", gb);
  })();

  /* ---------------- board table ---------------- */
  function match(r) {
    var f = state.filter;
    if (f === "warm") { if (!r.warm && !r.warm_hinted) return false; }
    else if (f === "remote") { if (!/remote/i.test(r.work_type || "")) return false; }
    else if (f !== "all" && r.stage !== f) return false;
    if (state.query) {
      var hay = (r.job + " " + r.company + " " + (r.location || "")).toLowerCase();
      if (hay.indexOf(state.query) === -1) return false;
    }
    return true;
  }
  function renderTable() {
    var tb = $("boardTable").tBodies[0];
    clear(tb);
    var rows = D.board.filter(match);
    if (!rows.length) {
      var tr = tb.insertRow(), td = tr.insertCell();
      td.colSpan = 8; td.className = "empty"; td.textContent = "Nothing matches that filter.";
      return;
    }
    rows.forEach(function (r) {
      var tr = tb.insertRow();
      tr.insertCell().appendChild(JH.fitCell(r.fit));
      var j = tr.insertCell(); j.className = "job"; j.textContent = r.job;
      var c = tr.insertCell(); c.className = "co"; c.textContent = r.company;
      var t = tr.insertCell(); t.className = "tiny"; t.textContent = r.work_type || "—";
      var w = tr.insertCell(); w.className = "tiny"; w.textContent = r.location || "—";
      tr.insertCell().appendChild(JH.stageChip(r.stage));
      var wa = tr.insertCell();
      if (r.warm) wa.appendChild(JH.star(true));
      else if (r.warm_hinted) wa.appendChild(JH.star(false));
      else { wa.className = "tiny"; wa.textContent = "—"; }
      var lc = tr.insertCell(); lc.className = "linkcell";
      lc.appendChild(JH.link("/jobs?id=" + encodeURIComponent(r.id), "Open"));
    });
  }
  renderTable();

  $("boardFilters").addEventListener("click", function (e) {
    var b = e.target.closest(".chipbtn");
    if (!b) return;
    state.filter = b.dataset.f;
    Array.prototype.forEach.call(this.querySelectorAll(".chipbtn"), function (x) {
      x.setAttribute("aria-pressed", String(x === b));
    });
    renderTable();
  });
  $("boardSearch").addEventListener("input", function () {
    state.query = this.value.trim().toLowerCase();
    renderTable();
  });
});

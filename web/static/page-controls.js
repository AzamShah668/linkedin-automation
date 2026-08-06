/* Run it: every pipeline step on a button, with live output.
   Safe steps run on one click. Heavy and send steps open a confirm panel first —
   the server enforces that too, so a stray fetch cannot fire outreach. */
JH.ready(function () {
  "use strict";
  var el = JH.el, clear = JH.clear, $ = JH.$;
  var actions = [];
  var activeRun = null;
  var poll = null;

  var TIER = {
    safe:  { chip: "c-good", label: "safe", blurb: "Reads only. Nothing leaves this machine." },
    heavy: { chip: "c-acc",  label: "heavy", blurb: "Drives a Claude session. Slow, costs tokens, writes to Notion and Slack." },
    send:  { chip: "c-crit", label: "sends to a person", blurb: "Puts a message in front of a real person. Cannot be undone." }
  };
  var GROUPS = [
    ["safe", "Check and refresh", "Run these freely. Start here when something looks wrong."],
    ["heavy", "Find and classify", "These wake a headless Claude. Minutes, not seconds."],
    ["send", "Reach out", "These two are the only steps that contact a human. Both ask first."]
  ];

  /* ---------------- preflight ---------------- */
  function renderPreflight(p) {
    var host = $("preflight");
    clear(host);
    var cls = p.verdict === "contended" ? "banner" : "banner ok";
    var box = el("div", cls);
    var title = p.verdict === "contended"
      ? "LinkedIn steps will fail right now"
      : "LinkedIn is clear to run";
    box.appendChild(el("h3", null, title));
    box.appendChild(el("p", null, p.detail));
    var meta = el("p", "lede");
    meta.style.marginTop = "6px";
    meta.textContent = "Servers running: " + p.servers.length +
      (p.session_saved ? " · session last saved " + JH.day(p.session_saved) + " " + JH.clock(p.session_saved) : "") +
      ". " + p.note;
    box.appendChild(meta);
    var again = el("button", "btn btn-sm", "Re-check");
    again.style.marginTop = "9px";
    again.addEventListener("click", loadPreflight);
    box.appendChild(again);
    host.appendChild(box);
  }
  function loadPreflight() {
    JH.api("/api/preflight").then(renderPreflight).catch(function (e) {
      clear($("preflight"));
      $("preflight").appendChild(el("div", "banner", "Could not run the preflight check: " + e.message));
    });
  }

  /* ---------------- action cards ---------------- */
  function actionCard(a) {
    var card = el("div", "actcard tier-" + a.tier);
    var head = el("div", "actcard-head");
    head.appendChild(el("h4", null, a.label));
    head.appendChild(el("span", "chip " + TIER[a.tier].chip, TIER[a.tier].label));
    card.appendChild(head);
    card.appendChild(el("p", "lede", a.blurb));
    var cmd = el("code", "cmdline", a.cmd);
    card.appendChild(cmd);

    var foot = el("div", "actcard-foot");
    var run = el("button", "btn" + (a.tier === "send" ? " btn-danger" : a.tier === "heavy" ? "" : " btn-primary"),
      a.tier === "safe" ? "Run" : "Run…");
    run.addEventListener("click", function () {
      if (a.tier === "safe") return fire(a, false);
      confirmPanel(card, a);
      run.disabled = true;
    });
    foot.appendChild(run);
    card.appendChild(foot);
    return card;
  }

  function confirmPanel(card, a) {
    var existing = card.querySelector(".confirm");
    if (existing) return;
    var box = el("div", "confirm");
    box.appendChild(el("p", "warn-line", a.tier === "send"
      ? "This sends real messages. Read what it does above, then confirm."
      : "This starts a headless Claude run. Confirm to go ahead."));
    var row = el("div", "grow");
    var yes = el("button", "btn " + (a.tier === "send" ? "btn-danger" : "btn-primary"),
      a.tier === "send" ? "Yes, send for real" : "Yes, run it");
    yes.addEventListener("click", function () {
      box.remove();
      card.querySelector(".actcard-foot .btn").disabled = false;
      fire(a, true);
    });
    var no = el("button", "btn", "Cancel");
    no.addEventListener("click", function () {
      box.remove();
      card.querySelector(".actcard-foot .btn").disabled = false;
    });
    row.appendChild(yes); row.appendChild(no);
    box.appendChild(row);
    card.appendChild(box);
  }

  function fire(a, confirm) {
    JH.post("/api/run", { action: a.key, confirm: !!confirm }).then(function (run) {
      JH.toast("Started: " + a.label);
      watch(run);
    }).catch(function (e) {
      JH.toast(e.message);
      renderRun({ label: a.label, status: "failed", exit: null,
                  started: new Date().toISOString(), lines: ["Could not start: " + e.message] });
    });
  }

  /* ---------------- live output ---------------- */
  function renderRun(run) {
    var host = $("runPane");
    clear(host);
    var panel = el("div", "panel");
    var head = el("div", "panel-head");
    head.appendChild(el("h3", null, run.label));
    var statusChip = run.status === "running" ? "c-acc"
      : run.status === "done" ? "c-good" : "c-warn";
    head.appendChild(el("span", "chip " + statusChip, run.status));
    if (run.exit != null) head.appendChild(el("span", "count", "exit " + run.exit));
    head.appendChild(el("span", "count", JH.ago(run.started)));
    if (run.status === "running" && run.id) {
      var stop = el("button", "btn btn-sm btn-danger", "Stop");
      stop.addEventListener("click", function () {
        JH.post("/api/run/" + run.id + "/stop", {}).then(function () { JH.toast("Stopping"); });
      });
      head.appendChild(stop);
    }
    panel.appendChild(head);
    var body = el("div", "panel-body");
    var pre = el("pre", "console", (run.lines || []).join("\n") || "waiting for output…");
    body.appendChild(pre);
    panel.appendChild(body);
    host.appendChild(panel);
    pre.scrollTop = pre.scrollHeight;
  }

  function watch(run) {
    activeRun = run.id;
    renderRun(run);
    clearInterval(poll);
    poll = setInterval(function () {
      JH.api("/api/run/" + activeRun).then(function (r) {
        renderRun(r);
        if (r.status !== "running") {
          clearInterval(poll);
          poll = null;
          loadHistory();
          if (r.status === "done") JH.toast(r.label + " finished");
        }
      }).catch(function () { clearInterval(poll); poll = null; });
    }, 1200);
  }

  /* ---------------- history ---------------- */
  function loadHistory() {
    JH.api("/api/runs").then(function (runs) {
      var host = $("runHistory");
      clear(host);
      if (!runs.length) {
        host.appendChild(el("div", "empty-state", "Nothing has been run from here yet."));
        return;
      }
      runs.forEach(function (r) {
        var row = el("div", "runrow");
        var cls = r.status === "done" ? "c-good" : r.status === "running" ? "c-acc" : "c-warn";
        row.appendChild(el("span", "chip " + cls, r.status));
        row.appendChild(el("span", "rl", r.label));
        row.appendChild(el("span", "count", JH.day(r.started) + " " + JH.clock(r.started) + " · " + JH.ago(r.started)));
        var view = el("button", "btn btn-sm", "Output");
        view.addEventListener("click", function () {
          JH.api("/api/run/" + r.id).then(function (full) {
            if (full.status === "running") watch(full); else renderRun(full);
            window.scrollTo({ top: $("runPane").offsetTop - 80, behavior: "smooth" });
          });
        });
        row.appendChild(view);
        host.appendChild(row);
      });
    }).catch(function () {});
  }

  /* ---------------- boot ---------------- */
  JH.api("/api/actions").then(function (list) {
    actions = list;
    var host = $("actions");
    clear(host);
    GROUPS.forEach(function (g) {
      var mine = actions.filter(function (a) { return a.tier === g[0]; });
      if (!mine.length) return;
      var h = el("h3", "grouphead", g[1]);
      host.appendChild(h);
      host.appendChild(el("p", "lede", g[2]));
      var grid = el("div", "actgrid");
      mine.forEach(function (a) { grid.appendChild(actionCard(a)); });
      host.appendChild(grid);
    });
  }).catch(function (e) {
    $("actions").appendChild(el("div", "banner", "Could not load the action list: " + e.message));
  });

  loadPreflight();
  loadHistory();
});

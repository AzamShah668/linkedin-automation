/* Console page: the whole pipeline in one screen — progress, the ranked action queue, the
   Easy-Apply / external split, what to learn, and what the machine can do unaided.

   It fetches /api/console for its own data rather than reusing the board bootstrap, because it
   needs three sources the board does not carry: the triage cache (can this job be one-click
   applied to?), the append-only apply ledger, and the coverage report. */
JH.ready(function () {
  "use strict";
  var el = JH.el, $ = JH.$, api = JH.api, post = JH.post;

  /* ---------------- the live loop ----------------
     The page polls instead of being loaded once. Two rules it must not break:

     1. It SAYS it is polling, and shows when each source was last written. A page that silently
        refreshes is indistinguishable from a page that has frozen.
     2. Polling STOPS while the tab is hidden and resumes on focus. A background tab hammering
        the backend every few seconds is how a local server ends up blamed for being slow. */
  var POLL_MS = 15000;
  var timer = null, inflight = false, failures = 0, lastData = null;

  function setLive(state, text) {
    var n = $("live");
    n.className = "live" + (state ? " " + state : "");
    n.lastChild.nodeValue = text;
  }

  function tick(manual) {
    if (inflight) { return; }
    inflight = true;
    if (manual) { $("refreshBtn").classList.add("busy"); }
    return api("/api/console").then(function (D) {
      failures = 0;
      lastData = D;
      render(D);
      setLive("", "live");
    }).catch(function (e) {
      failures++;
      // Never let a failed poll leave stale numbers looking current.
      setLive("err", "stale · " + (e.message || "backend unreachable"));
      if (failures === 1 && !lastData) {
        var m = $("main");
        m.insertBefore(el("p", "lede", "Could not load the console: " + e.message), m.firstChild);
      }
    }).then(function () {
      inflight = false;
      $("refreshBtn").classList.remove("busy");
    });
  }

  function start() {
    if (timer) { return; }
    tick();
    timer = setInterval(function () {
      if (document.hidden) { return; }
      tick();
    }, POLL_MS);
  }

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
      setLive("paused", "paused");
    } else {
      setLive("", "live");
      tick();   // catch up immediately rather than waiting out the interval
    }
  });
  $("refreshBtn").addEventListener("click", function () { tick(true); });
  start();

  /* ---------------- helpers ---------------- */
  var SVGNS = "http://www.w3.org/2000/svg";
  function svg(w, h) {
    var s = document.createElementNS(SVGNS, "svg");
    s.setAttribute("viewBox", "0 0 " + w + " " + h);
    s.setAttribute("role", "img");
    return s;
  }
  function mk(t, a) {
    var n = document.createElementNS(SVGNS, t);
    for (var k in a) { n.setAttribute(k, a[k]); }
    return n;
  }
  function tok(n) {
    return getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  }
  var tip = $("tip");
  function wire(node, text) {
    node.style.cursor = "crosshair";
    node.addEventListener("pointerenter", function () {
      tip.textContent = text; tip.style.opacity = "1";
    });
    node.addEventListener("pointermove", function (e) {
      tip.style.left = Math.min(e.clientX + 13, window.innerWidth - tip.offsetWidth - 8) + "px";
      tip.style.top = (e.clientY - 32) + "px";
    });
    node.addEventListener("pointerleave", function () { tip.style.opacity = "0"; });
  }

  /* ---------------- render ---------------- */
  function render(D) {
    var H = D.headline;

    // Idempotent by construction: every host is emptied before it is drawn. render() runs on
    // every poll, so anything that appends without clearing would grow the page forever.
    ["metrics", "freshness", "acts", "c-time", "c-funnel", "c-chan", "c-kind",
     "sk-demand", "sk-gap", "caps", "tl"].forEach(function (id) { JH.clear($(id)); });
    ["t-easy", "t-ext", "t-sent"].forEach(function (id) {
      JH.clear($(id).querySelector("tbody"));
    });

    freshness(D.sources || []);
    var stamp = $("stamp");
    if (stamp) {
      stamp.dataset.own = "1";   // stop common.js stamping the misleading "board synced Xd ago"
      stamp.textContent = "read " + (D.fetched || "").replace("T", " ").slice(0, 16);
    }

    // A source that failed must say so. A page rendering zeros looks identical to a page whose
    // data vanished — the exact confusion this project has been bitten by repeatedly.
    if (D.warnings && D.warnings.length) {
      var w = $("callout");
      w.hidden = false;
      w.innerHTML = "<p><strong>Some data could not be read, so the numbers below are "
        + "incomplete:</strong> " + D.warnings.join(" · ") + "</p>";
    } else {
      var c = $("callout");
      c.hidden = false;
      c.innerHTML = "<p><strong>The number that ran this project for two weeks was wrong.</strong> "
        + "Eight consecutive checks reported “zero replies”. All eight were honest about "
        + "the only place they looked — Gmail. Nothing had ever opened the LinkedIn inbox, "
        + "where a warm contact had answered <strong>within two hours</strong> asking for the CV. "
        + "Real score: <strong>" + H.applications + " applications, " + Math.max(1, H.replies)
        + " reply</strong>, and it came from the single warmest approach ever made.</p>";
    }

    metrics(H);
    actions();
    chartTime(D.series30);
    chartFunnel(H);
    chartChannel(D.channels);
    chartKind(H);
    jobTable("t-easy", D.easyApplyJobs, "Open");
    jobTable("t-ext", D.externalJobs, "Visit site");
    sentTable(D);
    $("n-easy").textContent = D.easyApplyJobs.length;
    $("n-ext").textContent = D.externalJobs.length;
    boardState.rows = D.board || [];
    renderBoard();
    skills();
    capabilities();
    timeline();
  }

  /* ---------------- the whole board ----------------
     Ported from the old index page, which is gone. Its data was always live — the page only
     LOOKED stale because it stamped "board synced Xd ago", which describes the last Notion
     capture and nothing else on the page. */
  var boardState = { rows: [], filter: "live", query: "" };

  function boardMatch(r) {
    var q = boardState.query;
    if (q && ((r.company || "") + " " + (r.job || "")).toLowerCase().indexOf(q) < 0) { return false; }
    var st = (r.status || "").toLowerCase();
    switch (boardState.filter) {
      case "live":    return st !== "applied" && st !== "skipped";
      case "applied": return st === "applied";
      case "warm":    return !!(r.warm || r.warm_hinted);
      case "remote":  return /remote/i.test(r.work_type || "");
      case "top":     return (r.fit || 0) >= 85;
      default:        return true;
    }
  }

  function renderBoard() {
    var tb = $("boardTable").tBodies[0];
    JH.clear(tb);
    var rows = boardState.rows.filter(boardMatch)
      .sort(function (a, b) { return (b.fit || 0) - (a.fit || 0); });

    $("boardCount").textContent = rows.length + " of " + boardState.rows.length
      + " rows shown" + (boardState.filter === "live" ? " · applied and ruled-out rows hidden" : "");

    if (!rows.length) {
      var tr = tb.insertRow(), td = tr.insertCell();
      td.colSpan = 7; td.className = "empty"; td.textContent = "Nothing matches that filter.";
      return;
    }
    rows.forEach(function (r) {
      var tr = tb.insertRow();
      tr.insertCell().innerHTML = fitCell(r.fit || 0);
      var c = tr.insertCell(); c.style.fontWeight = "600"; c.style.whiteSpace = "nowrap";
      c.textContent = r.company || "?";
      var j = tr.insertCell();
      if (r.url) {
        j.innerHTML = '<a class="rolelink" href="' + esc(r.url)
          + '" target="_blank" rel="noopener">' + esc(r.job) + "</a>";
      } else { j.textContent = r.job || "?"; }
      var w = tr.insertCell();
      w.innerHTML = '<span class="chip' + (/remote/i.test(r.work_type || "") ? " c-good" : "")
        + '">' + esc(r.work_type || "—") + "</span>";
      var st = tr.insertCell();
      st.innerHTML = '<span class="chip">' + esc(r.status || "—") + "</span>";
      var wa = tr.insertCell(); wa.style.textAlign = "center";
      wa.innerHTML = (r.warm || r.warm_hinted) ? "★" : '<span style="color:var(--faint)">—</span>';
      var lc = tr.insertCell(); lc.style.textAlign = "right";
      lc.innerHTML = '<a class="go" href="/jobs?id=' + encodeURIComponent(r.id) + '">Open →</a>';
    });
  }

  $("boardFilters").addEventListener("click", function (e) {
    var b = e.target.closest(".chipbtn");
    if (!b) { return; }
    boardState.filter = b.dataset.f;
    Array.prototype.forEach.call(this.querySelectorAll(".chipbtn"), function (x) {
      x.setAttribute("aria-pressed", String(x === b));
    });
    renderBoard();
  });
  $("boardSearch").addEventListener("input", function () {
    boardState.query = this.value.trim().toLowerCase();
    renderBoard();
  });

  function humanAge(h) {
    if (h == null) { return "never"; }
    if (h < 1) { return Math.max(1, Math.round(h * 60)) + " min ago"; }
    if (h < 48) { return Math.round(h) + "h ago"; }
    return Math.round(h / 24) + " days ago";
  }

  /* Per-source freshness. These four update on completely different clocks, so one page-level
     "updated 2s ago" would be true about the fetch and a lie about the data. A stale source also
     offers the button that fixes it, rather than only complaining. */
  function freshness(sources) {
    var host = $("freshness");
    sources.forEach(function (s) {
      var n = el("div", "fr" + (s.stale ? " stale" : ""));
      n.appendChild(el("b", null, s.label));
      n.appendChild(el("span", "when", humanAge(s.ageH) + (s.stale ? " · stale" : "")));
      if (s.stale && s.action) {
        var b = el("button", null, "Refresh");
        b.type = "button";
        b.addEventListener("click", function () {
          b.disabled = true; b.textContent = "running…";
          post("/api/run", { action: s.action, confirm: true }).then(function () {
            JH.toast("Started: " + s.label + ". This page will pick it up when it finishes.");
          }).catch(function (e) {
            b.disabled = false; b.textContent = "Refresh";
            JH.toast("Could not start it: " + e.message);
          });
        });
        n.appendChild(b);
      }
      host.appendChild(n);
    });
  }

  function metrics(H) {
    var host = $("metrics");
    [["Applications sent", H.applications, ""],
     ["Companies reached", H.companies, ""],
     ["Replies received", Math.max(1, H.replies), "ok"],
     ["Sitting with nobody", H.noHuman, "hot"],
     ["One-click jobs left", H.easyApply, ""],
     ["Need a manual visit", H.external, ""]
    ].forEach(function (m) {
      var d = el("div", "metric" + (m[2] ? " " + m[2] : ""));
      d.appendChild(el("div", "k", m[0]));
      d.appendChild(el("div", "v", String(m[1])));
      host.appendChild(d);
    });
  }

  var ACTS = [
    [1, "you", "Reply to the Infosys insider — 16 days overdue",
     "He answered two hours after the message on 26 July, gave a phone number and asked for the CV. Nothing has been sent. He is inside the company that also holds the best unworked role on this board, and he is already a first-degree connection. No automation can do this one — it is a message to a personal phone number."],
    [1, "you", "Apply to Infosys Junior AI Engineer — fit 90",
     "The strongest role on the board, and the rare Junior-titled AI req that fits a final-year student. Responses are handled off LinkedIn, so it needs a visit to the Infosys portal. The tailored CV can now be built for it — that blocker was cleared."],
    [2, "sys", "Find one named human for Recro",
     "Applied on 29 July and it has reached nobody in 13 days. It is the only application on record with no recruiter identified at all."],
    [2, "sys", "Build the warm-insider finder",
     "Accepts are not the bottleneck — three of three older invites were accepted, including cold ones. Conversion is: accept-to-reply is one in three, and the one was the warm contact with shared background and mutual connections. Every cold approach has gone quiet."],
    [3, "sys", "Work the remaining one-click roles",
     "Each costs about fifteen seconds. Worth doing, but the evidence says a submission with nobody attached does not convert — so pair each with a named contact rather than sending more into the void."]
  ];
  function actions() {
    var host = $("acts");
    ACTS.forEach(function (a) {
      var n = el("div", "act p" + a[0]);
      n.appendChild(el("div", "stripe"));
      var b = el("div", "body");
      b.appendChild(el("h3", null, a[2]));
      b.appendChild(el("p", null, a[3]));
      b.appendChild(el("span", "who" + (a[1] === "you" ? " you" : ""),
        a[1] === "you" ? "Only you can do this" : "The system can do this"));
      n.appendChild(b);
      host.appendChild(n);
    });
  }

  function chartTime(data) {
    var W = 520, Hh = 168, P = { l: 26, r: 8, t: 12, b: 26 };
    var max = Math.max(2, Math.max.apply(null, data.map(function (d) { return d.n; })));
    var iw = W - P.l - P.r, ih = Hh - P.t - P.b, bw = iw / data.length;
    var s = svg(W, Hh);
    for (var i = 0; i <= max; i++) {
      var y = P.t + ih - (i / max) * ih;
      s.appendChild(mk("line", { x1: P.l, x2: W - P.r, y1: y, y2: y, "class": "gl" }));
      var tx = mk("text", { x: P.l - 6, y: y + 3.5, "class": "ax", "text-anchor": "end" });
      tx.textContent = i; s.appendChild(tx);
    }
    data.forEach(function (d, i) {
      var x = P.l + i * bw, h = (d.n / max) * ih, last = i === data.length - 1;
      if (d.n > 0) {
        var r = mk("rect", { x: x + 1.5, y: P.t + ih - h, width: Math.max(2, bw - 3),
          height: h, rx: 2, fill: last ? tok("--s2") : tok("--s1") });
        s.appendChild(r);
        wire(r, d.d + " · " + d.n + " application" + (d.n > 1 ? "s" : ""));
      }
      if (i % 7 === 0 || last) {
        var t = mk("text", { x: x + bw / 2, y: Hh - 8, "class": "ax", "text-anchor": "middle" });
        t.textContent = d.d.slice(8) + "/" + d.d.slice(5, 7); s.appendChild(t);
      }
    });
    $("c-time").appendChild(s);
  }

  function chartFunnel(H) {
    var rows = [["Applications sent", H.applications, tok("--s1")],
                ["Distinct companies", H.companies, tok("--s1")],
                ["Reached a real person", H.reachedHuman, tok("--s3")],
                ["Replied", Math.max(1, H.replies), tok("--s2")]];
    bars($("c-funnel"), rows, 150);
  }

  function bars(host, rows, labW) {
    var W = 520, rh = 33, Hh = rows.length * rh + 8;
    var max = Math.max.apply(null, rows.map(function (r) { return r[1]; })) || 1;
    var iw = W - labW - 46;
    var s = svg(W, Hh);
    rows.forEach(function (r, i) {
      var y = i * rh + 6, w = Math.max(3, (r[1] / max) * iw);
      var lab = mk("text", { x: 0, y: y + 16, "class": "ax", "font-size": "11.5" });
      lab.setAttribute("fill", tok("--muted")); lab.textContent = r[0]; s.appendChild(lab);
      var bar = mk("rect", { x: labW, y: y + 4, width: w, height: 16, rx: 3, fill: r[2] });
      s.appendChild(bar); wire(bar, r[0] + ": " + r[1]);
      var v = mk("text", { x: labW + w + 8, y: y + 16.5, "class": "vl" });
      v.textContent = r[1]; s.appendChild(v);
    });
    host.appendChild(s);
  }

  function chartChannel(channels) {
    var NAME = { "linkedin-easy-apply": "Easy Apply form", "email": "Email to a person",
                 "linkedin-dm": "LinkedIn message" };
    var REPLIED = { "linkedin-dm": 1 };
    var W = 520, rh = 40, Hh = channels.length * rh + 20;
    var max = Math.max.apply(null, channels.map(function (c) { return c.n; })) || 1;
    var s = svg(W, Hh), iw = W - 200;
    channels.forEach(function (c, i) {
      var name = NAME[c.k] || c.k, rep = REPLIED[c.k] || 0;
      var y = i * rh + 8, w = Math.max(3, (c.n / max) * iw);
      var lab = mk("text", { x: 0, y: y + 15, "class": "ax", "font-size": "11.5" });
      lab.setAttribute("fill", tok("--muted")); lab.textContent = name; s.appendChild(lab);
      var bar = mk("rect", { x: 150, y: y + 4, width: w, height: 15, rx: 3, fill: tok("--s1") });
      s.appendChild(bar); wire(bar, name + ": " + c.n + " sent");
      var v = mk("text", { x: 150 + w + 8, y: y + 16, "class": "vl" });
      v.textContent = c.n; s.appendChild(v);
      var rl = mk("text", { x: 150, y: y + 31, "class": "ax", "font-size": "10.5" });
      rl.textContent = rep ? rep + " reply" : "no reply";
      rl.setAttribute("fill", rep ? tok("--s2") : tok("--faint"));
      s.appendChild(rl);
      if (rep) {
        s.appendChild(mk("rect", { x: 136, y: y + 24, width: 9, height: 9, rx: 2, fill: tok("--s2") }));
      }
    });
    var host = $("c-chan");
    host.appendChild(s);
    var lg = el("div", "legend");
    lg.innerHTML = '<span><i style="background:' + tok("--s1") + '"></i>Applications sent</span>'
      + '<span><i style="background:' + tok("--s2") + '"></i>Produced a reply</span>';
    host.appendChild(lg);
  }

  function chartKind(H) {
    var rows = [["Easy Apply", H.easyApply, tok("--s1")],
                ["External site", H.external, tok("--s3")],
                ["Closed / removed", H.dead, tok("--faint")]];
    var tot = rows.reduce(function (a, r) { return a + r[1]; }, 0) || 1;
    var W = 520, s = svg(W, 46), x = 0;
    rows.forEach(function (r) {
      var w = (r[1] / tot) * W;
      var bar = mk("rect", { x: x + (x ? 1 : 0), y: 6, width: Math.max(1, w - 2),
        height: 26, rx: 3, fill: r[2] });
      s.appendChild(bar); wire(bar, r[0] + ": " + r[1] + " of " + tot);
      if (w > 62) {
        var t = mk("text", { x: x + w / 2, y: 24, "class": "vl", "text-anchor": "middle" });
        t.textContent = r[1]; t.setAttribute("fill", "#fff"); s.appendChild(t);
      }
      x += w;
    });
    var host = $("c-kind");
    host.appendChild(s);
    var lg = el("div", "legend");
    lg.innerHTML = rows.map(function (r) {
      return '<span><i style="background:' + r[2] + '"></i>' + r[0] + " · " + r[1] + "</span>";
    }).join("");
    host.appendChild(lg);
  }

  function fitCell(f) {
    var w = Math.max(4, Math.round((f - 70) / 25 * 54));
    return '<div class="fitcell"><b>' + f + '</b><i class="' + (f < 82 ? "lo" : "")
      + '" style="width:' + w + 'px"></i></div>';
  }
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function jobTable(id, rows, cta) {
    var tb = $(id).querySelector("tbody");
    rows.forEach(function (r) {
      var tr = el("tr");
      var remote = /remote/i.test(r.work_type || "");
      tr.innerHTML = "<td>" + fitCell(r.fit) + "</td>"
        + '<td style="font-weight:600;white-space:nowrap">' + esc(r.company) + "</td>"
        + '<td><a class="rolelink" href="' + esc(r.url) + '" target="_blank" rel="noopener">'
        + esc(r.job) + "</a></td>"
        + '<td><span class="chip' + (remote ? " c-good" : "") + '">'
        + esc(r.work_type || "—") + "</span></td>"
        + '<td style="text-align:right"><a class="go" href="' + esc(r.url)
        + '" target="_blank" rel="noopener">' + cta + " →</a></td>";
      tb.appendChild(tr);
    });
  }
  function sentTable(D) {
    var CH = { "linkedin-easy-apply": "Easy Apply", "email": "Email", "linkedin-dm": "LinkedIn message" };
    var tb = $("t-sent").querySelector("tbody");
    var gaps = (D.gaps || []).map(function (g) { return g.toLowerCase(); });
    D.applied.forEach(function (r) {
      var isGap = gaps.indexOf((r.company || "").toLowerCase()) >= 0;
      var st = isGap
        ? '<span class="chip c-crit">no — needs a contact</span>'
        : '<span class="chip c-good">yes</span>';
      var tr = el("tr");
      tr.innerHTML = '<td style="font-family:var(--mono);font-size:12px;white-space:nowrap">'
        + esc(r.submitted_at) + "</td>"
        + '<td style="font-weight:600;white-space:nowrap">' + esc(r.company) + "</td>"
        + "<td>" + esc(r.role) + "</td>"
        + '<td><span class="chip">' + esc(CH[r.channel] || r.channel) + "</span></td>"
        + "<td>" + st + "</td>";
      tb.appendChild(tr);
    });
  }

  var DEMAND = [["Platform / infrastructure", 19, 1], ["SRE & reliability", 14, 1],
    ["RAG pipelines", 14, 1], ["LLM applications", 14, 1], ["Agentic systems", 9, 1],
    ["AWS", 9, 0], ["GenAI delivery", 8, 1], ["MLOps", 7, 1], ["CI/CD", 6, 1]];
  var GAPS = [
    ["Azure — AKS, Key Vault, Monitor", 95, "Named in roughly 60% of the requirements on the roles you scored worst against. Your single most expensive gap."],
    ["Terraform / Bicep", 80, "Listed as in progress. Ansible covers configuration but not provisioning, and every infrastructure req asks for it."],
    ["Container security scanning", 65, "Trivy, CVE triage, image policy. Marked critical on several descriptions and currently absent."],
    ["Grafana dashboards", 50, "You already run Prometheus, so this is the cheapest gap on the list to close."],
    ["Kubernetes RBAC & policy", 45, "Network policies, HPA, pod security standards. You run clusters; this is the governance half."]];
  function skills() {
    var d1 = $("sk-demand");
    DEMAND.forEach(function (s) {
      var n = el("div", "sk");
      n.innerHTML = '<div class="sk-top"><b>' + s[0] + "</b><span>" + s[1] + " mentions</span></div>"
        + '<div class="sk-bar"><i style="width:' + (s[1] / 19 * 100) + "%;background:"
        + (s[2] ? tok("--s1") : tok("--s5")) + '"></i></div>'
        + '<div class="sk-note">' + (s[2] ? "You have shipped evidence here"
          : "Partial evidence — worth deepening") + "</div>";
      d1.appendChild(n);
    });
    var d2 = $("sk-gap");
    GAPS.forEach(function (g) {
      var n = el("div", "sk");
      n.innerHTML = '<div class="sk-top"><b>' + g[0] + "</b><span>"
        + (g[1] >= 80 ? "high cost" : g[1] >= 60 ? "medium" : "quick win") + "</span></div>"
        + '<div class="sk-bar"><i style="width:' + g[1] + "%;background:"
        + (g[1] >= 80 ? tok("--s2") : g[1] >= 60 ? tok("--s4") : tok("--s5")) + '"></i></div>'
        + '<div class="sk-note">' + g[2] + "</div>";
      d2.appendChild(n);
    });
  }

  var CAPS = [
    ["Fill and submit Easy Apply forms", 1, "Reads a fixed answer bank, fills about 40 known questions in roughly fifteen seconds, and refuses to invent an answer. A blank beats a wrong one.", "run.py apply-all --submit"],
    ["Write a CV tailored to one job", 1, "Reads the real job description and builds a CV, cover letter and recruiter pitch from verified evidence only. About seven minutes each.", "run.py packet --job-id <id>"],
    ["Never apply twice", 1, "An append-only ledger checked before the page even loads. It depends on no board status, because those have been wrong before.", "run.py ledger"],
    ["Watch the LinkedIn inbox", 1, "Added after a reply sat unseen for sixteen days. Anything it cannot classify is escalated rather than ignored.", "apps/autopilot/replies.py"],
    ["Count applications that reached nobody", 1, "Reports on every run how many submissions have a named human attached.", "apps/autopilot/coverage.py"],
    ["Screen out companies with no one behind them", 1, "Blocks employers proven to have no findable staff. Caught a third such posting before it spent a slot.", "apps/autopilot/sourcing.py"],
    ["Classify the whole board", 1, "Opens every live posting to record whether it has an Easy Apply button. This page is built from that probe.", "apps/autopilot/triage.py"],
    ["Find a recruiter and send an invite", 0, "Research runs read-only; the connection request itself waits for your approval. Automating this is what gets accounts restricted.", "Slack card → you approve"],
    ["Message a personal phone number", 0, "Deliberately not automated, and not planned. The Infosys reply is waiting on exactly this.", "—"]];
  function capabilities() {
    var host = $("caps");
    CAPS.forEach(function (c) {
      var n = el("div", "cap-c");
      n.innerHTML = "<h3>" + c[0] + '<span class="state ' + (c[1] ? "on" : "man") + '">'
        + (c[1] ? "automatic" : "needs you") + "</span></h3><p>" + c[2] + "</p><code>"
        + esc(c[3]) + "</code>";
      host.appendChild(n);
    });
  }

  var TL = [
    ["26 Jul", "First warm approach, and the only reply so far", 1, "A connection request to a fellow Kashmiri inside Infosys was accepted in three hours. The pitch went out at 16:43. He replied at 18:58 asking for the CV on his phone. Nobody saw it for sixteen days."],
    ["29–30 Jul", "Three tailored CVs reach real recruiters by email", 0, "Innova ESI, GoodSpace and CodeRound, each with a CV written for that specific job. No bounces. No replies either."],
    ["1 Aug", "The sleep day", 0, "The laptop slept through a full day, then fired five overdue jobs within three seconds. Ordering was missing, not catch-up. An atomic lock fixed it."],
    ["6 Aug", "The rewrite starts working", 0, "A Python runner replaced the agent for form filling: about fifteen seconds a form instead of sixteen minutes, and no invented answers."],
    ["9–10 Aug", "Eight real submissions, and the flaw in doing it fast", 1, "Volume arrived. So did the problem: five of the eight reached nobody at all. Applying became cheap enough that nothing forced the question of whether it was worth sending."],
    ["10 Aug", "A wrong answer on a real form", 0, "A pattern matched “have you interviewed at any of our locations” and typed the candidate’s home city into it. It passed every guard, because the value genuinely came from the approved bank."],
    ["11 Aug", "The blind spot closes", 1, "The pipeline read the LinkedIn inbox for the first time and surfaced the sixteen-day-old reply on its own, unprompted."]];
  function timeline() {
    var host = $("tl");
    TL.forEach(function (t) {
      var n = el("div", "tl-i" + (t[2] ? " key" : ""));
      n.innerHTML = '<div class="tl-d">' + t[0] + "</div><h3>" + t[1] + "</h3><p>" + t[3] + "</p>";
      host.appendChild(n);
    });
  }
});

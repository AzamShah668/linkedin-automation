/* Jobs & CV: role list, job detail with the apply link, tailored CV with a real download. */
JH.ready(function (D) {
  "use strict";
  var el = JH.el, clear = JH.clear, $ = JH.$;
  var state = { query: "", id: new URLSearchParams(location.search).get("id") };

  function renderList() {
    var host = $("jobList");
    clear(host);
    var rows = D.board.filter(function (r) {
      return !state.query || (r.job + " " + r.company).toLowerCase().indexOf(state.query) !== -1;
    });
    $("jobCount").textContent = rows.length + " roles";
    rows.forEach(function (r) {
      var li = document.createElement("li");
      var b = el("button", "jobbtn");
      b.setAttribute("aria-current", String(state.id === r.id));
      b.appendChild(el("span", "jt", r.job));
      var m = el("div", "jm");
      m.appendChild(el("span", "jf", String(r.fit == null ? "—" : r.fit)));
      m.appendChild(el("span", null, r.company));
      if (r.warm || r.warm_hinted) m.appendChild(JH.star(!!r.warm));
      b.appendChild(m);
      b.appendChild(JH.stageChip(r.stage));
      b.addEventListener("click", function () { show(r.id); });
      li.appendChild(b);
      host.appendChild(li);
    });
  }

  /* Marking a role done by hand. The board can only read Notion, so when he applies
     himself nothing else would ever flip this row off "packet ready". */
  function statusControl(r) {
    var box = el("div", "statusbox");
    var now = el("p", "statusnow");
    now.appendChild(document.createTextNode("Status: "));
    now.appendChild(el("strong", null, r.status || "New"));
    if (r.applied) now.appendChild(el("span", "count", " · applied " + r.applied));
    box.appendChild(now);

    var delivered = r.stage === "delivered";
    var row = el("div", "grow");

    if (!delivered) {
      var mark = el("button", "btn btn-primary", "I sent the CV — mark as applied");
      mark.addEventListener("click", function () { change(r, "Applied", mark); });
      row.appendChild(mark);
    } else {
      var iv = el("button", "btn", "Got an interview");
      iv.addEventListener("click", function () { change(r, "Interview", iv); });
      row.appendChild(iv);
    }

    var others = [["Invite sent", "Invite sent"], ["Rejected", "Rejected"],
                  ["Skipped", "Not for me"], ["To Apply", "Back to packet ready"]];
    var sel = el("select", "statussel");
    sel.appendChild(el("option", null, "Something else…"));
    others.forEach(function (o) {
      if (o[0] === r.status) return;
      var opt = el("option", null, o[1]);
      opt.value = o[0];
      sel.appendChild(opt);
    });
    sel.addEventListener("change", function () {
      if (!this.value) return;
      change(r, this.value, sel);
      this.selectedIndex = 0;
    });
    row.appendChild(sel);
    box.appendChild(row);

    box.appendChild(notionRow());
    return box;
  }

  /* The "and update everything else" half: one button that writes Notion and
     re-aligns the local capture, so no manual bookkeeping is left over. */
  function notionRow() {
    var wrap = el("div", "notionrow");
    var pend = (JH.data().stats || {}).pending_notion || 0;
    if (!pend) {
      wrap.appendChild(el("p", "notionok", "Notion is up to date."));
      return wrap;
    }
    wrap.className = "notionrow pending";
    wrap.appendChild(el("p", "notionpend",
      pend + " change" + (pend === 1 ? "" : "s") + " made here " +
      (pend === 1 ? "is" : "are") + " not in Notion yet."));
    var btn = el("button", "btn btn-primary", "Push to Notion now");
    btn.addEventListener("click", function () {
      btn.disabled = true;
      btn.textContent = "Pushing…";
      JH.post("/api/notion/push", {}).then(function (res) {
        var D2 = JH.data();
        D2.stats.pending_notion = res.pending || 0;
        if (res.notion === "needs_token") {
          JH.toast("Local side aligned — Notion needs a token");
        } else {
          JH.toast(res.pushed ? "Pushed " + res.pushed + " to Notion" : (res.message || "Nothing to push"));
        }
        show(state.id);                              // re-render with the new state
      }).catch(function (e) {
        btn.disabled = false;
        btn.textContent = "Push to Notion now";
        JH.toast("Push failed: " + e.message);
      });
    });
    wrap.appendChild(btn);
    return wrap;
  }

  function change(r, status, control) {
    control.disabled = true;
    JH.post("/api/job/" + encodeURIComponent(r.id) + "/status", { status: status })
      .then(function (res) {
        // Keep the in-memory board in step so every panel re-renders correctly.
        var D2 = JH.data();
        for (var i = 0; i < D2.board.length; i++) {
          if (D2.board[i].id === res.job.id) { D2.board[i] = res.job; break; }
        }
        D2.stats.pending_notion = res.pending_notion;
        recount(D2);
        JH.toast("Marked as " + status);
        renderList();
        show(res.job.id);
      })
      .catch(function (e) {
        control.disabled = false;
        JH.toast("Could not change it: " + e.message);
      });
  }

  /* Stage counts feed the Board page's tiles; recompute so a later visit is right. */
  function recount(D2) {
    var by = {};
    D2.board.forEach(function (x) { by[x.stage] = (by[x.stage] || 0) + 1; });
    D2.stats.by_stage = by;
  }

  /* The only irreversible button on this page. Two clicks on purpose: an application
     cannot be withdrawn and a company only ever reads the first one. */
  function applyPanel(p, r) {
    var card = el("div", "cvcard");
    var head = el("div", "panel-head");
    head.appendChild(el("h3", null, "Apply"));
    card.appendChild(head);
    var body = el("div", "panel-body");

    if (r.status === "Applied" || r.stage === "delivered") {
      body.appendChild(el("p", "lede",
        "Already applied" + (r.applied ? " on " + r.applied : "") +
        ". Never sent twice: a duplicate application reads worse than none."));
      card.appendChild(body);
      return card;
    }

    body.appendChild(el("p", "lede",
      "Fills and submits the LinkedIn Easy Apply form for " + r.company + ", attaching " +
      p.cv.stem + ".pdf, the CV written for this company. Answers come only from your " +
      "answer bank; anything it does not know is left blank rather than guessed."));

    var run = el("button", "btn btn-primary", "Apply on LinkedIn now");
    var out = el("pre", "console buildout");
    out.hidden = true;
    var armed = false;

    run.addEventListener("click", function () {
      if (!armed) {
        armed = true;
        run.textContent = "Really submit? This cannot be undone";
        setTimeout(function () {
          if (!armed) return;
          armed = false;
          run.textContent = "Apply on LinkedIn now";
        }, 6000);
        return;
      }
      armed = false;
      run.disabled = true;
      run.textContent = "Applying… takes a few minutes";
      out.hidden = false;
      out.textContent = "starting…";
      JH.post("/api/run", { action: "apply", confirm: true, param: r.id })
        .then(function (job) { followBuild(job, out, run, "Application submitted"); })
        .catch(function (e) {
          run.disabled = false;
          run.textContent = "Apply on LinkedIn now";
          out.textContent = "Could not start: " + e.message;
        });
    });

    body.appendChild(run);
    body.appendChild(el("p", "lede",
      "Needs no other Claude window open — it drives the same browser."));
    body.appendChild(out);
    card.appendChild(body);
    return card;
  }

  function cvPanel(p, r) {
    var side = el("div", "cvside"), card = el("div", "cvcard");
    var head = el("div", "panel-head");
    head.appendChild(el("h3", null, "Tailored CV"));
    head.appendChild(el("span", "chip c-good", "ATS " + p.ats));
    card.appendChild(head);

    var body = el("div", "panel-body");
    if (p.cv.has_pdf) {
      body.appendChild(JH.link("/download/cv/" + p.cv.stem + ".pdf",
        "Download CV (PDF" + (p.cv.pdf_kb ? " · " + p.cv.pdf_kb + " KB" : "") + ")",
        "btn btn-primary"));
    }
    var alts = el("div", "grow");
    alts.appendChild(JH.link("/download/cv/" + p.cv.stem + ".html", "HTML"));
    alts.appendChild(JH.link("/download/packet/" + p.slug + ".zip", "Everything for " + p.company));
    body.appendChild(alts);

    if (p.cv.pdf_path) {
      body.appendChild(el("p", "pathlabel", "Full path — paste this into any upload box"));
      var pathRow = el("div", "pathrow");
      var code = el("code", null, p.cv.pdf_path);
      code.title = p.cv.pdf_path;
      pathRow.appendChild(code);
      var cp = el("button", "btn btn-sm", "Copy file");
      cp.addEventListener("click", function () { JH.copy(p.cv.pdf_path, "Full path copied"); });
      pathRow.appendChild(cp);
      var cd = el("button", "btn btn-sm", "Copy folder");
      cd.title = "Copy just the folder, to paste into Explorer";
      cd.addEventListener("click", function () { JH.copy(p.cv.pdf_dir, "Folder path copied"); });
      pathRow.appendChild(cd);
      body.appendChild(pathRow);
    }

    if (p.cv.html) {
      var prev = el("div", "cvprev");
      var frame = document.createElement("iframe");
      frame.className = "cvprev-shell";
      frame.setAttribute("title", "CV preview for " + p.company);
      frame.srcdoc = p.cv.html;
      prev.appendChild(frame);
      body.appendChild(prev);
    }
    card.appendChild(body);
    side.appendChild(card);
    side.appendChild(applyPanel(p, r));
    return side;
  }

  function show(id) {
    state.id = id;
    history.replaceState(null, "", "/jobs?id=" + encodeURIComponent(id));
    renderList();

    var r = D.board.filter(function (x) { return x.id === id; })[0];
    var host = $("jobDetail");
    clear(host);
    if (!r) { host.appendChild(el("div", "empty-state", "That role is no longer on the board.")); return; }

    var p = JH.packetFor(r.company);
    host.className = "detail" + (p ? " has-cv" : "");

    var panel = el("div", "panel");
    var head = el("div", "panel-head");
    head.appendChild(el("h3", null, r.job));
    head.appendChild(JH.stageChip(r.stage));
    if (r.warm) head.appendChild(el("span", "chip c-warn", "warm"));
    else if (r.warm_hinted) head.appendChild(el("span", "chip c-mute", "warm in notes"));
    panel.appendChild(head);

    var body = el("div", "panel-body");
    var dl = el("dl", "kvgrid");
    [["company", r.company], ["fit", r.fit == null ? "—" : r.fit + " / 100"],
     ["type", r.work_type || "—"], ["location", r.location || "—"],
     ["found", r.found || "—"], ["applied", r.applied || "not yet"],
     ["next", r.next_action || "—"]].forEach(function (kv) {
      dl.appendChild(el("dt", null, kv[0]));
      dl.appendChild(el("dd", null, String(kv[1])));
    });
    body.appendChild(dl);

    var row = el("div", "grow");
    if (r.url) row.appendChild(JH.link(r.url, "Open the job on LinkedIn ↗", "btn btn-primary"));
    else row.appendChild(el("span", "lede", "No apply link captured for this role."));
    if (p) row.appendChild(JH.link("/download/packet/" + p.slug + ".zip", "Packet .zip"));
    body.appendChild(row);

    body.appendChild(el("h4", null, "Where this stands"));
    body.appendChild(statusControl(r));

    if (r.notes) {
      body.appendChild(el("h4", null, "What we know and how to apply"));
      body.appendChild(el("div", "notes", r.notes));
    }
    if (p) {
      body.appendChild(el("h4", null, "The message that goes with it"));
      body.appendChild(JH.msgBlock(p.docs.touch2 || p.docs.touch1 || "", "Copy message"));
      body.appendChild(JH.link("/research?c=" + p.slug, "Full research for " + p.company + " →"));
    }
    panel.appendChild(body);
    host.appendChild(panel);
    host.appendChild(p ? cvPanel(p, r) : buildPanel(r));
  }

  /* No packet yet: this is the only way to create one from the front-end. */
  function buildPanel(r) {
    var side = el("div", "cvside");
    var card = el("div", "cvcard");
    var head = el("div", "panel-head");
    head.appendChild(el("h3", null, "No CV yet"));
    head.appendChild(el("span", "chip c-mute", "nothing written"));
    card.appendChild(head);

    var body = el("div", "panel-body");
    body.appendChild(el("p", "lede",
      "Nothing has been written for " + r.company + " yet: no tailored CV, no contact, no messages. " +
      "Building the packet researches the company, tailors a CV to this job description, finds the right " +
      "person, drafts both messages and posts a Slack card for you to approve. It sends nothing."));

    var steps = el("ol", "buildsteps");
    ["Read this role and pull the real job description",
     "Tailor the CV and check it against the job's keywords (target ATS 90+)",
     "Find a warm insider first, then a recruiter if there is none",
     "Draft the email and the LinkedIn pitch",
     "Move the role to packet ready and post a Slack card"
    ].forEach(function (s) { steps.appendChild(el("li", null, s)); });
    body.appendChild(steps);

    var run = el("button", "btn btn-primary", "Build the CV + outreach packet");
    var out = el("pre", "console buildout");
    out.hidden = true;
    run.addEventListener("click", function () {
      run.disabled = true;
      run.textContent = "Building… this takes a few minutes";
      out.hidden = false;
      out.textContent = "starting…";
      JH.post("/api/run", { action: "build-packet", confirm: true, param: r.id })
        .then(function (job) { followBuild(job, out, run); })
        .catch(function (e) {
          run.disabled = false;
          run.textContent = "Build the CV + outreach packet";
          out.textContent = "Could not start: " + e.message;
        });
    });
    body.appendChild(run);
    body.appendChild(el("p", "lede",
      "Takes a few minutes and needs no other Claude window open, because it drives the same browser."));
    body.appendChild(out);
    card.appendChild(body);
    side.appendChild(card);
    return side;
  }

  /* Shared by the build and apply buttons: poll the run, stream its log, reload when
     it lands. The wording follows the job so "Built" never appears after an apply. */
  function followBuild(job, out, run, noun) {
    noun = noun || "Packet built";
    var timer = setInterval(function () {
      JH.api("/api/run/" + job.id).then(function (j) {
        out.textContent = (j.lines || []).join("\n") || "working…";
        out.scrollTop = out.scrollHeight;
        if (j.status === "running") return;
        clearInterval(timer);
        run.disabled = false;
        run.textContent = j.status === "done" ? "Done — reload to see it" : "Failed, read the log above";
        if (j.status === "done") {
          JH.toast(noun + ". Reloading…");
          setTimeout(function () { location.reload(); }, 1800);
        }
      }).catch(function () { clearInterval(timer); });
    }, 2000);
  }

  renderList();
  if (state.id) show(state.id);

  $("jobSearch").addEventListener("input", function () {
    state.query = this.value.trim().toLowerCase();
    renderList();
  });
});

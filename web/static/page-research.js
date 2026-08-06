/* Research page: the six rules, the shared Highlight Reel, then per-company dossier + messages. */
JH.ready(function (D) {
  "use strict";
  var el = JH.el, clear = JH.clear, $ = JH.$;
  var current = new URLSearchParams(location.search).get("c");

  var BASIS = [
    ["Step 1 · find", "Only real, fresh openings",
     "Roles come from LinkedIn job search, deduped against the board and scored 0-100 for fit. Anything posted in the last 48 hours is prioritised, because the first wave of applicants is the wave that gets read."],
    ["Step 2 · score", "Fit 85 is the line",
     "At 85 or above a full packet is built automatically: tailored CV, cover letter, recruiter contact, both messages. Below that it waits for a human decision, so effort goes where it converts."],
    ["Step 3 · who", "A warm insider beats a recruiter, every time",
     "Before any cold recruiter we look for someone inside who shares real ground with you: home region, university, mutual connections. That is exactly how the Infosys door opened, via a fellow Kashmiri engineer, second degree, two mutuals."],
    ["Step 4 · proof", "Every claim is verifiable",
     "Messages only use numbers that exist in public repos: 18+ shipped projects, a 7-service private cloud with 98 passing tests, 108 production tools, a 60-95x context reduction. Open-source stats are framed as project-level, never as personal output."],
    ["Step 5 · shape", "Bare request first, pitch second",
     "A connection request with a note is capped at three a month; a message to someone who has accepted is uncapped. So the request goes out empty, and the whole pitch (warm hook, highlight reel, CV link) lands after they accept."],
    ["Step 6 · voice", "Nothing that reads as machine-written",
     "No em-dashes, no markdown asterisks, no unfilled placeholders, no flattery. One researched detail per message that proves the company was actually looked at. A human ticks the check mark before anything sends."]
  ];

  (function basis() {
    var host = $("basis");
    clear(host);
    BASIS.forEach(function (b) {
      var r = el("div", "rule");
      r.appendChild(el("span", "tagline", b[0]));
      r.appendChild(el("h4", null, b[1]));
      r.appendChild(el("p", null, b[2]));
      host.appendChild(r);
    });
  })();

  $("reelDoc").innerHTML = JH.markdown(D.research.highlightReel);

  function render() {
    var tabs = $("researchTabs");
    clear(tabs);
    (D.packets || []).forEach(function (p) {
      var b = el("button", "chipbtn", p.company);
      b.setAttribute("aria-pressed", String(current === p.slug));
      b.addEventListener("click", function () {
        current = p.slug;
        history.replaceState(null, "", "/research?c=" + p.slug);
        render();
      });
      tabs.appendChild(b);
    });

    var host = $("researchBody");
    clear(host);
    if (!current && D.packets.length) current = D.packets[0].slug;
    var p = (D.packets || []).filter(function (x) { return x.slug === current; })[0];
    if (!p) { host.appendChild(el("div", "empty-state", "No packet selected.")); return; }

    var panel = el("div", "panel");
    var head = el("div", "panel-head");
    head.appendChild(el("h3", null, p.company + " · " + p.role));
    head.appendChild(el("span", "chip c-good", "ATS " + p.ats));
    head.appendChild(JH.link("/download/packet/" + p.slug + ".zip", "Download this packet"));
    panel.appendChild(head);

    var body = el("div", "panel-body");
    body.appendChild(el("h4", null, "The research — who to contact and why"));
    var doc = el("div", "doc");
    doc.innerHTML = JH.markdown(p.docs.contact);
    body.appendChild(doc);

    [["touch2", "Message 2 — the LinkedIn pitch, sent after they accept"],
     ["touch1", "Message 1 — the formal email"],
     ["cover", "Cover letter"]].forEach(function (pair) {
      if (!p.docs[pair[0]]) return;
      body.appendChild(el("h4", null, pair[1]));
      body.appendChild(JH.msgBlock(p.docs[pair[0]], "Copy"));
    });

    panel.appendChild(body);
    host.appendChild(panel);
  }
  render();
});

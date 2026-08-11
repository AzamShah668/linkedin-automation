/* Shared by every page: bootstrap fetch, nav, formatting, markdown, small DOM helpers.
   Each page then loads exactly one page-*.js which calls JH.ready(fn). */
window.JH = (function () {
  "use strict";

  var D = null;
  var waiting = [];

  /* ---------------- DOM ---------------- */
  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function clear(node) { while (node && node.firstChild) node.removeChild(node.firstChild); }
  function link(href, text, cls) {
    var a = el("a", cls || "btn btn-sm", text);
    a.href = href;
    if (/^https?:/.test(href)) { a.target = "_blank"; a.rel = "noopener"; }
    return a;
  }
  function toast(msg) {
    var t = $("toast");
    if (!t) return;
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { t.hidden = true; }, 2400);
  }
  function copy(text, msg) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () { toast(msg || "Copied"); },
        function () { toast("Could not copy — select it by hand"); });
    } else { toast("Clipboard unavailable — select it by hand"); }
  }

  /* ---------------- time ---------------- */
  var MS = { m: 60000, h: 3600000, d: 86400000 };
  function span(ms) {
    if (ms < MS.h) return Math.round(ms / MS.m) + " min";
    if (ms < MS.d) {
      var h = Math.floor(ms / MS.h), m = Math.round((ms % MS.h) / MS.m);
      return h + "h" + (m ? " " + m + "m" : "");
    }
    var dd = Math.floor(ms / MS.d), hh = Math.round((ms % MS.d) / MS.h);
    return dd + "d" + (hh ? " " + hh + "h" : "");
  }
  function ago(iso) {
    var t = new Date(iso).getTime();
    if (isNaN(t)) return "";
    var diff = Date.now() - t;
    if (diff < 0) return "in " + span(-diff);
    if (diff < 2 * MS.m) return "just now";
    return span(diff) + " ago";
  }
  function clock(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) return "—";
    return String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0");
  }
  function day(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) return "—";
    return d.toLocaleDateString(undefined, { day: "numeric", month: "short" });
  }

  /* ---------------- markdown (only what this project's docs use) ---------------- */
  function esc(s) { return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function inline(s) {
    return esc(s)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      .replace(/(^|[\s>(])((?:https?:\/\/|www\.)[^\s<)]+)/g, function (m, pre, url) {
        var href = url.indexOf("http") === 0 ? url : "https://" + url;
        return pre + '<a href="' + href + '" target="_blank" rel="noopener">' + url + "</a>";
      });
  }
  function splitRow(line) {
    return line.trim().replace(/^\||\|$/g, "").split("|").map(function (c) { return c.trim(); });
  }
  function markdown(src) {
    if (!src) return '<p class="lede">Nothing written for this yet.</p>';
    var lines = src.replace(/\r/g, "").split("\n"), out = [], i = 0;
    while (i < lines.length) {
      var line = lines[i];
      if (/^```/.test(line)) {
        var buf = []; i++;
        while (i < lines.length && !/^```/.test(lines[i])) { buf.push(lines[i]); i++; }
        i++;
        out.push("<pre><code>" + esc(buf.join("\n")) + "</code></pre>");
        continue;
      }
      if (/^---+\s*$/.test(line)) { out.push("<hr />"); i++; continue; }
      var h = line.match(/^(#{1,4})\s+(.*)$/);
      if (h) {
        var lv = Math.min(h[1].length, 3);
        out.push("<h" + lv + ">" + inline(h[2]) + "</h" + lv + ">");
        i++; continue;
      }
      if (/^\s*\|.*\|\s*$/.test(line) && i + 1 < lines.length && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1])) {
        var head = splitRow(lines[i]); i += 2;
        var body = [];
        while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) { body.push(splitRow(lines[i])); i++; }
        out.push('<div class="tablewrap"><table><thead><tr>' +
          head.map(function (c) { return "<th>" + inline(c) + "</th>"; }).join("") +
          "</tr></thead><tbody>" +
          body.map(function (r) {
            return "<tr>" + r.map(function (c) { return "<td>" + inline(c) + "</td>"; }).join("") + "</tr>";
          }).join("") + "</tbody></table></div>");
        continue;
      }
      if (/^\s*>\s?/.test(line)) {
        var q = [];
        while (i < lines.length && /^\s*>\s?/.test(lines[i])) { q.push(lines[i].replace(/^\s*>\s?/, "")); i++; }
        out.push("<blockquote>" + inline(q.join(" ")) + "</blockquote>");
        continue;
      }
      if (/^\s*[-*]\s+/.test(line)) {
        var items = [];
        while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
          items.push("<li>" + inline(lines[i].replace(/^\s*[-*]\s+/, "")) + "</li>"); i++;
        }
        out.push("<ul>" + items.join("") + "</ul>");
        continue;
      }
      if (!line.trim()) { i++; continue; }
      var para = [];
      while (i < lines.length && lines[i].trim() &&
             !/^(#{1,4}\s|\s*[-*]\s|```|\s*>|\s*\|)/.test(lines[i])) { para.push(lines[i]); i++; }
      out.push("<p>" + inline(para.join(" ")) + "</p>");
    }
    return out.join("\n");
  }

  /* ---------------- slack mrkdwn ---------------- */
  function slackText(raw) {
    var s = esc(raw || "");
    s = s.replace(/:([a-z0-9_+-]+):/g, function (m, n) { return (D && D.emoji && D.emoji[n]) || m; });
    s = s.replace(/&lt;(https?:[^|&]+)\|([^&]+)&gt;/g, '<a href="$1" target="_blank" rel="noopener">$2</a>');
    s = s.replace(/&lt;(https?:[^&]+)&gt;/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    s = s.replace(/\*([^*\n]+)\*/g, "<strong>$1</strong>");
    s = s.replace(/_([^_\n]+)_/g, "<em>$1</em>");
    return s;
  }
  function slackKind(text) {
    if (/Outreach sent|Pitch \+ CV delivered|Knocked on/i.test(text)) return "sent";
    if (/WHO to contact|APPLY HERE/i.test(text)) return "card";
    if (/Update|BLOCKED|paused|expired|logged out/i.test(text)) return "alert";
    return "info";
  }

  /* ---------------- shared bits of UI ---------------- */
  var STAGE_CHIP = {
    delivered: ["c-good", "CV delivered"],
    inflight: ["c-warn", "invite sent"],
    ready: ["c-acc", "packet ready"],
    cold: ["c-mute", "untouched"],
    closed: ["c-mute", "closed"]
  };
  function stageChip(stage) {
    var s = STAGE_CHIP[stage] || STAGE_CHIP.cold;
    return el("span", "chip " + s[0], s[1]);
  }
  function fitCell(fit) {
    var wrap = el("div", "fit");
    wrap.appendChild(el("span", "n", fit == null ? "—" : fit));
    var bar = el("div", "bar");
    var i = document.createElement("i");
    i.style.width = Math.max(0, Math.min(100, fit || 0)) + "%";
    bar.appendChild(i);
    bar.appendChild(document.createElement("u"));
    wrap.appendChild(bar);
    return wrap;
  }
  function star(solid) {
    var s = el("span", "star" + (solid ? "" : " hint"), solid ? "◆" : "◇");
    s.title = solid ? "Marked warm — someone inside"
                    : "Notes mention alumni inside, but the Warm Intro box is not ticked";
    return s;
  }
  function packetFor(company) {
    return (D.packets || []).filter(function (p) { return p.company === company; })[0] || null;
  }
  function msgBlock(text, label) {
    var wrap = el("div", "msgblock");
    var btn = el("button", "btn btn-sm copy", label || "Copy");
    btn.addEventListener("click", function () { copy(text, "Copied"); });
    wrap.appendChild(btn);
    wrap.appendChild(el("pre", "msgtext", text || "(nothing written)"));
    return wrap;
  }

  /* ---------------- nav ---------------- */
  /* Four pages, down from seven (2026-08-11). Removed: the old Board index (its live table
     moved onto the Console), Research (reading files 5-17 days stale, and duplicating Jobs) and
     Slack (a 16-day-old mirror of an app that is already on your phone). */
  var NAV = [
    ["/", "Console"], ["/jobs", "Jobs & CV"],
    ["/downloads", "Downloads"], ["/controls", "Run it"]
  ];
  function renderNav(active) {
    var host = $("nav");
    if (!host) return;
    clear(host);
    NAV.forEach(function (n) {
      var a = el("a", "tab", n[1]);
      a.href = n[0];
      if (n[0] === active) a.setAttribute("aria-current", "page");
      host.appendChild(a);
    });
  }

  /* ---------------- api ---------------- */
  function api(path, opts) {
    return fetch(path, opts).then(function (r) {
      return r.json().then(function (body) {
        if (!r.ok) throw new Error(body && body.error ? body.error : "HTTP " + r.status);
        return body;
      });
    });
  }
  function post(path, payload) {
    return api(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {})
    });
  }

  /* ---------------- boot ---------------- */
  function ready(fn) {
    if (D) { fn(D); return; }
    waiting.push(fn);
  }

  function boot() {
    var active = location.pathname.replace(/\/$/, "") || "/";
    renderNav(active);
    api("/api/bootstrap").then(function (data) {
      D = data;
      // Only stamp pages that do not set their own. The console overwrites this with a per-source
      // freshness strip, because one page-level "synced Xd ago" is true about the last Notion
      // capture and says nothing about the four other sources a page may be showing.
      var sync = (D.stats.last_sync || {}).synced_at;
      var stamp = $("stamp");
      if (stamp && !stamp.dataset.own) {
        stamp.textContent = "board synced " + (sync ? ago(sync) : "—");
      }
      waiting.forEach(function (fn) { fn(D); });
      waiting = [];
    }).catch(function (err) {
      var stamp = $("stamp");
      if (stamp) stamp.textContent = "backend unreachable";
      var main = $("main");
      if (main) {
        main.insertBefore(el("div", "banner",
          "Could not reach the local server (" + err.message +
          "). Start it with: py -3 tools/serve_dashboard.py"), main.firstChild);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", boot);

  return {
    $: $, el: el, clear: clear, link: link, toast: toast, copy: copy,
    ago: ago, span: span, clock: clock, day: day,
    markdown: markdown, slackText: slackText, slackKind: slackKind,
    stageChip: stageChip, fitCell: fitCell, star: star,
    packetFor: packetFor, msgBlock: msgBlock,
    api: api, post: post, ready: ready,
    data: function () { return D; }
  };
})();

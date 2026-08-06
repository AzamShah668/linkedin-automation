/* Slack page: the mirrored channel feed with the reactions that gated each send. */
JH.ready(function (D) {
  "use strict";
  var el = JH.el, clear = JH.clear, $ = JH.$;
  var state = { filter: "all", query: "" };

  function render() {
    var host = $("slackFeed");
    clear(host);
    var msgs = (D.slack || []).filter(function (m) {
      var kind = JH.slackKind(m.text), f = state.filter;
      if (f === "cards" && kind !== "card") return false;
      if (f === "sent" && kind !== "sent") return false;
      if (f === "alerts" && kind !== "alert") return false;
      if (f === "approved" && !(m.reactions || []).some(function (r) {
        return r.name === "white_check_mark";
      })) return false;
      if (state.query && m.text.toLowerCase().indexOf(state.query) === -1) return false;
      return true;
    });
    if (!msgs.length) {
      host.appendChild(el("div", "empty-state", "No Slack messages match that."));
      return;
    }
    msgs.forEach(function (m) {
      var kind = JH.slackKind(m.text);
      var box = el("div", "msg kind-" + kind);
      var head = el("div", "msg-head");
      head.appendChild(el("span", "when",
        JH.day(m.iso) + " " + JH.clock(m.iso) + " · " + JH.ago(m.iso)));
      head.appendChild(el("span", "chip " + (kind === "sent" ? "c-good" :
        kind === "alert" ? "c-warn" : kind === "card" ? "c-acc" : "c-mute"), kind));
      box.appendChild(head);
      var b = el("div", "msg-body");
      b.innerHTML = JH.slackText(m.text);
      box.appendChild(b);
      if ((m.reactions || []).length) {
        var rx = el("div", "rx");
        m.reactions.forEach(function (r) {
          var glyph = (D.emoji && D.emoji[r.name]) || (":" + r.name + ":");
          rx.appendChild(el("span", null, glyph + " " + r.count));
        });
        box.appendChild(rx);
      }
      host.appendChild(box);
    });
  }
  render();

  $("slackFilters").addEventListener("click", function (e) {
    var b = e.target.closest(".chipbtn");
    if (!b) return;
    state.filter = b.dataset.f;
    Array.prototype.forEach.call(this.querySelectorAll(".chipbtn"), function (x) {
      x.setAttribute("aria-pressed", String(x === b));
    });
    render();
  });
  $("slackSearch").addEventListener("input", function () {
    state.query = this.value.trim().toLowerCase();
    render();
  });
});

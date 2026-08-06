/* Downloads page: every artefact the pipeline has produced, with real files behind each button. */
JH.ready(function (D) {
  "use strict";
  var el = JH.el, $ = JH.$;
  var host = $("downloadsBody");

  function section(title, lede) {
    host.appendChild(el("h2", "sec", title));
    if (lede) host.appendChild(el("p", "lede", lede));
    var grid = el("div", "basis");
    host.appendChild(grid);
    return grid;
  }
  function card(grid, name, meta, desc, buttons) {
    var c = el("div", "grab"), t = el("div", "gt");
    t.appendChild(el("span", "gname", name));
    if (meta) t.appendChild(el("span", "gmeta", meta));
    c.appendChild(t);
    if (desc) c.appendChild(el("p", "lede", desc));
    var row = el("div", "grow");
    buttons.forEach(function (b) { row.appendChild(b); });
    c.appendChild(row);
    grid.appendChild(c);
  }

  var g0 = section("Everything at once",
    "One archive with every CV, every message, the highlight reel and the LinkedIn profile pack.");
  card(g0, "job-hunt-everything.zip", "30 files",
    "Use this when you want the lot on a USB stick or another machine.",
    [JH.link("/download/all.zip", "Download", "btn btn-primary")]);

  var g1 = section("Tailored CVs",
    "One per company, rewritten against that job description and scored on its keywords. Upload the PDF when you apply.");
  (D.packets || []).forEach(function (p) {
    var btns = [];
    if (p.cv.has_pdf) btns.push(JH.link("/download/cv/" + p.cv.stem + ".pdf", "PDF", "btn btn-sm btn-primary"));
    btns.push(JH.link("/download/cv/" + p.cv.stem + ".html", "HTML"));
    btns.push(JH.link("/download/packet/" + p.slug + ".zip", "Whole packet"));
    card(g1, p.company, "ATS " + p.ats + (p.cv.pdf_kb ? " · " + p.cv.pdf_kb + " KB" : ""), p.role, btns);
  });

  var g2 = section("General CV",
    "Untailored, and the only CV a recruiter is ever linked to. Keeping the tailored versions private is deliberate: a recruiter should never find a copy written for a different company.");
  var gb = [];
  if (D.generalCv.has_pdf) gb.push(JH.link("/download/cv/" + D.generalCv.stem + ".pdf", "PDF", "btn btn-sm btn-primary"));
  gb.push(JH.link("/download/cv/" + D.generalCv.stem + ".html", "HTML"));
  gb.push(JH.link(D.generalCv.url, "Public link on GitHub"));
  card(g2, "Azam Shah — DevOps CV", "public", "The version linked in every message.", gb);

  var g3 = section("Per-company packets",
    "The CV plus every written message and the research behind it, zipped per company.");
  (D.packets || []).forEach(function (p) {
    var files = Object.keys(p.docs).filter(function (k) { return p.docs[k]; }).length;
    card(g3, p.company, files + " docs + CV",
      "Research, LinkedIn pitch, formal email" + (p.docs.cover ? ", cover letter" : "") + ".",
      [JH.link("/download/packet/" + p.slug + ".zip", "Download .zip", "btn btn-sm btn-primary")]);
  });
});

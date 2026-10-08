#!/usr/bin/env python3
"""Genera la web estática en ./public a partir de ./src.

Uso:  python3 tools/build.py            (web completa)
      python3 tools/build.py --preview  (index.html sin envoltorio, para publicar como vista previa)

Make solo tiene que añadir un archivo .md en src/posts/ con esta cabecera:
---
title: ...
date: AAAA-MM-DD
summary: ...
---
"""
import html, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "src", ROOT / "public"
PREVIEW = "--preview" in sys.argv

cfg = json.loads((SRC / "config.json").read_text(encoding="utf-8"))
data = json.loads((SRC / "data.json").read_text(encoding="utf-8"))
esc = html.escape


def inline(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[(.+?)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', t)
    return t


def md_to_html(text):
    out, para, items, kind = [], [], [], None

    def flush_p():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    def flush_l():
        nonlocal kind
        if items:
            out.append(f"<{kind}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{kind}>")
            items.clear()
            kind = None

    for line in text.splitlines():
        s = line.strip()
        if not s:
            flush_p(); flush_l(); continue
        if s.startswith("## "):
            flush_p(); flush_l(); out.append(f"<h2>{inline(s[3:])}</h2>"); continue
        m = re.match(r"([-*]|\d+\.)\s+(.*)", s)
        if m:
            flush_p()
            k = "ul" if m.group(1) in "-*" else "ol"
            if kind and kind != k:
                flush_l()
            kind = k
            items.append(m.group(2)); continue
        flush_l(); para.append(s)
    flush_p(); flush_l()
    return "\n".join(out)


def parse_post(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
    if not m:
        raise SystemExit(f"Falta la cabecera en {path.name}")
    meta = dict(
        (k.strip(), v.strip()) for k, v in (l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)
    )
    for k in ("title", "date", "summary"):
        if not meta.get(k):
            raise SystemExit(f"Falta '{k}' en {path.name}")
    meta["slug"] = path.stem
    meta["html"] = md_to_html(m.group(2))
    return meta


def fmt_date(d):
    meses = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
    y, mo, da = d.split("-")
    return f"{int(da)} de {meses[int(mo) - 1]} de {y}"


def chip(s):
    return f'<span class="chip {s}">{esc(data["status"][s])}</span>'


def page(rel, title, body, desc, current=""):
    depth = rel.count("/")
    up = "../" * depth
    nav = [("index.html", "Inicio"), ("blog/index.html", "Blog")]
    links = "".join(
        f'<a href="{up}{h}"' + (' aria-current="page"' if h == current else "") + f">{n}</a>" for h, n in nav
    )
    parts = [esc(x) for x in (cfg["titular_nombre"], cfg["titular_nif"], cfg["titular_direccion"]) if x]
    contact = " · ".join(parts + [esc(cfg["contact_email"])])
    robots = "" if cfg["titular_nombre"] else '<meta name="robots" content="noindex,nofollow">'
    inner = f"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Source+Sans+3:wght@400;600;700&display=swap">
<link rel="stylesheet" href="{up}style.css">
<header class="site"><div class="wrap"><a class="brand" href="{up}index.html">{esc(cfg['site_name'])}</a><nav class="main" aria-label="Principal">{links}</nav></div></header>
<div class="draft"><div class="wrap">Borrador interno. Las cifras de esta web están sin contrastar con las ordenanzas oficiales.</div></div>
<main><div class="wrap">{body}</div></main>
<footer class="site"><div class="wrap">
<span>Información orientativa. No sustituye a la ordenanza fiscal de cada ayuntamiento ni a la normativa vigente: consulta siempre la fuente oficial.</span>
<span>Contacto: {contact}</span>
</div></footer>"""
    if PREVIEW and rel == "index.html":
        return f'<title>{esc(title)}</title>\n<meta name="description" content="{esc(desc)}">{robots}' + inner
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">{robots}</head><body>{inner}</body></html>'
    )


def write(rel, content):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copy(SRC / "style.css", OUT / "style.css")
    posts = sorted((parse_post(p) for p in (SRC / "posts").glob("*.md")), key=lambda x: x["date"], reverse=True)

    # Inicio
    def bars(key):
        rows = []
        for m in data["municipios"]:
            pc = m[key].get("pct")
            if pc:
                lo, hi = pc
                label = f"{lo} %" if lo == hi else f"{lo}–{hi} %"
                track = (f'<span class="fill" style="width:{lo}%"></span>'
                         + (f'<span class="rng" style="left:{lo}%;width:{hi - lo}%"></span>' if hi > lo else ""))
            else:
                label, track = "Sin dato", ""
            rows.append(
                f'<li><a href="{m["id"]}.html"><span class="n">{m["name"]}</span>'
                f'<span class="track">{track}</span><span class="v">{label}</span></a></li>'
            )
        return '<ul class="bars">' + "".join(rows) + "</ul>"

    pills = "".join(
        f'<button type="button" class="pill" role="tab" id="t-{m["id"]}" aria-controls="p-{m["id"]}" aria-selected="{"true" if i == 0 else "false"}">{m["name"]}</button>'
        for i, m in enumerate(data["municipios"])
    )
    panels = ""
    for i, m in enumerate(data["municipios"]):
        mini = "".join(
            f'<div class="mini"><span class="lab">{t}</span><span class="big">{esc(c["h"])}</span>{chip(c["s"])}</div>'
            for t, c in (("IBI · cada año", m["ibi"]), ("ICIO · una vez", m["icio"]))
        )
        panels += (f'<div class="qp" role="tabpanel" id="p-{m["id"]}" aria-labelledby="t-{m["id"]}"{"" if i == 0 else " hidden"}>'
                   f'<div class="minis">{mini}</div><a class="more" href="{m["id"]}.html">Ver la ficha de {m["name"]} →</a></div>')
    legend = "".join(chip(s) for s in data["status"])
    recent = "".join(
        f'<li><a href="blog/{p["slug"]}.html"><time datetime="{p["date"]}">{fmt_date(p["date"])}</time>'
        f'<span class="t">{esc(p["title"])}</span></a></li>'
        for p in posts[:3]
    )
    script = """<script>
(function(){
  function tabs(root, btnSel, show){
    var btns = root.querySelectorAll(btnSel);
    btns.forEach(function(b){ b.addEventListener('click', function(){ btns.forEach(function(x){ x.setAttribute('aria-selected', x===b ? 'true':'false'); }); show(b); }); });
  }
  var cmp = document.getElementById('cmp');
  if (cmp) tabs(cmp, '.seg button', function(b){
    cmp.querySelectorAll('.bars-g').forEach(function(u){ u.hidden = u.getAttribute('data-k') !== b.getAttribute('data-k'); });
  });
  var qs = document.getElementById('quick');
  if (qs) tabs(qs, '.pill', function(b){
    qs.querySelectorAll('.qp').forEach(function(p){ p.hidden = p.id !== b.getAttribute('aria-controls'); });
  });
})();
</script>"""
    body = f"""
<div><h1>Ahorro fiscal por placas solares en Andalucía</h1>
<p class="lead">Lo que bonifica cada ayuntamiento en IBI e ICIO, con una etiqueta que dice cuánto nos fiamos de cada dato.</p></div>
<section class="panel" id="cmp"><div class="head"><h2>Compara municipios</h2>
<div class="seg" role="group" aria-label="Impuesto"><button type="button" data-k="ibi" aria-selected="true">IBI</button><button type="button" data-k="icio" aria-selected="false">ICIO</button></div></div>
<div class="bars-wrap"><div data-k="ibi" class="bars-g">{bars("ibi")}</div><div data-k="icio" class="bars-g" hidden>{bars("icio")}</div></div>
<p class="note"><span class="sw fill"></span> mínimo indicado por las fuentes <span class="sw rng"></span> hasta el máximo (fuentes en desacuerdo)</p></section>
<section class="panel" id="quick"><h2>Ficha rápida</h2><div class="pills" role="tablist" aria-label="Municipio">{pills}</div>{panels}</section>
<section class="panel"><h2>Cómo leer las etiquetas</h2><div class="legend">{legend}</div></section>
<section><h2>Últimos artículos</h2><ul class="posts" style="margin-top:12px">{recent}</ul></section>{script}"""
    write("index.html", page("index.html", cfg["site_name"],
        body, "Bonificaciones de IBI e ICIO por placas solares en municipios andaluces.", "index.html"))

    # Fichas
    for m in data["municipios"]:
        cards = [
            ("IBI · cada año", m["ibi"]),
            ("ICIO · una sola vez", m["icio"]),
            ("IRPF · estatal", data["irpf"]),
            ("Subvención directa", data["subv"]),
        ]
        cards_html = "".join(
            f'<div class="card"><span class="lab">{esc(t)}</span><span class="big">{esc(c["h"])}</span>'
            f'<p>{esc(c["d"])}</p>{chip(c["s"])}</div>'
            for t, c in cards
        )
        notes = "".join(f"<li>{esc(n)}</li>" for n in m["notes"])
        body = f"""
<div><p class="crumb"><a href="index.html">Inicio</a> / {m['name']}</p>
<h1>Placas solares en {m['name']}</h1>
<p class="lead">IBI: impuesto anual del inmueble. ICIO: impuesto de la obra, se paga una vez.</p></div>
<section class="cards">{cards_html}</section>
<details class="panel src"><summary>Qué dicen las fuentes consultadas</summary><ul>{notes}</ul></details>"""
        write(f"{m['id']}.html", page(f"{m['id']}.html", f"Placas solares en {m['name']}",
            body, f"Bonificaciones de IBI e ICIO por placas solares en {m['name']}.", ""))

    # Blog
    listing = "".join(
        f'<li><a href="{p["slug"]}.html"><time datetime="{p["date"]}">{fmt_date(p["date"])}</time>'
        f'<span class="t">{esc(p["title"])}</span><span>{esc(p["summary"])}</span></a></li>'
        for p in posts
    )
    write("blog/index.html", page("blog/index.html", "Blog",
        f'<div><h1>Blog</h1><p class="lead">Cambios en ordenanzas, plazos y ayudas para placas solares.</p></div><ul class="posts">{listing}</ul>',
        "Novedades sobre bonificaciones fiscales para placas solares.", "blog/index.html"))
    for p in posts:
        write(f"blog/{p['slug']}.html", page(f"blog/{p['slug']}.html", p["title"],
            f'<article class="post"><div><p class="crumb"><a href="index.html">Blog</a> · <time datetime="{p["date"]}">{fmt_date(p["date"])}</time></p>'
            f'<h1>{esc(p["title"])}</h1></div>{p["html"]}</article>', p["summary"], "blog/index.html"))
    print(f"OK: {len(data['municipios'])} fichas, {len(posts)} artículos -> {OUT}")


if __name__ == "__main__":
    main()

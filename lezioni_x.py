#!/usr/bin/env python3
"""Lezioni → post per X (via Buffer).

Legge la sitemap, trova le lezioni nuove, scarica la GIF di anteprima, la converte in MP4 e prepara il testo del post.
Non pubblica niente: scrive in `uscita/` (testo e titolo della issue) e il video in `video/`.
Uso:  python3 lezioni_x.py            giro normale (la prima volta segna tutto come già visto e si ferma)
      python3 lezioni_x.py --prova    non scrive lo stato: mostra cosa farebbe
"""
import argparse, html, json, os, re, subprocess, sys, urllib.error, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin, urlparse

RADICE = Path(__file__).parent
STATO = RADICE / "stato" / "visti.json"
# Lo script si presenta con il suo nome: chi gestisce il sito può riconoscerlo e autorizzarlo.
# Se il sito vuole anche una chiave, si mette nella variabile d'ambiente LEZIONI_X_CHIAVE (su GitHub: Settings → Secrets) e viaggia nell'intestazione «X-Lezioni-Chiave».
UA = {"User-Agent": os.environ.get("LEZIONI_X_AGENTE", "lezioni-x/1.0")}
if os.environ.get("LEZIONI_X_CHIAVE"): UA["X-Lezioni-Chiave"] = os.environ["LEZIONI_X_CHIAVE"]

def scarica(url, binario=False, limite=60 * 1024 * 1024):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            dati = r.read(limite + 1)
    except urllib.error.HTTPError as e:
        sys.exit(f"Il sito ha risposto {e.code} a {url}.\n" + ("Il sito rifiuta le richieste automatiche: serve che chi lo gestisce autorizzi «" + UA["User-Agent"] + "» (vedi LEGGIMI.md)." if e.code in (401, 403) else "Controlla l'indirizzo."))
    if len(dati) > limite: raise ValueError(f"file troppo grande: {url}")
    return dati if binario else dati.decode("utf-8", "replace")

def indirizzi_sitemap(url, profondita=0):
    radice = ET.fromstring(scarica(url, binario=True))
    voci = [e.text.strip() for e in radice.iter() if e.tag.endswith("}loc") and e.text]
    if radice.tag.endswith("sitemapindex") and profondita < 2:      # una sitemap di sitemap: si scende
        return [u for v in voci for u in indirizzi_sitemap(v, profondita + 1)]
    return voci

def meta(pagina, nome):
    for m in re.finditer(r"<meta\b[^>]*>", pagina, re.I):
        t = m.group(0)
        if re.search(r'(?:property|name)\s*=\s*["\']%s["\']' % re.escape(nome), t, re.I):
            c = re.search(r'content\s*=\s*["\']([^"\']*)["\']', t, re.I)
            if c: return html.unescape(c.group(1)).strip()
    return ""

def leggi_pagina(url):
    p = scarica(url)
    titolo = meta(p, "og:title") or (re.search(r"<h1[^>]*>(.*?)</h1>", p, re.I | re.S) or re.search(r"<title>(.*?)</title>", p, re.I | re.S)).group(1)
    titolo = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", titolo))).strip()
    gif = next((urljoin(url, g) for g in re.findall(r'["\(\s]([^"\'()\s]+\.gif)(?:\?[^"\'()\s]*)?', p, re.I)), "")
    gif = gif or meta(p, "og:image")
    return {"url": url, "titolo": titolo, "descrizione": meta(p, "og:description") or meta(p, "description"), "gif": urljoin(url, gif) if gif else ""}

def componi_testo(l, cfg):
    tag = " ".join(cfg.get("hashtag", []))
    fisso = f"\n\n{cfg.get('frase_finale', '').strip()} {l['url']}\n\n{tag}".strip()
    spazio = 280 - (len(fisso) - len(l["url"]) + 23)             # su X ogni indirizzo conta 23 caratteri
    t = l["titolo"]
    if len(t) > spazio: t = t[: max(spazio - 1, 0)].rstrip() + "…"
    return f"{t}\n\n{cfg.get('frase_finale', '').strip()} {l['url']}\n\n{tag}".strip()

def converti(gif_bytes, destinazione, tetto_mb):
    tmp = destinazione.with_suffix(".gif"); tmp.write_bytes(gif_bytes)
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-movflags", "+faststart", "-pix_fmt", "yuv420p",
                        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-crf", "26", "-an", str(destinazione)], check=True)
    finally: tmp.unlink(missing_ok=True)
    mb = destinazione.stat().st_size / 1024 / 1024
    if mb > tetto_mb: print(f"  attenzione: l'MP4 pesa {mb:.1f} MB, oltre il tetto di {tetto_mb} MB", file=sys.stderr)
    return mb

def nome_sicuro(url):
    # l'ultimo pezzo dell'indirizzo (lo «slug») è unico per ogni video; si tiene l'inizio, non la fine
    pezzi = [x for x in urlparse(url).path.split("/") if x]
    return re.sub(r"[^a-z0-9]+", "-", (pezzi[-1] if pezzi else "").lower()).strip("-")[:100] or "lezione"

def link_video(nome):
    repo = os.environ.get("GITHUB_REPOSITORY")                    # su GitHub Actions: «utente/repository»
    if repo: return f"https://github.com/{repo}/raw/main/video/{nome}.mp4"   # scarica il file direttamente
    return f"`video/{nome}.mp4`"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--prova", action="store_true"); ap.add_argument("--config", default=str(RADICE / "config.json"))
    a = ap.parse_args(); cfg = json.loads(Path(a.config).read_text())
    if "INSERISCI" in cfg["sitemap_url"] or "INSERISCI" in cfg["filtro_lezioni"]:
        sys.exit("Compila prima config.json: indirizzo della sitemap e filtro delle lezioni.")
    tutte = [u for u in indirizzi_sitemap(cfg["sitemap_url"]) if cfg["filtro_lezioni"] in u]
    if not tutte: sys.exit("Nessuna lezione trovata nella sitemap: controlla sitemap_url e filtro_lezioni.")
    visti = set(json.loads(STATO.read_text())) if STATO.exists() else None
    if visti is None:
        print(f"Prima esecuzione: {len(tutte)} lezioni segnate come già viste, nessun post preparato.")
        if not a.prova: STATO.write_text(json.dumps(sorted(tutte), indent=1)); 
        return
    nuove = [u for u in tutte if u not in visti][: cfg.get("max_nuove_per_giro", 5)]
    print(f"{len(tutte)} lezioni in sitemap, {len(nuove)} nuove.")
    (RADICE / "uscita").mkdir(exist_ok=True)
    for u in nuove:
        print("→", u)
        try:
            l = leggi_pagina(u); testo = componi_testo(l, cfg); nome = nome_sicuro(u); mp4 = RADICE / "video" / f"{nome}.mp4"; avviso = ""
            if l["gif"]:
                tetto = cfg.get("peso_massimo_mb_mp4", 15)
                mb = converti(scarica(l["gif"], binario=True, limite=60 * 1024 * 1024), mp4, tetto); print(f"  MP4 {mb:.1f} MB")
                if mb > tetto: avviso = f"\n\n⚠️ L'MP4 pesa {mb:.1f} MB, oltre il limite di {tetto} MB di Buffer: va ridotto prima di caricarlo."
            else: avviso = "\n\n⚠️ Non ho trovato la GIF di anteprima in questa pagina: il video va aggiunto a mano."
            (RADICE / "uscita" / f"{nome}.titolo.txt").write_text(f"Nuova lezione: {l['titolo']}"[:200])
            (RADICE / "uscita" / f"{nome}.md").write_text(
                f"Testo del post (copialo in Buffer):\n\n```\n{testo}\n```\n\nVideo: {link_video(nome)}{avviso}\n\nPagina: {u}\n")
            print("  testo:", testo.replace("\n", " | "))
            visti.add(u)
        except Exception as e:
            print(f"  ERRORE su {u}: {e}", file=sys.stderr)     # resta non vista: si riprova al giro dopo
    if not a.prova: STATO.write_text(json.dumps(sorted(visti), indent=1))

if __name__ == "__main__": main()

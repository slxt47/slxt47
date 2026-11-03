#!/usr/bin/env python3
"""Erzeugt die Diagramme fürs GitHub-Profil (hell + dunkel) als statische SVGs in assets/.
Nur Standardbibliothek. Token aus GITHUB_TOKEN (GitHub Action) oder GH_TOKEN. Zählt nur öffentliche Repos ohne Forks.
Design wie slxt.org: ein Farbton (Violett), keine Palette nötig, Text in Textfarben, Raster zurückhaltend."""
import json, os, urllib.request, datetime, html
from collections import Counter, OrderedDict

NUTZER = os.environ.get("PROFIL", "slxt47")
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
THEMEN = {
    "hell":   {"text": "#1f2328", "leise": "#59636e", "linie": "#d1d9e0", "akzent": "#5b3df5", "flaeche": "#f6f4fe", "rand": "#e4defc"},
    "dunkel": {"text": "#e6edf3", "leise": "#9198a1", "linie": "#30363d", "akzent": "#a993ff", "flaeche": "#161233", "rand": "#2c2557"},
}
SCHRIFT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONATE = ["Jän", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

def graphql(q):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": q}).encode(),
                                 headers={"Authorization": f"bearer {token}", "User-Agent": "slxt47-profil"})
    antwort = json.load(urllib.request.urlopen(req, timeout=30))
    if "errors" in antwort: raise SystemExit(antwort["errors"])
    return antwort["data"]

def daten():
    d = graphql('query{user(login:"%s"){createdAt repositories(ownerAffiliations:OWNER,first:100,isFork:false,privacy:PUBLIC){totalCount nodes{stargazerCount languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}} contributionsCollection{totalCommitContributions contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}' % NUTZER)["user"]
    sprachen = Counter()
    for r in d["repositories"]["nodes"]:
        for e in r["languages"]["edges"]: sprachen[e["node"]["name"]] += e["size"]
    monate = OrderedDict()
    heute = datetime.date.today()
    for i in range(11, -1, -1):  # letzte 12 Monate, ältester zuerst
        j, m = heute.year, heute.month - i
        while m <= 0: m += 12; j -= 1
        monate[(j, m)] = 0
    for w in d["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for t in w["contributionDays"]:
            dt = datetime.date.fromisoformat(t["date"])
            if (dt.year, dt.month) in monate: monate[(dt.year, dt.month)] += t["contributionCount"]
    return {
        "repos": d["repositories"]["totalCount"],
        "sterne": sum(r["stargazerCount"] for r in d["repositories"]["nodes"]),
        "commits": d["contributionsCollection"]["totalCommitContributions"],
        "beitraege": d["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "seit": d["createdAt"][:4],
        "sprachen": sprachen, "monate": monate,
    }

def svg(b, h, inhalt, titel):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{b}" height="{h}" viewBox="0 0 {b} {h}" role="img" aria-label="{html.escape(titel)}">'
            f'<title>{html.escape(titel)}</title><style>text{{font-family:{SCHRIFT}}}</style>{inhalt}</svg>\n')

def kacheln(x, f):
    werte = [(str(x["repos"]), "öffentliche Repos"), (str(x["commits"]), "Commits · 12 Monate"),
             (str(len(x["sprachen"])), "Sprachen"), (x["seit"], "auf GitHub seit")]
    b, h, gap = 200, 92, 12
    teile = []
    for i, (wert, text) in enumerate(werte):
        px = i * (b + gap)
        teile.append(f'<rect x="{px+1}" y="1" width="{b-2}" height="{h-2}" rx="18" fill="{f["flaeche"]}" stroke="{f["rand"]}"/>'
                     f'<text x="{px+20}" y="50" font-size="30" font-weight="800" fill="{f["text"]}" letter-spacing="-0.5">{html.escape(wert)}</text>'
                     f'<text x="{px+20}" y="74" font-size="13" fill="{f["leise"]}">{html.escape(text)}</text>')
    return svg(4 * b + 3 * gap, h, "".join(teile), "Kennzahlen: " + ", ".join(f"{w} {t}" for w, t in werte))

def commits(x, f):
    B, H, L, R_, O, U = 848, 230, 36, 8, 42, 30
    monate = list(x["monate"].items())
    hoechst = max([v for _, v in monate] + [1])
    stufe = next(s for s in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 10**9) if s * 4 >= hoechst)  # runde Achsenschritte
    oben = stufe * 4
    breit = (B - L - R_) / len(monate); balken = min(34, breit - 14)
    teile = [f'<text x="0" y="18" font-size="15" font-weight="700" fill="{f["text"]}">Beiträge pro Monat</text>',
             f'<text x="{B}" y="18" font-size="13" fill="{f["leise"]}" text-anchor="end">letzte 12 Monate · {x["beitraege"]} insgesamt</text>']
    for k in range(5):  # Raster + y-Achse (0, ¼, ½, ¾, oben)
        y = H - U - (H - U - O) * k / 4
        teile.append(f'<line x1="{L}" x2="{B-R_}" y1="{y:.1f}" y2="{y:.1f}" stroke="{f["linie"]}" stroke-width="1"/>'
                     f'<text x="{L-8}" y="{y+4:.1f}" font-size="11" fill="{f["leise"]}" text-anchor="end">{stufe*k}</text>')
    letzter = len(monate) - 1
    imax = max(range(len(monate)), key=lambda i: monate[i][1])
    for i, ((j, m), v) in enumerate(monate):
        cx = L + breit * i + breit / 2
        hh = (H - U - O) * v / oben
        y0 = H - U
        if v:
            r = min(4, hh / 2, balken / 2)  # runde Datenkante oben, unten am Boden anliegend
            pfad = (f'M{cx-balken/2:.1f},{y0} V{y0-hh+r:.1f} Q{cx-balken/2:.1f},{y0-hh:.1f} {cx-balken/2+r:.1f},{y0-hh:.1f} '
                    f'H{cx+balken/2-r:.1f} Q{cx+balken/2:.1f},{y0-hh:.1f} {cx+balken/2:.1f},{y0-hh+r:.1f} V{y0} Z')
            teile.append(f'<path d="{pfad}" fill="{f["akzent"]}"><title>{MONATE[m-1]} {j}: {v} Beiträge</title></path>')
        if i in (imax, letzter) and v:  # nur ausgewählte Werte direkt beschriften
            teile.append(f'<text x="{cx:.1f}" y="{y0-hh-7:.1f}" font-size="12" font-weight="700" fill="{f["text"]}" text-anchor="middle">{v}</text>')
        teile.append(f'<text x="{cx:.1f}" y="{H-10}" font-size="11" fill="{f["leise"]}" text-anchor="middle">{MONATE[m-1]}</text>')
    beschr = "; ".join(f"{MONATE[m-1]} {j}: {v}" for (j, m), v in monate)
    return svg(B, H, "".join(teile), "Beiträge pro Monat, letzte 12 Monate – " + beschr)

def sprachen(x, f):
    gesamt = sum(x["sprachen"].values()) or 1
    top = x["sprachen"].most_common(6)
    rest = gesamt - sum(v for _, v in top)
    zeilen = top + ([("Andere", rest)] if rest > 0 else [])
    B, Z = 848, 30
    H = 40 + Z * len(zeilen)
    L, Rr = 110, 64
    teile = [f'<text x="0" y="18" font-size="15" font-weight="700" fill="{f["text"]}">Sprachen</text>',
             f'<text x="{B}" y="18" font-size="13" fill="{f["leise"]}" text-anchor="end">Anteil am Code aller öffentlichen Repos</text>']
    for i, (name, v) in enumerate(zeilen):
        y = 40 + Z * i
        anteil = v / gesamt
        w = max(4, (B - L - Rr) * anteil / (zeilen[0][1] / gesamt))
        teile.append(f'<text x="0" y="{y+14}" font-size="13" fill="{f["text"]}">{html.escape(name)}</text>'
                     f'<rect x="{L}" y="{y+3}" width="{B-L-Rr}" height="14" rx="7" fill="{f["flaeche"]}"/>'
                     f'<rect x="{L}" y="{y+3}" width="{w:.1f}" height="14" rx="7" fill="{f["akzent"]}" fill-opacity="{1 if name != "Andere" else .45}"><title>{html.escape(name)}: {anteil*100:.1f} %</title></rect>'
                     f'<text x="{B}" y="{y+14}" font-size="13" font-weight="700" fill="{f["text"]}" text-anchor="end">{anteil*100:.1f} %</text>')
    return svg(B, H, "".join(teile), "Sprachen: " + ", ".join(f"{n} {v/gesamt*100:.1f} %" for n, v in zeilen))

if __name__ == "__main__":
    x = daten()
    os.makedirs(OUT, exist_ok=True)
    for modus, f in THEMEN.items():
        for name, fn in (("kennzahlen", kacheln), ("beitraege", commits), ("sprachen", sprachen)):
            with open(os.path.join(OUT, f"{name}-{modus}.svg"), "w") as h: h.write(fn(x, f))
    print("ok", x["repos"], x["commits"], dict(x["monate"]))

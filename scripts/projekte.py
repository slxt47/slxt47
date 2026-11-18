#!/usr/bin/env python3
"""Schreibt die Projekt-Tabelle im README neu (zwischen <!-- PROJEKTE:START --> und <!-- PROJEKTE:END -->).

Quelle: alle öffentlichen, eigenen Repos (keine Forks, nicht archiviert, mit Beschreibung) über die GitHub-API,
das zuletzt geänderte zuerst. Symbol, Kurztext und Doku-Link aus scripts/projekte.json. Nur Standardbibliothek.
Token aus GITHUB_TOKEN (GitHub Action) oder GH_TOKEN; ohne Token geht es auch (öffentliche API, Rate-Limit).
"""
import json, os, re, urllib.request

NUTZER = os.environ.get("PROFIL", "slxt47")
HIER = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(HIER, "..", "README.md")


def repos():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    kopf = {"User-Agent": "slxt47-profil", "Accept": "application/vnd.github+json"}
    if token:
        kopf["Authorization"] = f"bearer {token}"
    url = f"https://api.github.com/users/{NUTZER}/repos?type=owner&per_page=100&sort=pushed"
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=kopf), timeout=30))


def zelle(text):
    return text.replace("|", "\\|").replace("\n", " ").strip()


def tabelle(alle, cfg):
    weg = set(cfg.get("ausblenden", []))
    eigen = cfg.get("repos", {})
    zeilen = []
    for r in sorted(alle, key=lambda r: r["pushed_at"], reverse=True):
        if r["fork"] or r["archived"] or r["private"] or r["name"] in weg:
            continue
        e = eigen.get(r["name"], {})
        text = e.get("text") or (r["description"] or "").strip()
        if not text:
            continue
        if not e.get("text") and r.get("language"):
            text += f" – {r['language']}"
        links = []
        if r.get("homepage"):
            links.append(f"[live]({r['homepage']})")
        if e.get("mehr"):
            links.append(f"[mehr]({e['mehr']})")
        zeilen.append(f"| {e.get('symbol', '📦')} | **[{r['name']}]({r['html_url']})** | {zelle(text)}"
                      f"{' · ' + ' · '.join(links) if links else ''} |")
        if len(zeilen) >= cfg.get("anzahl", 12):
            break
    return "\n".join(["| | Projekt | Worum es geht |", "|---|---|---|", *zeilen])


def main():
    cfg = json.load(open(os.path.join(HIER, "projekte.json"), encoding="utf-8"))
    neu = tabelle(repos(), cfg)
    s = open(README, encoding="utf-8").read()
    if "<!-- PROJEKTE:START -->" not in s or "<!-- PROJEKTE:END -->" not in s:
        raise SystemExit("Markierungen fehlen im README")
    s2 = re.sub(r"<!-- PROJEKTE:START -->.*?<!-- PROJEKTE:END -->",
                lambda m: "<!-- PROJEKTE:START -->\n" + neu + "\n<!-- PROJEKTE:END -->", s, flags=re.S)
    open(README, "w", encoding="utf-8").write(s2)
    print(neu)


if __name__ == "__main__":
    main()

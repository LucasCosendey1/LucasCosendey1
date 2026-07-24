import os
import json
import requests
from datetime import datetime

USERNAME = "LucasCosendey1"
API_BASE = f"https://api.github.com/users/{USERNAME}"

def fetch(url):
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()

def get_stats():
    user  = fetch(API_BASE)
    # type=source exclui forks completamente
    repos = fetch(f"{API_BASE}/repos?per_page=100&type=source")

    stars      = sum(r.get("stargazers_count", 0) for r in repos)
    lang_bytes = {}

    for repo in repos:
        # dupla proteção: ignora forks e repos arquivados
        if repo.get("fork") or repo.get("archived"):
            continue
        name = repo["name"]
        try:
            langs = fetch(f"https://api.github.com/repos/{USERNAME}/{name}/languages")
            for lang, b in langs.items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + b
        except Exception:
            pass

    total_bytes   = sum(lang_bytes.values()) or 1
    top_langs_raw = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:5]
    top_langs     = [(l, round(b / total_bytes * 100, 1)) for l, b in top_langs_raw]

    return {
        "followers":    user.get("followers", 0),
        "public_repos": user.get("public_repos", 0),
        "stars":        stars,
        "top_langs":    top_langs,
        "updated":      datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"),
    }

LANG_COLORS = {
    "Python":           "#3572A5",
    "JavaScript":       "#f1e05a",
    "TypeScript":       "#3178c6",
    "HTML":             "#e34c26",
    "CSS":              "#563d7c",
    "Jupyter Notebook": "#DA5B0B",
    "PHP":              "#4F5D95",
    "Shell":            "#89e051",
    "Java":             "#b07219",
    "C":                "#555555",
    "C++":              "#f34b7d",
}
DEFAULT_COLOR = "#8f8f8f"

def make_svg(stats):
    langs      = stats["top_langs"]
    total_pct  = sum(p for _, p in langs) or 1
    bar_width  = 460
    W, H       = 500, 310

    lang_bars = lang_labels = ""
    x = 0
    for i, (lang, pct) in enumerate(langs):
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        w     = round(bar_width * pct / total_pct)
        lang_bars += (
            f'<rect x="{20+x}" y="200" width="{w}" height="12" rx="3" fill="{color}"/>'
        )
        col, row = i % 3, i // 3
        lx, ly   = 20 + col * 155, 228 + row * 22
        lang_labels += (
            f'<circle cx="{lx+6}" cy="{ly}" r="5" fill="{color}"/>'
            f'<text x="{lx+16}" y="{ly+4}" font-size="12" fill="#ccc">{lang} {pct}%</text>'
        )
        x += w

    return f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}"
     xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI',Arial,sans-serif">
  <rect width="{W}" height="{H}" rx="12" fill="#0d1117"/>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" fill="none" stroke="#F5A623" stroke-width="1.5"/>
  <text x="20" y="38" font-size="16" font-weight="700" fill="#F5A623">GitHub Stats</text>
  <text x="{W-20}" y="38" font-size="11" fill="#555" text-anchor="end">{stats["updated"]}</text>
  <line x1="20" y1="50" x2="{W-20}" y2="50" stroke="#1e1e1e" stroke-width="1"/>
  <text x="20"  y="90" font-size="22" font-weight="700" fill="#fff">{stats["public_repos"]}</text>
  <text x="20"  y="108" font-size="11" fill="#888">Public Repos</text>
  <text x="160" y="90" font-size="22" font-weight="700" fill="#fff">{stats["stars"]}</text>
  <text x="160" y="108" font-size="11" fill="#888">Total Stars</text>
  <text x="300" y="90" font-size="22" font-weight="700" fill="#fff">{stats["followers"]}</text>
  <text x="300" y="108" font-size="11" fill="#888">Followers</text>
  <line x1="20" y1="130" x2="{W-20}" y2="130" stroke="#1e1e1e" stroke-width="1"/>
  <text x="20" y="158" font-size="13" font-weight="600" fill="#F5A623">Top Languages</text>
  <rect x="20" y="168" width="{bar_width}" height="12" rx="3" fill="#1e1e1e"/>
  {lang_bars}
  {lang_labels}
</svg>"""

if __name__ == "__main__":
    print("Buscando dados do GitHub...")
    stats = get_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    svg = make_svg(stats)
    with open("github-stats.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("✅ github-stats.svg gerado!")

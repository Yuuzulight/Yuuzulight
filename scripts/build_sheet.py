"""Generate the profile's SVG art: the character sheet and the section headers,
each in a day (light mode) and a night (dark mode) version.

Edit the data below, then run:  python scripts/build_sheet.py
Every derived number (modifiers, saves, skills, HP, spell DC) is computed here
from 5e rules, so changing a score or the level keeps the sheet consistent.
"""
import json
import math
import os
import random
import re
import urllib.request
from html import escape
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# ---------------------------------------------------------------- data
GH = "https://github.com/Yuuzulight/"
# Crafted items, one level per project. Rarity comes from the live commit count
# (the stored "commits" is only a fallback when GitHub can't be reached), unless
# "rarity" overrides it. "map" puts a finished project on the road, in that order.
PROJECTS = [
    dict(name="Mana", commits=1489, type="Companion", stack="C# · JS · llama.cpp · Live2D",
         lines=["Windows AI companion with a Live2D avatar. Speech-to-text,", "LLM, TTS and screen awareness all run on your own PC."]),
    dict(name="Hecate", commits=176, type="Scrying instrument", stack="Python · dbt · Kubernetes", map=2,
         lines=["Repo intelligence", "across ecosystems"]),
    dict(name="Folio", commits=87, type="Forged tool", stack="C# · SkiaSharp", map=5,
         lines=["HTML/CSS engine", "for .NET"]),
    dict(name="Hephastion", commits=51, type="Companion", stack="Python · Hermes plugin", map=4,
         lines=["Obsidian vault", "as AI memory"]),
    dict(name="Argos", commits=38, type="Forged tool", stack="C++ · Direct2D", map=3,
         lines=["Win32 / Direct2D widget", "engine, zero deps"]),
    dict(name="Veritarach", commits=32, type="Scrying instrument", stack="Python · PyTorch", map=1,
         lines=["DeBERTa AI-text", "detector, served live"]),
    dict(name="Rozetta", commits=15, type="Companion", stack="Python",
         lines=["MCP server for YouTube transcripts and stats"]),
    dict(name="Veracia", commits=12, type="Scrying instrument", stack="Python",
         lines=["Evaluation harness for trustworthy ML output"]),
    dict(name="Wisp", commits=6, type="Companion", stack="Python",
         lines=["Cited answers on top of SearXNG"]),
    dict(name="db-artisan", commits=6, type="Forged tool", stack="Agent skills",
         lines=["Agent skills for schemas and data pipelines"]),
]
RARITIES = [(500, "LEGENDARY"), (200, "VERY RARE"), (50, "RARE"), (25, "UNCOMMON"), (0, "COMMON")]
PIPS = {"COMMON": 1, "UNCOMMON": 1, "RARE": 2, "VERY RARE": 3, "LEGENDARY": 4}


def live_commits(name):
    """Commit count on the default branch, read from the API's last-page link."""
    req = urllib.request.Request(f"https://api.github.com/repos/Yuuzulight/{name}/commits?per_page=1",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-sheet"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=20) as r:
        last = re.search(r'[?&]page=(\d+)>; rel="last"', r.headers.get("Link", ""))
        return int(last.group(1)) if last else len(json.load(r))


def refresh_commits():
    for p in PROJECTS:
        try:
            p["commits"] = live_commits(p["name"])
        except OSError as e:  # offline or rate-limited: keep the stored count
            print(f"warning: using stored commit count for {p['name']} ({e})")


def rarity(p):
    return p.get("rarity") or next(r for n, r in RARITIES if p["commits"] >= n)


NUMBERS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen".split()
LEVEL = len(PROJECTS)
ROAD = [p["name"] for p in sorted((p for p in PROJECTS if "map" in p), key=lambda p: p["map"])]

NAME = "YUUZULIGHT"
TAGLINE = [f"Level {LEVEL} Artificer who tinkers with local-first AI,", "native Windows tools and data & ML."]
FIELDS = [  # (value, label), one slim row
    (f"Artificer {LEVEL}", "CLASS & LEVEL"), ("Cartographer", "SUBCLASS"),
    ("Solo Developer", "BACKGROUND"), ("Neutral Good", "ALIGNMENT"),
]
HIT_DIE = 8
AC, SPEED = 17, "30 ft"  # half plate: 15 + DEX (max 2)
ABILITIES = [  # rolled, not point-buy; caption = what the stat means for a developer
    ("STR", 13, "low-level grit"), ("DEX", 16, "clean UI craft"), ("CON", 14, "ships offline"),
    ("INT", 17, "ML & data"), ("WIS", 15, "knows where data goes"), ("CHA", 12, "gives tools a face"),
]
SAVE_PROFS = {"CON", "INT"}  # artificer saving throws
SPELL_ABILITY = "INT"
SKILLS = [  # (name, ability, proficient, flavour)
    ("Arcana", "INT", True, "local LLMs"),
    ("Investigation", "INT", True, "debugging"),
    ("Sleight of Hand", "DEX", True, "Win32, Direct2D"),
    ("Insight", "WIS", True, "model evals"),
    ("Stealth", "DEX", False, "zero telemetry"),
    ("Perception", "WIS", False, "screen awareness"),
]
FEATURES = [
    ("Homunculus Servant: Mana", "A companion construct with a voice and a face."),
    ("Infuse Item: Local-first", "Every tool runs on your own machine."),
    ("Tool Expertise", "C++, C#, Python and TypeScript."),
    ("Flash of Genius", f"{(NUMBERS[LEVEL] if LEVEL < len(NUMBERS) else str(LEVEL)).capitalize()} public projects, each built solo."),
]
IDEAL = ["A personal AI of my own, running on my own PC."]
FLAW = ["Starts a new quest before", "finishing the last one."]
HEADERS = {"crafted-items": "CRAFTED ITEMS", "quest-board": "QUEST BOARD", "equipment": "EQUIPMENT"}
QUESTS = [  # (title lines, objective lines, reward lines, link)
    (["Summon a", "companion"], ["Set up Mana", "on your PC."], ["A companion that", "talks back."],
     GH + "Mana/blob/main/docs/quick_start_windows.md"),
    (["Browse the", "armory"], ["Look through every", "repository."], ["A new tool", "for your pack."],
     "https://github.com/Yuuzulight?tab=repositories"),
    (["Consult the", "atlas"], ["Explore the", "portfolio."], ["Every project,", "with write-ups."], "https://yuuzulight.github.io"),
]
EQUIPMENT = [
    ("WEAPONS", ["C++", "C# / .NET", "Python", "TypeScript"]),
    ("ARMOR & TOOLS", ["Half plate (Docker)", "Kubernetes", "dbt", "PyTorch"]),
    ("PACK", ["Tinker's tools (VS Code)", "llama.cpp", "whisper.cpp", "Live2D", "SkiaSharp", "Direct2D"]),
]
# Mana's crystal, from her character design: a slender faceted shard in violet-blue
CRYSTAL = dict(light="#d3def6", base="#98b1e0", dark="#7189c9", deep="#566ba8", glow="#a9d8ff")

# ---------------------------------------------------------------- 5e rules
def mod(score):
    return (score - 10) // 2


def signed(n):
    return f"{n:+d}"


PROF = 2 + (LEVEL - 1) // 4
MODS = {a: mod(s) for a, s, _ in ABILITIES}
HP = HIT_DIE + MODS["CON"] + (LEVEL - 1) * (HIT_DIE // 2 + 1 + MODS["CON"])
SAVES = {a: MODS[a] + (PROF if a in SAVE_PROFS else 0) for a, _, _ in ABILITIES}
SKILL_BONUS = [(n, a, p, f, MODS[a] + (PROF if p else 0)) for n, a, p, f in SKILLS]
PASSIVE_PERCEPTION = 10 + next(b for n, _, _, _, b in SKILL_BONUS if n == "Perception")
SPELL_DC = 8 + PROF + MODS[SPELL_ABILITY]
SPELL_ATTACK = PROF + MODS[SPELL_ABILITY]

# ---------------------------------------------------------------- themes
# Purple base, pink blossoms and lantern, cyan only on the wisps.
RIBBON = ("#8d6ee2", "#7c5bd6", "#5f41b8")  # amethyst on both sheets
THEMES = {
    "day": dict(
        paper=("#f6f0ff", "#ece2ff", "#e0d2fb"), ink="#3a2a5e", ink_soft="#4f4270", label="#8a74c8",
        gloss="#7d66b8", lilac="#b9a2f0", line="#cdb9f5", panel="#ffffff", panel_op=".6", oval="#ffffff",
        accent="#7c5bd6", trail="#5f41b8", grain="#3a2a5e", grain_op=1, vignette=("#7c5bd6", ".14"),
        moon=("#fdfbff", "1"), moon_halo=("#d9c8fb", ".75"), moon_rim="#c3adf2", crater="#e6dbfb", legendary="#c24f8c", blossom="#f4a9cf", branch="#8a6fd0",
        lantern=("#f7dbe9", "#e3b3cf"), lantern_glow=("#f7b3d6", ".3"), wisp=("#8fe3dc", ".7"), wisp_core="#ffffff"),
    "night": dict(
        paper=("#2a2358", "#211b48", "#171233"), ink="#f1eaff", ink_soft="#d9ccf7", label="#a997e8",
        gloss="#b9a6f0", lilac="#7a66c0", line="#4d4190", panel="#2e2760", panel_op=".55", oval="#1c1740",
        accent="#b59cf6", trail="#cdb9f5", grain="#e9dcff", grain_op=.5, vignette=("#07051a", ".45"),
        moon=("#efe6ff", "1"), moon_halo=("#f4ecff", ".45"), moon_rim="#efe6ff", crater="#ddd0f7", legendary="#f7b3d6", blossom="#f7b3d6", branch="#a58be6",
        lantern=("#f2c6e0", "#f7b3d6"), lantern_glow=("#f7b3d6", ".75"), wisp=("#9ff0ec", ".95"), wisp_core="#e9fffd"),
}
SERIF = "Georgia, 'Palatino Linotype', 'Book Antiqua', 'Times New Roman', serif"


def css(c):
    return f"""
  .label {{ font: 14px {SERIF}; letter-spacing: 2px; fill: {c['label']}; }}
  .value {{ font: 20px {SERIF}; fill: {c['ink']}; }}
  .tag {{ font: italic 34px {SERIF}; fill: {c['ink']}; }}
  .big {{ font: bold 36px {SERIF}; fill: {c['ink']}; }}
  .body {{ font: 17px {SERIF}; fill: {c['ink_soft']}; }}
  .save {{ font: 15px {SERIF}; fill: {c['ink_soft']}; }}
  .head {{ font: bold 17px {SERIF}; fill: {c['ink']}; }}
  .stop {{ font: bold 15px {SERIF}; fill: {c['ink']}; }}
  .gloss {{ font: italic 15px {SERIF}; fill: {c['gloss']}; }}
  .num {{ font: bold 17px {SERIF}; fill: {c['ink']}; }}
  .panel {{ fill: {c['panel']}; fill-opacity: {c['panel_op']}; stroke: {c['line']}; stroke-width: 1.4; }}
  .rule {{ stroke: {c['line']}; }}
  .petal {{ animation: drift linear infinite; }}
  @keyframes drift {{ from {{ transform: translate(-60px, -700px) rotate(0deg) }} to {{ transform: translate(60px, 700px) rotate(300deg) }} }}
  .wisp {{ animation: breathe 4s ease-in-out infinite; }}
  @keyframes breathe {{ 0%, 100% {{ opacity: .35 }} 50% {{ opacity: 1 }} }}
  @media (prefers-reduced-motion: reduce) {{ .petal, .wisp {{ animation: none }} }}
"""


def t(x, y, text, cls, anchor="start", extra=""):
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"{extra}>{escape(text)}</text>'


def torn_path(rnd, w, h, m=10):
    """Paper outline: long slow wobbles plus small fibres, not a uniform zigzag."""
    pts = []
    sides = [((m, m), (w - m, m)), ((w - m, m), (w - m, h - m)),
             ((w - m, h - m), (m, h - m)), ((m, h - m), (m, m))]
    for (x0, y0), (x1, y1) in sides:
        length = math.hypot(x1 - x0, y1 - y0)
        p1, p2 = rnd.uniform(0, 6.3), rnd.uniform(0, 6.3)
        for i in range(int(length // 6)):
            d = i * 6
            off = 3.5 * math.sin(d / 140 * 6.3 + p1) + 2 * math.sin(d / 45 * 6.3 + p2) + rnd.uniform(-1.2, 1.2)
            x, y = x0 + (x1 - x0) * d / length, y0 + (y1 - y0) * d / length
            if y0 == y1:
                y += off
            else:
                x += off
            pts.append(f"{x:.1f} {y:.1f}")
    return "M" + " L".join(pts) + " Z"


def grain_pattern(rnd, c):
    """Paper grain as a tile of tiny dots: cheap to paint, unlike a full-size noise filter."""
    dots = "".join(
        f'<circle cx="{rnd.uniform(0, 120):.1f}" cy="{rnd.uniform(0, 120):.1f}" r="{rnd.uniform(.4, 1.1):.2f}" '
        f'fill-opacity="{rnd.uniform(.08, .22) * c["grain_op"]:.2f}"/>' for _ in range(110))
    return f'<pattern id="grain" width="120" height="120" patternUnits="userSpaceOnUse"><g fill="{c["grain"]}">{dots}</g></pattern>'


def smooth(pts):
    """Catmull-Rom curve through every point, as cubic Beziers."""
    d = f"M{pts[0][0]} {pts[0][1]}"
    for i in range(len(pts) - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def blossom(x, y, r, c):
    petals = "".join(f'<ellipse rx="{r * .55:.1f}" ry="{r:.1f}" transform="rotate({a}) translate(0 {-r:.1f})"/>' for a in range(0, 360, 72))
    return (f'<g transform="translate({x} {y})" fill="{c["blossom"]}">{petals}'
            f'<circle r="{r * .38:.1f}" fill="#fff3b0"/></g>')


def branch(c, lantern=False):
    """Blossom branch drawn for the top-left corner; mirror it with a transform."""
    out = [f'<path d="M0 0 C 40 6 70 18 104 44 M40 7 C 44 -6 56 -12 70 -10 M70 20 C 76 34 74 48 66 60" '
           f'fill="none" stroke="{c["branch"]}" stroke-width="3" stroke-linecap="round"/>']
    out += [blossom(x, y, r, c) for x, y, r in [(104, 44, 8), (70, -10, 7), (66, 60, 7), (30, 4, 6), (88, 30, 5)]]
    if lantern:
        gc, go = c["lantern_glow"]
        body, trim = c["lantern"]
        out += [f'<line x1="58" y1="16" x2="58" y2="70" stroke="{c["branch"]}" stroke-width="1.4"/>',
                f'<circle cx="58" cy="96" r="46" fill="url(#lanternGlow)"/>',
                f'<rect x="42" y="72" width="32" height="46" rx="13" fill="{body}" stroke="{trim}" stroke-width="1.5"/>',
                f'<path d="M46 86 H70 M46 104 H70" stroke="{trim}" stroke-width="1.2"/>',
                f'<rect x="47" y="68" width="22" height="6" rx="2" fill="{RIBBON[2]}"/>',
                f'<rect x="47" y="116" width="22" height="6" rx="2" fill="{RIBBON[2]}"/>',
                f'<path d="M58 122 V134" stroke="{RIBBON[2]}" stroke-width="2" stroke-linecap="round"/>']
    return "".join(out)


# ---------------------------------------------------------------- sheet
def sheet(theme):
    c = THEMES[theme]
    rnd = random.Random(7)
    W, H, MY = 1000, 1290, 1060  # MY = top of the map panel
    torn = torn_path(rnd, W, H)
    xs = [50 + i * 152.4 for i in range(6)]
    out = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
           f'<title>{NAME.title()}: {escape(FIELDS[0][0])} ({escape(FIELDS[1][0])}), {escape(FIELDS[3][0])}</title>',
           f'<defs><style>{css(c)}</style>',
           f'<linearGradient id="paperFill" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["paper"][0]}"/>'
           f'<stop offset=".55" stop-color="{c["paper"][1]}"/><stop offset="1" stop-color="{c["paper"][2]}"/></linearGradient>',
           f'<radialGradient id="vignette" cx=".5" cy=".5" r=".75"><stop offset=".7" stop-color="{c["vignette"][0]}" stop-opacity="0"/>'
           f'<stop offset="1" stop-color="{c["vignette"][0]}" stop-opacity="{c["vignette"][1]}"/></radialGradient>',
           f'<radialGradient id="moonHalo"><stop offset="0" stop-color="{c["moon_halo"][0]}" stop-opacity="{c["moon_halo"][1]}"/>'
           f'<stop offset="1" stop-color="{c["moon_halo"][0]}" stop-opacity="0"/></radialGradient>',
           f'<radialGradient id="lanternGlow"><stop offset="0" stop-color="{c["lantern_glow"][0]}" stop-opacity="{c["lantern_glow"][1]}"/>'
           f'<stop offset="1" stop-color="{c["lantern_glow"][0]}" stop-opacity="0"/></radialGradient>',
           f'<radialGradient id="wispGlow"><stop offset="0" stop-color="{c["wisp"][0]}" stop-opacity="{c["wisp"][1]}"/>'
           f'<stop offset="1" stop-color="{c["wisp"][0]}" stop-opacity="0"/></radialGradient>',
           f'<linearGradient id="ribbon" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{RIBBON[0]}"/><stop offset="1" stop-color="{RIBBON[1]}"/></linearGradient>',
           f'<path id="petal" d="M0 0 C5 -8 13 -5 10 3 C8 9 1 8 0 0 Z" fill="{c["blossom"]}"/>',
           grain_pattern(rnd, c), f'<clipPath id="paper"><path d="{torn}"/></clipPath>', '</defs>',
           '<g clip-path="url(#paper)">',
           f'<rect width="{W}" height="{H}" fill="url(#paperFill)"/>',
           f'<rect width="{W}" height="{H}" fill="url(#grain)"/>',
           f'<rect width="{W}" height="{H}" fill="url(#vignette)"/>',
           # moon behind the ribbon: faint by day, full at night
           f'<circle cx="500" cy="60" r="130" fill="url(#moonHalo)"/>',
           f'<circle cx="500" cy="60" r="56" fill="{c["moon"][0]}" fill-opacity="{c["moon"][1]}" stroke="{c["moon_rim"]}" stroke-width="2"/>',
           f'<g fill="{c["crater"]}"><circle cx="478" cy="30" r="9"/><circle cx="522" cy="22" r="6"/><circle cx="534" cy="44" r="5"/></g>',
           '</g>',
           f'<path d="{torn}" fill="none" stroke="{c["lilac"]}" stroke-width="1.4"/>',
           f'<rect x="28" y="28" width="{W - 56}" height="{H - 56}" rx="6" fill="none" stroke="{c["lilac"]}" stroke-opacity=".8"/>',
           f'<g transform="translate(34 34)">{branch(c)}</g>',
           f'<g transform="translate({W - 34} 34) scale(-1 1)">{branch(c, lantern=True)}</g>',
           # bottom-left: the bottom-right corner belongs to the map's main quest and compass
           f'<g transform="translate(34 {H - 34}) scale(.7 -.7)">{branch(c)}</g>']

    # header: centred ribbon, seal on the right tail, tagline, slim fields row
    out += [f'<path d="M166 82 H252 V162 H166 L190 122 Z" fill="{RIBBON[2]}"/>',
            f'<path d="M834 82 H748 V162 H834 L810 122 Z" fill="{RIBBON[2]}"/>',
            '<path d="M226 150 L252 162 V150 Z M774 150 L748 162 V150 Z" fill="#3d2a80" opacity=".6"/>',
            '<path d="M226 62 Q500 48 774 62 V150 Q500 136 226 150 Z" fill="url(#ribbon)"/>',
            '<path d="M226 62 Q500 48 774 62 V150 Q500 136 226 150 Z" fill="url(#grain)" opacity=".5"/>',
            '<path d="M226 70 Q500 56 774 70 M226 142 Q500 128 774 142" fill="none" stroke="#e9dcff" stroke-opacity=".6"/>',
            '<path id="nameArc" d="M262 124 Q500 106 738 124" fill="none"/>',
            f'<text font-family="{escape(SERIF)}" font-size="56" font-weight="bold" fill="#fdfbff" text-anchor="middle">'
            f'<textPath href="#nameArc" startOffset="50%" textLength="420" lengthAdjust="spacingAndGlyphs">{NAME}</textPath></text>']
    seal = "M" + " L".join(
        f"{(31 if i % 2 else 26) * math.cos(i * math.pi / 18):.1f} {(31 if i % 2 else 26) * math.sin(i * math.pi / 18):.1f}"
        for i in range(36)) + " Z"
    out += [f'<g transform="translate(836 164)"><path d="{seal}" fill="{RIBBON[2]}" stroke="{RIBBON[2]}" stroke-width="3" stroke-linejoin="round"/>',
            '<circle r="19" fill="none" stroke="#c9b3f5" stroke-width="1.5"/>',
            '<path d="M-13 -12 A 18 18 0 0 1 8 -17" fill="none" stroke="#efe7ff" stroke-opacity=".6" stroke-width="2" stroke-linecap="round"/>',
            f'<text y="8" text-anchor="middle" font-family="{escape(SERIF)}" font-size="22" font-weight="bold" fill="#efe7ff">Y</text></g>']
    out += [t(500, 208 + 42 * i, line, "tag", "middle") for i, line in enumerate(TAGLINE)]
    out.append('<rect x="50" y="276" width="900" height="64" rx="8" class="panel"/>')
    for i, (value, label) in enumerate(FIELDS):
        cx = 162.5 + i * 225
        if i:
            out.append(f'<path d="M{50 + i * 225} 288 V328" class="rule"/>')
        out += [t(cx, 305, value, "value", "middle"), t(cx, 327, label, "label", "middle")]

    # ability scores, with saving throws folded in as on the official sheet
    out.append(t(50, 370, "ABILITY SCORES", "label") + t(950, 370, "rolled, not point-buy", "gloss", "end"))
    for x, (abbr, score, caption) in zip(xs, ABILITIES):
        cx = x + 69
        prof = abbr in SAVE_PROFS
        out += [f'<rect x="{x:.1f}" y="382" width="138" height="134" rx="10" class="panel"/>',
                t(cx, 406, abbr, "label", "middle"), t(cx, 448, signed(MODS[abbr]), "big", "middle"),
                f'<ellipse cx="{cx:.1f}" cy="470" rx="22" ry="12" fill="{c["oval"]}" stroke="{c["lilac"]}"/>',
                t(cx, 475, str(score), "body", "middle"),
                f'<circle cx="{cx - 34:.1f}" cy="498" r="5" fill="{c["accent"] if prof else "none"}" stroke="{c["accent"]}" stroke-width="1.5"/>',
                t(cx + 6, 503, f"save {signed(SAVES[abbr])}", "save", "middle"),
                t(cx, 540, caption, "gloss", "middle")]

    # combat strip
    combat = [("ARMOR CLASS", str(AC), "half plate"), ("INITIATIVE", signed(MODS["DEX"]), ""),
              ("SPEED", SPEED, ""), ("HIT POINTS", str(HP), f"{LEVEL}d{HIT_DIE} hit dice"),
              ("PROFICIENCY", signed(PROF), ""), ("SPELL SAVE DC", str(SPELL_DC), f"spell attack {signed(SPELL_ATTACK)}")]
    for x, (label, big, sub) in zip(xs, combat):
        cx = x + 69
        shape = (f'<path d="M{x:.1f} 564 H{x + 138:.1f} V618 Q{x + 138:.1f} 652 {cx:.1f} 666 Q{x:.1f} 652 {x:.1f} 618 Z" class="panel"/>'
                 if label == "ARMOR CLASS" else f'<rect x="{x:.1f}" y="564" width="138" height="100" rx="10" class="panel"/>')
        out += [shape, t(cx, 586, label, "label", "middle"), t(cx, 628, big, "big", "middle")]
        if sub:
            out.append(t(cx, 652, sub, "gloss", "middle"))

    # skills (left) and features (right)
    out += ['<rect x="50" y="684" width="430" height="266" rx="10" class="panel"/>', t(70, 708, "SKILLS", "label"),
            t(460, 708, "● proficient", "gloss", "end")]
    for i, (name, abbr, prof, flavour, bonus) in enumerate(SKILL_BONUS):
        y = 740 + i * 30
        out += [f'<circle cx="76" cy="{y - 6}" r="6" fill="{c["accent"] if prof else "none"}" stroke="{c["accent"]}" stroke-width="1.5"/>',
                t(90, y, signed(bonus), "num"),
                f'<text x="126" y="{y}" class="body">{escape(name)} <tspan class="gloss">· {escape(flavour)}</tspan></text>']
    out += [f'<rect x="70" y="904" width="390" height="34" rx="17" fill="{c["oval"]}" fill-opacity=".7" stroke="{c["line"]}"/>',
            t(90, 927, str(PASSIVE_PERCEPTION), "num"), t(126, 927, "PASSIVE PERCEPTION", "label")]
    out += ['<rect x="510" y="684" width="440" height="266" rx="10" class="panel"/>', t(530, 708, "FEATURES & TRAITS", "label")]
    for i, (head, body) in enumerate(FEATURES):
        y = 744 + i * 54
        out += [t(530, y, head, "head"), t(530, y + 22, body, "body")]

    # ideal & flaw, under skills
    out += ['<rect x="50" y="966" width="900" height="78" rx="10" class="panel"/>', t(70, 990, "IDEAL", "label"), t(510, 990, "FLAW", "label")]
    out += [t(70, 1014 + 20 * i, line, "body") for i, line in enumerate(IDEAL)]
    out += [t(510, 1014 + 20 * i, line, "body") for i, line in enumerate(FLAW)]

    # map: the road so far, one stop per finished project in completion order
    out += [f'<rect x="50" y="{MY}" width="900" height="200" rx="10" class="panel"/>', t(70, MY + 24, "THE ROAD SO FAR", "label")]
    out.append(f'<g fill="none" stroke="{c["lilac"]}" stroke-opacity=".35">'
               + "".join(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx - k * 16}" ry="{ry - k * 7}" transform="rotate({rot} {cx} {cy})"/>'
                         for cx, cy, rx, ry, rot in [(300, MY + 118, 64, 20, -6), (600, MY + 116, 58, 18, 5)] for k in range(3))
               + '</g>')
    stops = ([(150, MY + 116)] + [(240 + i * 490 / (len(ROAD) - 1), MY + (84 if i % 2 == 0 else 146)) for i in range(len(ROAD))]
             + [(812, MY + 124)])
    out.append(f'<path d="{smooth(stops)}" fill="none" stroke="{c["trail"]}" stroke-width="3" stroke-linecap="round" stroke-dasharray="2 9"/>')
    for i, (x, y) in enumerate(stops[:-1]):  # wisps breathe in turn along the trail
        out.append(f'<circle class="wisp" cx="{x:.1f}" cy="{y}" r="22" fill="url(#wispGlow)" style="animation-delay:{-i * .8:.1f}s"/>')
    x, y = stops[0]
    out += [f'<circle cx="{x}" cy="{y}" r="6" fill="{c["wisp_core"]}" stroke="{c["trail"]}" stroke-width="2"/>',
            t(x, y + 32, "Set out", "stop", "middle")]
    for (x, y), name in zip(stops[1:-1], ROAD):
        above = y < MY + 114
        out += [f'<circle cx="{x:.1f}" cy="{y}" r="6" fill="{c["wisp_core"]}" stroke="{c["trail"]}" stroke-width="2"/>',
                t(round(x, 1), y - 22 if above else y + 34, name, "stop", "middle")]
    qx, qy = stops[-1]
    out += [f'<path d="M{qx - 12} {qy - 12} L{qx + 12} {qy + 12} M{qx + 12} {qy - 12} L{qx - 12} {qy + 12}" stroke="{c["accent"]}" stroke-width="5" stroke-linecap="round"/>',
            t(qx, qy + 38, "MAIN QUEST: MANA", "label", "middle"), t(qx, qy + 55, "in progress", "gloss", "middle")]
    star = lambda r, w: " ".join(f"M0 0 L{r * math.cos(a):.1f} {r * math.sin(a):.1f} L{w * math.cos(a + .5):.1f} {w * math.sin(a + .5):.1f} Z"
                                 for a in [k * math.pi / 2 - math.pi / 2 for k in range(4)])
    out += [f'<g transform="translate(900 {MY + 98})">',
            f'<circle r="44" fill="{c["panel"]}" fill-opacity=".6" stroke="{c["lilac"]}"/>',
            f'<circle r="37" fill="none" stroke="{c["lilac"]}" stroke-dasharray="1 4"/>',
            f'<g transform="rotate(45)"><path d="{star(24, 6)}" fill="{c["line"]}"/></g>',
            f'<path d="{star(34, 8)}" fill="{c["accent"]}"/>',
            f'<circle r="4" fill="{c["wisp_core"]}"/>',
            t(0, -50, "N", "head", "middle"), '</g>']

    # drifting petals; with reduced motion they rest where they are placed
    out.append('<g clip-path="url(#paper)">')
    for i in range(10):
        # rest in the side margins, so a still frame (or reduced motion) never covers text
        x, y = (rnd.uniform(16, 40) if i % 2 else rnd.uniform(960, 984)), 200 + i * 95 + rnd.uniform(-30, 30)
        out.append(f'<g transform="translate({x:.0f} {y:.0f}) scale({rnd.uniform(.8, 1.3):.2f})">'
                   f'<use href="#petal" class="petal" style="animation-duration:{rnd.uniform(18, 30):.1f}s;animation-delay:{-rnd.uniform(0, 30):.1f}s"/></g>')
    out += ['</g>', '</svg>']
    return "\n".join(out)


# ---------------------------------------------------------------- section headers
def header(title, theme):
    c = THEMES[theme]
    W, H = 1000, 72
    pw = len(title) * 21 + 90  # plaque width sized to the lettering
    x0 = (W - pw) / 2
    plaque = f'M{x0:.0f} 12 H{x0 + pw:.0f} L{x0 + pw + 14:.0f} 36 L{x0 + pw:.0f} 60 H{x0:.0f} L{x0 - 14:.0f} 36 Z'
    line = "#b9a2f0"  # the same lilac on both, visible on GitHub's light and dark pages
    return "\n".join([
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
        f'<title>{escape(title.title())}</title>',
        f'<defs><linearGradient id="p" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["paper"][0]}"/>'
        f'<stop offset="1" stop-color="{c["paper"][2]}"/></linearGradient>{grain_pattern(random.Random(7), c)}</defs>',
        f'<path d="M72 36 H{x0 - 22:.0f} M{x0 + pw + 22:.0f} 36 H{W - 72}" stroke="{line}" stroke-width="1.6"/>',
        f'<path d="M48 36 L60 28 L72 36 L60 44 Z M{W - 72} 36 L{W - 60} 28 L{W - 48} 36 L{W - 60} 44 Z" fill="{line}"/>',
        f'<path d="{plaque}" fill="url(#p)" stroke="{line}" stroke-width="1.6"/>',
        f'<path d="{plaque}" fill="url(#grain)"/>',
        f'<text x="{W / 2}" y="45" text-anchor="middle" font-family="{escape(SERIF)}" font-size="26" font-weight="bold" letter-spacing="5" fill="{c["ink"]}"'
        f' textLength="{pw - 70}" lengthAdjust="spacingAndGlyphs">{escape(title)}</text>',
        '</svg>'])


# ---------------------------------------------------------------- lower-half cards
# Shown side by side at a percentage width, so the type is large enough to stay
# readable when a phone shrinks a card to a third of its size.
CARD_CSS = """
  .rar {{ font: bold 22px {serif}; letter-spacing: 3px; }}
  .nm {{ font: bold 40px {serif}; fill: {ink}; }}
  .ds {{ font: 28px {serif}; fill: {soft}; }}
  .st {{ font: italic 24px {serif}; fill: {gloss}; }}
  .lb {{ font: 18px {serif}; letter-spacing: 3px; fill: {label}; }}
  .tl {{ font: bold 32px {serif}; fill: {ink}; }}
  .eq {{ font: 30px {serif}; fill: {soft}; }}
"""
TIER_GLOW = {"day": "#b59cf6", "night": "#c9b3f5"}  # pearl glow for Very Rare


def tier_frame(w, h, tier, c, theme):
    """Border ornament escalates with rarity: single, double, double + glow, pink + glow."""
    rect = lambda inset, **a: (f'<rect x="{inset}" y="{inset}" width="{w - 2 * inset}" height="{h - 2 * inset}" rx="{max(4, 16 - inset // 3)}" fill="none" '
                               + " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in a.items()) + "/>")
    glow_colour = {"VERY RARE": TIER_GLOW[theme], "LEGENDARY": c["legendary"]}.get(tier)
    out = []
    if glow_colour:
        out += [rect(12, stroke=glow_colour, stroke_width=sw, stroke_opacity=op) for sw, op in ((18, .10), (11, .16), (5, .28))]
    border = {"LEGENDARY": (c["legendary"], 3), "VERY RARE": (c["line"], 2.5), "RARE": (c["accent"], 2.5)}.get(tier, (c["lilac"], 2))
    out.append(rect(12, stroke=border[0], stroke_width=border[1]))
    if tier in ("RARE", "VERY RARE", "LEGENDARY"):
        out.append(rect(20, stroke=c["accent"] if tier != "RARE" else c["line"], stroke_width=1.3))
    return "".join(out)


def panel_svg(w, h, theme, body, title, tilt=0, extra_defs="", tier="COMMON"):
    c = THEMES[theme]
    shape = f'<rect x="12" y="12" width="{w - 24}" height="{h - 24}" rx="12"/>'
    style = CARD_CSS.format(serif=SERIF, ink=c["ink"], soft=c["ink_soft"], gloss=c["gloss"], label=c["label"])
    return "\n".join([
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">',
        f'<title>{escape(title)}</title>',
        f'<defs><style>{style}</style>',
        f'<linearGradient id="pf" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["paper"][0]}"/><stop offset="1" stop-color="{c["paper"][2]}"/></linearGradient>',
        grain_pattern(random.Random(w * 7 + h), c), extra_defs, '</defs>',
        f'<g transform="rotate({tilt} {w / 2} {h / 2})">',
        f'<g fill="url(#pf)">{shape}</g>', f'<g fill="url(#grain)">{shape}</g>',
        tier_frame(w, h, tier, c, theme), body, '</g>', '</svg>'])


def rarity_colour(r, c):
    return {"LEGENDARY": c["legendary"], "VERY RARE": c["ink"], "RARE": c["accent"]}.get(r, c["gloss"])


def rarity_label(x, y, r, c, text=None):
    """Gem pips, then the tier name: the pips can be counted at a glance."""
    col = rarity_colour(r, c)
    pips = "".join(f'<path d="M{x + 7 + 18 * i} {y - 15} l7 7 -7 7 -7 -7 Z" fill="{"none" if r == "COMMON" else col}" stroke="{col}" stroke-width="1.6"/>'
                   for i in range(PIPS[r]))
    return pips + t(x + 18 * PIPS[r] + 8, y, text or r, "rar", extra=f' fill="{col}"')


def item_card(p, theme, wide=False):
    c = THEMES[theme]
    r = rarity(p)
    w, h = (500, 300) if wide else (330, 300)
    body = [rarity_label(34, 60, r, c), t(34, 114, p["name"], "nm")]
    body += [t(34, 166 + 36 * i, line, "ds") for i, line in enumerate(p["lines"])]
    tight = len(p["stack"]) > (30 if wide else 20)  # keep long stack lines clear of the border
    body.append(t(34, 262, p["stack"], "st", extra=' style="font-size:21px"' if tight else ""))
    return panel_svg(w, h, theme, "".join(body), f'{p["name"]}: {r.title()} {p["type"].lower()}', tier=r)


def common_chip(p, theme):
    c = THEMES[theme]
    body = rarity_label(30, 50, "COMMON", c) + t(30, 94, p["name"], "nm", extra=' style="font-size:32px"')
    return panel_svg(250, 120, theme, body, f'{p["name"]}: Common {p["type"].lower()}')


def crystal(cx, cy, s=1.0):
    """Mana's crystal: a slender faceted violet-blue shard, lit from the upper left."""
    k = CRYSTAL
    P = dict(T=(0, -92), UR=(20, -40), R=(24, 22), B=(0, 94), L=(-22, 26), UL=(-18, -44), C1=(3, -30), C2=(-2, 32))
    face = lambda names, col: f'<path d="M{" L".join(f"{P[n][0]} {P[n][1]}" for n in names)} Z" fill="{col}"/>'
    return (f'<g transform="translate({cx} {cy}) rotate(-10) scale({s})">'
            + face(["T", "UL", "C1"], k["light"]) + face(["T", "C1", "UR"], k["base"])
            + face(["UL", "L", "C2", "C1"], k["base"]) + face(["C1", "UR", "R", "C2"], k["dark"])
            + face(["L", "B", "C2"], k["dark"]) + face(["C2", "B", "R"], k["deep"])
            + '<path d="M-8 -62 L-3 -40" stroke="#ffffff" stroke-opacity=".8" stroke-width="3" stroke-linecap="round"/>'
            + "</g>")


def legendary_banner(p, theme):
    c = THEMES[theme]
    glow = (f'<radialGradient id="halo"><stop offset="0" stop-color="{CRYSTAL["glow"]}" stop-opacity=".7"/>'
            f'<stop offset="1" stop-color="{CRYSTAL["glow"]}" stop-opacity="0"/></radialGradient>')
    body = ['<circle cx="872" cy="146" r="140" fill="url(#halo)"/>', crystal(872, 146, 1.3),
            "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{CRYSTAL["glow"]}" fill-opacity=".8"/>' for x, y, r in ((798, 84, 3), (944, 222, 2.5), (936, 70, 2))),
            rarity_label(44, 66, "LEGENDARY", c, "LEGENDARY · BEING CRAFTED · MAIN QUEST"),
            f'<text x="44" y="136" font-family="{escape(SERIF)}" font-size="64" font-weight="bold" fill="{c["ink"]}">{escape(p["name"])}</text>']
    body += [f'<text x="44" y="{184 + 36 * i}" font-family="{escape(SERIF)}" font-size="28" fill="{c["ink_soft"]}">{escape(line)}</text>'
             for i, line in enumerate(p["lines"])]
    body += [t(44, 260, p["stack"], "st"), blossom(956, 46, 11, c), blossom(928, 34, 7, c), blossom(958, 76, 6, c)]
    return panel_svg(1000, 290, theme, "".join(body), f'{p["name"]}: legendary companion, being crafted, the main quest',
                     extra_defs=glow, tier="LEGENDARY")


NOTE_PAPER = {"day": ("#fcfaff", "#d9c8fb"), "night": ("#ebe2fb", "#b9a2f0")}  # (paper, edge and fold)


def quest_note(q, theme, tilt):
    """A pale paper notice: torn top edge, folded bottom-right corner, pinned."""
    paper, edge = NOTE_PAPER[theme]
    title, objective, reward, _ = q
    rnd = random.Random(len(title[0]) * 31 + len(reward[0]))
    w, h = 330, 400
    top = " ".join(f"L{x} {20 + rnd.uniform(-4, 4):.1f}" for x in range(20, w - 19, 10))
    outline = f"M20 20 {top} L{w - 20} {h - 60} L{w - 60} {h - 20} L20 {h - 20} Z"
    fold = f"M{w - 20} {h - 60} L{w - 60} {h - 20} L{w - 54} {h - 54} Z"
    ink, soft, label = "#3a2a5e", "#4f4270", "#8a74c8"  # plum ink on paper in both modes
    body = [f'<path d="{outline}" fill="{paper}" stroke="{edge}" stroke-width="2"/>',
            f'<path d="{fold}" fill="{edge}"/>',
            f'<circle cx="165" cy="44" r="10" fill="{THEMES[theme]["blossom"]}"/><circle cx="162" cy="41" r="3" fill="#fff" fill-opacity=".7"/>']
    body += [f'<text x="40" y="{96 + 36 * i}" font-family="{escape(SERIF)}" font-size="32" font-weight="bold" fill="{ink}">{escape(line)}</text>'
             for i, line in enumerate(title)]
    for y, head, lines in ((182, "OBJECTIVE", objective), (298, "REWARD", reward)):
        body.append(f'<text x="40" y="{y}" font-family="{escape(SERIF)}" font-size="18" letter-spacing="3" fill="{label}">{head}</text>')
        body += [f'<text x="40" y="{y + 34 + 32 * i}" font-family="{escape(SERIF)}" font-size="28" fill="{soft}">{escape(line)}</text>'
                 for i, line in enumerate(lines)]
    return "\n".join([
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">',
        f'<title>Quest: {escape(" ".join(title))}</title>',
        f'<g transform="rotate({tilt} {w / 2} {h / 2})">', *body, '</g>', '</svg>'])


def equipment_panel(theme):
    c = THEMES[theme]
    body = []
    for x, (label, items) in zip((54, 290, 600), EQUIPMENT):
        body.append(t(x, 68, label, "lb"))
        for k, item in enumerate(items):
            name, _, note = item.partition(" (")
            extra = f' <tspan font-style="italic" font-size="24" fill="{c["gloss"]}">({escape(note)}</tspan>' if note else ""
            body.append(f'<text x="{x}" y="{120 + 44 * k}" class="eq">{escape(name)}{extra}</text>')
    return panel_svg(1000, 400, theme, "".join(body), "Equipment: " + ", ".join(i for _, items in EQUIPMENT for i in items))


def picture(name, alt, width):
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-night.svg" />'
            f'<img src="assets/{name}-day.svg" width="{width}" alt="{escape(alt)}" /></picture>')


def readme_block():
    """The generated part of README.md, between the items markers."""
    tiers = {r: [p for p in PROJECTS if rarity(p) == r] for _, r in RARITIES}

    def card(p, width):
        alt = f'{p["name"]}: {rarity(p).title()} {p["type"].lower()}'
        if rarity(p) == "LEGENDARY":
            alt += ", being crafted, the main quest"
        return f'  <a href="{GH}{p["name"]}">{picture("item-" + p["name"].lower(), alt, width)}</a>'

    def rows(items, per_row, width):
        out = []
        for i in range(0, len(items), per_row):
            out += ['<p align="center">'] + [card(p, width) for p in items[i:i + per_row]] + ["</p>", ""]
        return out

    out = ['<p align="center">', "  " + picture("header-crafted-items", "Crafted items", "100%"), "</p>", ""]
    out += rows(tiers["LEGENDARY"], 1, "100%")
    out += rows(tiers["VERY RARE"] + tiers["RARE"], 3, "32%")
    out += rows(tiers["UNCOMMON"], 2, "48.5%")
    out += rows(tiers["COMMON"], 4, "23.5%")
    out += ['<p align="center">', "  " + picture("header-quest-board", "Quest board", "100%"), "</p>", "", '<p align="center">']
    out += [f'  <a href="{q[3]}">{picture(f"quest-{i + 1}", "Quest: " + " ".join(q[0]), "32%")}</a>' for i, q in enumerate(QUESTS)]
    out += ["</p>", "", '<p align="center">', "  " + picture("header-equipment", "Equipment", "100%"), "</p>", "",
            '<p align="center">', "  " + picture("equipment", "Equipment: " + ", ".join(i for _, items in EQUIPMENT for i in items), "100%"), "</p>"]
    return "\n".join(out)


def write_readme():
    path = ASSETS.parent / "README.md"
    text = path.read_text(encoding="utf-8")
    start, end = "<!-- items:start -->", "<!-- items:end -->"
    assert start in text and end in text, "README.md needs the items markers"
    head, rest = text.split(start, 1)
    path.write_text(head + start + "\n" + readme_block() + "\n" + end + rest.split(end, 1)[1], encoding="utf-8")


def check():
    assert [mod(s) for s in (8, 9, 10, 11, 17)] == [-1, -1, 0, 0, 3]
    assert (PROF, SPELL_DC, SPELL_ATTACK) == (4, 15, 7)
    assert HP == 8 + MODS["CON"] + (LEVEL - 1) * (5 + MODS["CON"])
    assert THEMES["day"].keys() == THEMES["night"].keys(), "themes must define the same colours"
    assert [rarity(dict(commits=n)) for n in (1489, 200, 199, 50, 49, 25, 6)] == \
        ["LEGENDARY", "VERY RARE", "RARE", "RARE", "UNCOMMON", "UNCOMMON", "COMMON"]
    assert ROAD == ["Veritarach", "Hecate", "Argos", "Hephastion", "Folio"]
    assert LEVEL == len(PROJECTS) and FIELDS[0][0] == f"Artificer {LEVEL}"
    assert rarity(dict(commits=6, rarity="RARE")) == "RARE"
    assert sum(rarity(p) == "LEGENDARY" for p in PROJECTS) == 1, "exactly one legendary item (the main quest)"


if __name__ == "__main__":
    check()
    refresh_commits()
    for theme in THEMES:
        files = {"character-sheet": sheet(theme), "equipment": equipment_panel(theme)}
        files.update({f"header-{slug}": header(title, theme) for slug, title in HEADERS.items()})
        for p in PROJECTS:
            r, slug = rarity(p), "item-" + p["name"].lower()
            files[slug] = (legendary_banner(p, theme) if r == "LEGENDARY" else common_chip(p, theme) if r == "COMMON"
                           else item_card(p, theme, wide=r == "UNCOMMON"))
        files.update({f"quest-{i + 1}": quest_note(q, theme, tilt) for i, (q, tilt) in enumerate(zip(QUESTS, (-2, 1.5, -1)))})
        for name, svg in files.items():
            (ASSETS / f"{name}-{theme}.svg").write_text(svg, encoding="utf-8")
    write_readme()
    print(", ".join(f"{p['name']} {p['commits']} ({rarity(p).lower()})" for p in PROJECTS))

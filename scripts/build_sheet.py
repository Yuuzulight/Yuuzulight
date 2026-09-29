"""Generate the profile's SVG art: the character sheet and the section headers.

Edit the data below, then run:  python scripts/build_sheet.py
Every derived number (modifiers, saves, skills, HP, spell DC) is computed here
from 5e rules, so changing a score or the level keeps the sheet consistent.
"""
import math
import random
from html import escape
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# ---------------------------------------------------------------- data
NAME = "YUUZULIGHT"
FIELDS = [  # (value, label), laid out 2x2
    ("Artificer 10", "CLASS & LEVEL"), ("Battle Smith", "SUBCLASS"),
    ("Solo Developer", "BACKGROUND"), ("Local-First Good", "ALIGNMENT"),
]
LEVEL = 10  # one level per public project
HIT_DIE = 8
AC, SPEED = 17, "30 ft"  # half plate: 15 + DEX (max 2)
ABILITIES = [  # rolled, not point-buy
    ("STR", 13, "raw C++"), ("DEX", 16, "C# / .NET"), ("CON", 14, "runs offline"),
    ("INT", 17, "ML & data"), ("WIS", 15, "privacy sense"), ("CHA", 12, "Live2D charm"),
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
    ("Steel Defender: Mana", "A companion construct with a voice and a face."),
    ("Infuse Item: Local-first", "Every tool runs on your own machine."),
    ("Tool Expertise", "C++, C#, Python, TypeScript and Go."),
    ("Flash of Genius", "Ten public projects, each built solo."),
]
# the bigger projects (by commit count), in the order they were finished;
# Mana is the main quest, still in progress
ROAD = ["Veritarach", "Hecate", "Argos", "Hephastion", "Folio"]
IDEAL = ["Your data stays", "on your machine."]
FLAW = ["Writes a renderer", "from scratch before", "adding a dependency."]
HEADERS = {"infusions": "INFUSIONS", "quest-board": "QUEST BOARD", "equipment": "EQUIPMENT"}

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

# ---------------------------------------------------------------- palette
PAPER = ("#f6f0ff", "#ece2ff", "#e0d2fb")
INK, INK_SOFT, LABEL, GLOSS = "#3a2a5e", "#4f4270", "#8a74c8", "#7d66b8"
LILAC, LINE = "#b9a2f0", "#cdb9f5"
ACCENT, ACCENT_DARK = "#7c5bd6", "#5f41b8"  # the one saturated colour
SERIF = "Georgia, 'Palatino Linotype', 'Book Antiqua', 'Times New Roman', serif"

CSS = f"""
  .label {{ font: 14px {SERIF}; letter-spacing: 2px; fill: {LABEL}; }}
  .value {{ font: 21px {SERIF}; fill: {INK}; }}
  .big {{ font: bold 36px {SERIF}; fill: {INK}; }}
  .body {{ font: 17px {SERIF}; fill: {INK_SOFT}; }}
  .head {{ font: bold 17px {SERIF}; fill: {INK}; }}
  .stop {{ font: bold 15px {SERIF}; fill: {INK}; }}
  .gloss {{ font: italic 15px {SERIF}; fill: {GLOSS}; }}
  .num {{ font: bold 17px {SERIF}; fill: {INK}; }}
  .panel {{ fill: #ffffff; fill-opacity: .6; stroke: {LINE}; stroke-width: 1.4; }}
  .rule {{ stroke: {LINE}; }}
  .trail {{ animation: march 2.4s linear infinite; }}
  @keyframes march {{ to {{ stroke-dashoffset: -44 }} }}
  @media (prefers-reduced-motion: reduce) {{ .trail {{ animation: none }} }}
"""

rnd = random.Random(7)


def torn_path(w, h, m=10):
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
            t = d / length
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if y0 == y1:
                y += off
            else:
                x += off
            pts.append(f"{x:.1f} {y:.1f}")
    return "M" + " L".join(pts) + " Z"


def grain_pattern():
    """Paper grain as a tile of tiny dots: cheap to paint, unlike a full-size noise filter."""
    dots = "".join(
        f'<circle cx="{rnd.uniform(0, 120):.1f}" cy="{rnd.uniform(0, 120):.1f}" r="{rnd.uniform(.4, 1.1):.2f}" fill-opacity="{rnd.uniform(.08, .22):.2f}"/>'
        for _ in range(110))
    return f'<pattern id="grain" width="120" height="120" patternUnits="userSpaceOnUse"><g fill="{INK}">{dots}</g></pattern>'


def smooth(pts):
    """Catmull-Rom curve through every point, as cubic Beziers."""
    d = f"M{pts[0][0]} {pts[0][1]}"
    for i in range(len(pts) - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]} {p2[1]}"
    return d


def t(x, y, text, cls, anchor="start", extra=""):
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"{extra}>{escape(text)}</text>'


FLOURISH = f'<path id="flourish" d="M0 0 C 22 0 32 10 32 28 C 32 14 44 6 60 8 M0 0 C 0 22 10 32 28 32 C 14 32 6 44 8 60 M10 10 L18 18" fill="none" stroke="{LILAC}" stroke-width="2.2" stroke-linecap="round"/>'


# ---------------------------------------------------------------- sheet
def sheet():
    W, H = 1000, 1150
    torn = torn_path(W, H)
    out = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
           f'<title>Yuuzulight: level {LEVEL} Artificer (Battle Smith), Local-First Good</title>',
           f'<defs><style>{CSS}</style>',
           f'<linearGradient id="paperFill" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{PAPER[0]}"/><stop offset=".55" stop-color="{PAPER[1]}"/><stop offset="1" stop-color="{PAPER[2]}"/></linearGradient>',
           f'<radialGradient id="vignette" cx=".5" cy=".5" r=".75"><stop offset=".7" stop-color="{ACCENT}" stop-opacity="0"/><stop offset="1" stop-color="{ACCENT}" stop-opacity=".14"/></radialGradient>',
           f'<linearGradient id="ribbon" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8d6ee2"/><stop offset="1" stop-color="{ACCENT}"/></linearGradient>',
           grain_pattern(), f'<clipPath id="paper"><path d="{torn}"/></clipPath>', FLOURISH, '</defs>',
           # paper
           '<g clip-path="url(#paper)">',
           f'<rect width="{W}" height="{H}" fill="url(#paperFill)"/>',
           f'<rect width="{W}" height="{H}" fill="url(#grain)"/>',
           f'<rect width="{W}" height="{H}" fill="url(#vignette)"/>', '</g>',
           f'<path d="{torn}" fill="none" stroke="{LILAC}" stroke-width="1.4"/>',
           f'<rect x="28" y="28" width="{W - 56}" height="{H - 56}" rx="6" fill="none" stroke="{LILAC}" stroke-opacity=".8"/>',
           '<use href="#flourish" transform="translate(34 34)"/>',
           f'<use href="#flourish" transform="translate({W - 34} 34) scale(-1 1)"/>',
           f'<use href="#flourish" transform="translate(34 {H - 34}) scale(1 -1)"/>',
           f'<use href="#flourish" transform="translate({W - 34} {H - 34}) scale(-1 -1)"/>']

    # header: ribbon + wax seal + fields
    out += [f'<path d="M52 88 H112 V156 H52 L72 122 Z" fill="{ACCENT_DARK}"/>',
            f'<path d="M508 88 H448 V156 H508 L488 122 Z" fill="{ACCENT_DARK}"/>',
            '<path d="M92 146 L112 156 V146 Z M468 146 L448 156 V146 Z" fill="#3d2a80" opacity=".6"/>',
            '<path id="ribbonBody" d="M92 72 Q280 60 468 72 V146 Q280 134 92 146 Z" fill="url(#ribbon)"/>',
            '<path d="M92 72 Q280 60 468 72 V146 Q280 134 92 146 Z" fill="url(#grain)" opacity=".6"/>',
            '<path d="M92 79 Q280 67 468 79 M92 139 Q280 127 468 139" fill="none" stroke="#e9dcff" stroke-opacity=".6"/>',
            '<path id="nameArc" d="M116 122 Q280 108 444 122" fill="none"/>',
            f'<text font-family="{escape(SERIF)}" font-size="40" font-weight="bold" fill="#fdfbff" text-anchor="middle">'
            f'<textPath href="#nameArc" startOffset="50%" textLength="300" lengthAdjust="spacingAndGlyphs">{NAME}</textPath></text>',
            t(280, 176, "CHARACTER NAME", "label", "middle")]
    seal = "M" + " L".join(
        f"{(31 if i % 2 else 26) * math.cos(i * math.pi / 18):.1f} {(31 if i % 2 else 26) * math.sin(i * math.pi / 18):.1f}"
        for i in range(36)) + " Z"
    out += [f'<g transform="translate(514 126)"><path d="{seal}" fill="{ACCENT_DARK}" stroke="{ACCENT_DARK}" stroke-width="3" stroke-linejoin="round"/>',
            '<circle r="19" fill="none" stroke="#c9b3f5" stroke-width="1.5"/>',
            '<path d="M-13 -12 A 18 18 0 0 1 8 -17" fill="none" stroke="#efe7ff" stroke-opacity=".6" stroke-width="2" stroke-linecap="round"/>',
            f'<text y="8" text-anchor="middle" font-family="{escape(SERIF)}" font-size="22" font-weight="bold" fill="#efe7ff">Y</text></g>']
    out.append('<rect x="572" y="56" width="378" height="136" rx="8" class="panel"/>')
    out.append('<path d="M592 124 H930 M761 70 V178" class="rule"/>')
    for i, (value, label) in enumerate(FIELDS):
        x, y = 592 + (i % 2) * 189, 102 + (i // 2) * 66
        out += [t(x, y, value, "value"), t(x, y + 18, label, "label")]

    # ability scores
    xs = [50 + i * 152.4 for i in range(6)]
    out.append(t(50, 226, "ABILITY SCORES", "label") + t(950, 226, "rolled, not point-buy", "gloss", "end"))
    for x, (abbr, score, gloss) in zip(xs, ABILITIES):
        cx = x + 69
        out += [f'<rect x="{x:.1f}" y="238" width="138" height="104" rx="10" class="panel"/>',
                t(cx, 262, abbr, "label", "middle"), t(cx, 304, signed(MODS[abbr]), "big", "middle"),
                f'<ellipse cx="{cx:.1f}" cy="326" rx="22" ry="12" fill="#fff" stroke="{LILAC}"/>',
                t(cx, 331, str(score), "body", "middle"), t(cx, 364, gloss, "gloss", "middle")]

    # combat strip
    combat = [("ARMOR CLASS", str(AC), "half plate"), ("INITIATIVE", signed(MODS["DEX"]), ""),
              ("SPEED", SPEED, ""), ("HIT POINTS", str(HP), f"{LEVEL}d{HIT_DIE} hit dice"),
              ("PROFICIENCY", signed(PROF), ""), ("SPELL SAVE DC", str(SPELL_DC), f"spell attack {signed(SPELL_ATTACK)}")]
    for x, (label, big, sub) in zip(xs, combat):
        cx = x + 69
        shape = (f'<path d="M{x:.1f} 386 H{x + 138:.1f} V440 Q{x + 138:.1f} 474 {cx:.1f} 488 Q{x:.1f} 474 {x:.1f} 440 Z" class="panel"/>'
                 if label == "ARMOR CLASS" else f'<rect x="{x:.1f}" y="386" width="138" height="100" rx="10" class="panel"/>')
        out += [shape, t(cx, 408, label, "label", "middle"), t(cx, 450, big, "big", "middle")]
        if sub:
            out.append(t(cx, 474, sub, "gloss", "middle"))

    # saving throws
    out += ['<rect x="50" y="506" width="430" height="104" rx="10" class="panel"/>', t(70, 530, "SAVING THROWS", "label")]
    for i, (abbr, _, _) in enumerate(ABILITIES):
        x, y = 70 + (i % 3) * 140, 562 + (i // 3) * 32
        dot = ACCENT if abbr in SAVE_PROFS else "none"
        out += [f'<circle cx="{x + 6}" cy="{y - 6}" r="6" fill="{dot}" stroke="{ACCENT}" stroke-width="1.5"/>',
                t(x + 20, y, signed(SAVES[abbr]), "num"), t(x + 56, y, abbr, "body")]

    # skills
    out += ['<rect x="50" y="626" width="430" height="262" rx="10" class="panel"/>', t(70, 650, "SKILLS", "label"),
            t(460, 650, "● proficient", "gloss", "end")]
    for i, (name, abbr, prof, flavour, bonus) in enumerate(SKILL_BONUS):
        y = 682 + i * 30
        out += [f'<circle cx="76" cy="{y - 6}" r="6" fill="{ACCENT if prof else "none"}" stroke="{ACCENT}" stroke-width="1.5"/>',
                t(90, y, signed(bonus), "num"),
                f'<text x="126" y="{y}" class="body">{escape(name)} <tspan class="gloss">· {escape(flavour)}</tspan></text>']
    out += [f'<rect x="70" y="{682 + 6 * 30 - 16}" width="390" height="36" rx="18" fill="#fff" fill-opacity=".7" stroke="{LINE}"/>',
            t(90, 682 + 6 * 30 + 8, str(PASSIVE_PERCEPTION), "num"),
            t(126, 682 + 6 * 30 + 8, "PASSIVE PERCEPTION", "label")]

    # features, ideal & flaw
    out += ['<rect x="510" y="506" width="440" height="258" rx="10" class="panel"/>', t(530, 530, "FEATURES & TRAITS", "label")]
    for i, (head, body) in enumerate(FEATURES):
        y = 566 + i * 54
        out += [t(530, y, head, "head"), t(530, y + 22, body, "body")]
    out += ['<rect x="510" y="780" width="440" height="108" rx="10" class="panel"/>', t(530, 804, "IDEAL", "label")]
    out += [t(530, 826 + 20 * i, line, "body") for i, line in enumerate(IDEAL)]
    out.append(t(740, 804, "FLAW", "label"))
    out += [t(740, 826 + 20 * i, line, "body") for i, line in enumerate(FLAW)]

    # map: the road so far, one stop per finished project in completion order
    out += ['<rect x="50" y="906" width="900" height="200" rx="10" class="panel"/>', t(70, 930, "THE ROAD SO FAR", "label")]
    out.append(f'<g fill="none" stroke="{LILAC}" stroke-opacity=".35">'
               + "".join(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx - k * 16}" ry="{ry - k * 7}" transform="rotate({rot} {cx} {cy})"/>'
                         for cx, cy, rx, ry, rot in [(300, 1024, 64, 20, -6), (600, 1022, 58, 18, 5)] for k in range(3))
               + '</g>')
    stops = [(100, 1022)] + [(190 + i * 540 / (len(ROAD) - 1), 990 if i % 2 == 0 else 1052) for i in range(len(ROAD))] + [(812, 1030)]
    out.append(f'<path class="trail" d="{smooth(stops)}" fill="none" stroke="{ACCENT_DARK}" stroke-width="3" stroke-linecap="round" stroke-dasharray="2 9"/>')
    x, y = stops[0]
    out += [f'<circle cx="{x}" cy="{y}" r="7" fill="#fff" stroke="{ACCENT_DARK}" stroke-width="2"/>',
            t(x, y + 30, "Set out", "stop", "middle")]
    for (x, y), name in zip(stops[1:-1], ROAD):
        above = y < 1020
        out += [f'<circle cx="{x}" cy="{y}" r="7" fill="{LILAC}" stroke="{ACCENT_DARK}" stroke-width="2"/>',
                t(x, y - 18 if above else y + 30, name, "stop", "middle")]
    qx, qy = stops[-1]
    out += [f'<path d="M{qx - 12} {qy - 12} L{qx + 12} {qy + 12} M{qx + 12} {qy - 12} L{qx - 12} {qy + 12}" stroke="{ACCENT}" stroke-width="5" stroke-linecap="round"/>',
            t(qx, qy + 38, "MAIN QUEST: MANA", "label", "middle"), t(qx, qy + 55, "in progress", "gloss", "middle")]
    star = lambda r, w: " ".join(f"M0 0 L{r * math.cos(a):.1f} {r * math.sin(a):.1f} L{w * math.cos(a + .5):.1f} {w * math.sin(a + .5):.1f} Z"
                                 for a in [k * math.pi / 2 - math.pi / 2 for k in range(4)])
    out += ['<g transform="translate(900 1004)">',
            f'<circle r="44" fill="#fff" fill-opacity=".6" stroke="{LILAC}"/>',
            f'<circle r="37" fill="none" stroke="{LILAC}" stroke-dasharray="1 4"/>',
            f'<g transform="rotate(45)"><path d="{star(24, 6)}" fill="#cdb9f5"/></g>',
            f'<path d="{star(34, 8)}" fill="{ACCENT}"/>',
            '<circle r="4" fill="#fff"/>',
            t(0, -50, "N", "head", "middle"), '</g>']
    out.append('</svg>')
    return "\n".join(out)


# ---------------------------------------------------------------- section headers
def header(title):
    W, H = 1000, 72
    pw = len(title) * 21 + 90  # plaque width sized to the lettering
    x0 = (W - pw) / 2
    return "\n".join([
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
        f'<title>{escape(title.title())}</title>',
        f'<defs><linearGradient id="p" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{PAPER[0]}"/><stop offset="1" stop-color="{PAPER[2]}"/></linearGradient>{grain_pattern()}</defs>',
        f'<path d="M60 36 H{x0 - 18:.0f} M{x0 + pw + 18:.0f} 36 H{W - 60}" stroke="{LILAC}" stroke-width="1.6"/>',
        f'<path d="M48 36 L60 28 L72 36 L60 44 Z M{W - 72} 36 L{W - 60} 28 L{W - 48} 36 L{W - 60} 44 Z" fill="{LILAC}"/>',
        f'<path d="M{x0:.0f} 12 H{x0 + pw:.0f} L{x0 + pw + 14:.0f} 36 L{x0 + pw:.0f} 60 H{x0:.0f} L{x0 - 14:.0f} 36 Z" fill="url(#p)" stroke="{LILAC}" stroke-width="1.6"/>',
        f'<path d="M{x0:.0f} 12 H{x0 + pw:.0f} L{x0 + pw + 14:.0f} 36 L{x0 + pw:.0f} 60 H{x0:.0f} L{x0 - 14:.0f} 36 Z" fill="url(#grain)"/>',
        f'<text x="{W / 2}" y="45" text-anchor="middle" font-family="{escape(SERIF)}" font-size="26" font-weight="bold" letter-spacing="5" fill="{INK}"'
        f' textLength="{pw - 70}" lengthAdjust="spacingAndGlyphs">{escape(title)}</text>',
        '</svg>'])


def check():
    assert [mod(s) for s in (8, 9, 10, 11, 17)] == [-1, -1, 0, 0, 3]
    assert (PROF, SPELL_DC, SPELL_ATTACK) == (4, 15, 7)
    assert HP == 8 + MODS["CON"] + (LEVEL - 1) * (5 + MODS["CON"])


if __name__ == "__main__":
    check()
    (ASSETS / "character-sheet.svg").write_text(sheet(), encoding="utf-8")
    for slug, title in HEADERS.items():
        (ASSETS / f"header-{slug}.svg").write_text(header(title), encoding="utf-8")
    print(f"HP {HP}, DC {SPELL_DC}, passive perception {PASSIVE_PERCEPTION}, saves {SAVES}")

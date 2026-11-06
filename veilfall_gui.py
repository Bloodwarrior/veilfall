"""VEILFALL graphical maps - pure Python stdlib Tkinter. Python 3.9+.

v0.4: polish pass on the v0.3 Shadows-style presentation:
  * pan (drag) + zoom (wheel toward cursor, +/- buttons, Reset View)
    via a pure view transform, so click/hover stay accurate
  * hover halo + black/gold tooltip on location markers
  * deterministic terrain detail (trees, waves, peaks, snow sparkle)
  * Enshadow hex creep: hexes darken toward purple-black near
    corrupted locations, with distance falloff
  * drop shadows under shields/banners/tokens, green scheme path line
  * event ticker under the map (latest chronicle entry, click = Chronicle)
  * agent roster ("MINIONS") strip in the left panel
  * tile view draws shapes (houses, trees, shrine, water, gravestones)
  * god chooser rebuilt as four presentation cards
  * keys: Space = END TURN, W = Watch 12, Esc = clear selection

v0.3: reworked to the Shadows of Forbidden Gods visual signatures
(studied from screenshots; all art here is original, drawn in code):
  * full-bleed HEX terrain map - dark sea, forest/plains land, snow north
  * location shields with BLACK RIBBON name banners, white link graph
  * political borders: glowing multi-stroke hulls in each kingdom colour
  * capitals wear a heraldic banner with an original sigil glyph
  * agents / hunters as circular portrait tokens on the map
  * black + gold UI chrome: god panel top-left, turn panel top-right,
    selected-location panel left, ACTIONS + THREATS panel right,
    big red END TURN bottom-left, view-mask toggle (World/Enshadow/Clues)
  * the Ruinarch-style 18x12 tile view of the selected location (tab)
  * Chronicle tab

All generation logic (hex terrain, hulls, links, tokens, masks, GUI game
actions) lives in plain functions that never touch Tk, so this module can
be imported and tested headless. The Tk app is built only inside main().
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import veilfall
from veilfall import (Agent, GODS, POWERS, SCHEMES, World, clamp,
                      person_name, save_world)

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except Exception:  # headless / no Tk build: logic functions still work
    tk = None
    messagebox = None
    ttk = None

MAP_W = 100.0
MAP_H = 100.0
TILE_COLS = 18
TILE_ROWS = 12

# Heraldic kingdom colours (banner / border glow), indexed by the
# kingdom's order in world.kingdoms - always distinct for the 4 kingdoms.
KINGDOM_COLORS = ["#7a1f2b", "#1f4d3a", "#27436e", "#5e2a72"]
KINGDOM_GLOWS = ["#e5484d", "#3fb96f", "#4d8de5", "#c07fe8"]
KINGDOM_LABEL_COLORS = ["#f0a3a8", "#a3e8bf", "#a3c8f0", "#dcb0f5"]
# Original sigils, one per kingdom (simple geometric / heraldic marks).
KINGDOM_SIGILS = ["\u25c6", "\u263e", "\u2726", "\u2660"]

# Per-god presentation for the chooser cards: a big sigil glyph, a deep
# card colour and a light accent. Dark, tasteful palette; derived from
# the god key only, never stored on pickled objects.
GOD_PRESENTATION = {
    "1": {"sigil": "\u03a8", "color": "#2f3a17", "accent": "#d8cfb0"},   # Devouring Maw: bone / moss green
    "2": {"sigil": "\u271d", "color": "#2a2110", "accent": "#f0dca0"},   # Whispering Saint: candle gold
    "3": {"sigil": "\u265a", "color": "#12333d", "accent": "#7fb6d9"},   # Drowned King: deep sea teal
    "4": {"sigil": "\u263d", "color": "#2b2135", "accent": "#c9a0e8"},   # Hollow Child: charcoal violet
}

# Enshadow hex creep: nearest-location Enshadow is at full strength
# within this distance (map units) and gone past the outer distance.
CREEP_FULL_DIST = 8.0
CREEP_MAX_DIST = 22.0
CREEP_TARGET = (34, 8, 46)  # the same deep purple-black as enshadow_color(100)

GOLD = "#d8b25a"
GOLD_LIGHT = "#f0dca0"
CHROME_BG = "#0a0a0c"
PANEL_BG = "#101014"
SERIF = "Georgia"
SERIF_FALLBACK = "Times New Roman"

KIND_GLYPH = {"Capital": "C", "Town": "T", "Abbey": "+", "Port": "~", "Village": "o"}

LEGEND_TEXT = (
    "Drawn tiles: house (walls + roof), tree, road, water with waves, shrine (pillars + lintel), gravestones.\n"
    "State marks: U=risen undead in the graveyard  green + on a house=plague-sick  "
    "purple creep=Enshadow  broken shrine (x)=desecrated  o on a house=cult household"
)

HEX_R = 4.4  # hex radius in map units (pointy-top hexes)

TERRAIN_FILLS = {
    "sea": ["#16324a", "#132c44", "#1a3852"],
    "forest": ["#2e4a22", "#2a4420", "#334f26"],
    "plains": ["#4a5d2a", "#54682f", "#425426"],
    "snow": ["#aebfc6", "#c2d2d8", "#9db2ba"],
    "hills": ["#5c5a44", "#66624c", "#55523f"],
}
TERRAIN_FILLS_DIM = {
    "sea": ["#0a141f", "#09121b", "#0b1622"],
    "forest": ["#101a0e", "#0e180c", "#111c0f"],
    "plains": ["#161c0e", "#181f10", "#151b0d"],
    "snow": ["#232a2e", "#272f33", "#20272b"],
    "hills": ["#1b1a14", "#1e1d16", "#1a1913"],
}


def _seed(text):
    return veilfall._name_seed(text)


# ---------------------------------------------------------------- layout

def ensure_map_positions(world):
    """Give every location x/y. Handles v0.1 saves whose Location objects
    were unpickled without x/y attributes at all."""
    missing = []
    for loc in world.locations:
        x = getattr(loc, "x", None)
        y = getattr(loc, "y", None)
        if x is None or y is None or (x == 0.0 and y == 0.0):
            missing.append(loc)
    if missing:
        veilfall.assign_map_positions(world.locations, world.kingdoms)
    return world


def enshadow_color(enshadow):
    """Pale gold (0) -> deep purple-black (100), as an #rrggbb string."""
    t = max(0.0, min(100.0, float(enshadow))) / 100.0
    r0, g0, b0 = 216, 178, 90
    r1, g1, b1 = 34, 8, 46
    r = int(r0 + (r1 - r0) * t)
    g = int(g0 + (g1 - g0) * t)
    b = int(b0 + (b1 - b0) * t)
    return "#" + format(r, "02x") + format(g, "02x") + format(b, "02x")


def kingdom_index(world, kingdom_name):
    for i, k in enumerate(world.kingdoms):
        if k.name == kingdom_name:
            return i
    return _seed(str(kingdom_name)) % len(KINGDOM_COLORS)


def kingdom_sigil(world, kingdom_name):
    """Original sigil for a kingdom, derived from its order/name only -
    never stored on the pickled Kingdom, so old saves are safe."""
    return KINGDOM_SIGILS[kingdom_index(world, kingdom_name) % len(KINGDOM_SIGILS)]


def kingdom_color(world, kingdom_name):
    return KINGDOM_COLORS[kingdom_index(world, kingdom_name) % len(KINGDOM_COLORS)]


def kingdom_glow(world, kingdom_name):
    return KINGDOM_GLOWS[kingdom_index(world, kingdom_name) % len(KINGDOM_GLOWS)]


# ---------------------------------------------------------------- hexes

def world_signature(world):
    return "|".join(k.name for k in world.kingdoms)


def terrain_for_hex(world, cx, cy, col, row):
    """Deterministic terrain for one hex centre. Sea fills everything far
    from any location; the north is snow; land near locations is forest /
    plains / hills by a stable hash. Returns (terrain, variant 0-2)."""
    h = _seed(world_signature(world) + ":" + str(col) + "," + str(row))
    variant = h % 3
    if not world.locations:
        return ("sea", variant)
    dmin = min(math.hypot(cx - loc.x, cy - loc.y) for loc in world.locations)
    if dmin > 26.0:
        return ("sea", variant)
    if cy <= 15.0:
        return ("snow", variant)
    roll = h % 100
    if roll < 38:
        return ("forest", variant)
    if roll < 80:
        return ("plains", variant)
    return ("hills", variant)


def hex_grid(world, x_min=-30.0, x_max=130.0):
    """All hexes covering (and bleeding past) the 0-100 map. Each entry:
    (col, row, cx, cy, terrain, variant). Deterministic per world."""
    out = []
    dx = math.sqrt(3.0) * HEX_R
    dy = 1.5 * HEX_R
    row = 0
    cy = HEX_R
    while cy - HEX_R < MAP_H + HEX_R:
        offset = dx / 2.0 if row % 2 else 0.0
        col = 0
        cx = x_min + offset
        while cx < x_max:
            terrain, variant = terrain_for_hex(world, cx, cy, col, row)
            out.append((col, row, cx, cy, terrain, variant))
            col += 1
            cx += dx
        row += 1
        cy += dy
    return out


def hex_corners(cx, cy, r=None):
    """Pointy-top hex corners in map units."""
    if r is None:
        r = HEX_R
    pts = []
    for i in range(6):
        ang = math.radians(60 * i - 30)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def hex_fill(terrain, variant, dim=False):
    table = TERRAIN_FILLS_DIM if dim else TERRAIN_FILLS
    fills = table.get(terrain, table["plains"])
    return fills[variant % len(fills)]


# ------------------------------------------------------- colour blending

def _hex_to_rgb(colour):
    c = colour.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def _rgb_to_hex(r, g, b):
    return "#" + format(int(round(r)), "02x") + format(int(round(g)), "02x") + format(int(round(b)), "02x")


def blend_color(colour_a, colour_b, t):
    """Linear blend between two #rrggbb colours. t=0 -> a, t=1 -> b."""
    t = max(0.0, min(1.0, float(t)))
    ar, ag, ab = _hex_to_rgb(colour_a)
    br, bg, bb = _hex_to_rgb(colour_b)
    return _rgb_to_hex(ar + (br - ar) * t, ag + (bg - ag) * t, ab + (bb - ab) * t)


# ------------------------------------------------------- enshadow creep

def enshadow_at_point(world, ux, uy):
    """Effective Enshadow (0-100) at a map point: the strongest nearby
    location's Enshadow, at full strength within CREEP_FULL_DIST and
    falling linearly to zero at CREEP_MAX_DIST."""
    best = 0.0
    for loc in world.locations:
        en = float(getattr(loc, "enshadow", 0))
        if en <= 0:
            continue
        d = math.hypot(ux - loc.x, uy - loc.y)
        if d <= CREEP_FULL_DIST:
            factor = 1.0
        elif d >= CREEP_MAX_DIST:
            factor = 0.0
        else:
            factor = (CREEP_MAX_DIST - d) / (CREEP_MAX_DIST - CREEP_FULL_DIST)
        val = en * factor
        if val > best:
            best = val
    return best


def hex_display_fill(world, cx, cy, terrain, variant, dim=False):
    """The fill a hex is actually drawn with: its terrain colour blended
    toward deep purple-black by the Enshadow creep at its centre.
    Enshadow 0 leaves the terrain colour untouched; Enshadow 100 at
    ground zero gives exactly the deep purple-black #22082e."""
    if dim:
        base = hex_fill(terrain, variant, dim=True)
        en = enshadow_at_point(world, cx, cy)
        if en <= 0:
            return base
        blended = blend_color(base, "#16061f", en / 100.0)
        return blended
    base = hex_fill(terrain, variant, dim=False)
    en = enshadow_at_point(world, cx, cy)
    if en <= 0:
        return base
    return blend_color(base, _rgb_to_hex(*CREEP_TARGET), en / 100.0)


# ------------------------------------------------------- terrain detail

def terrain_detail(world, col, row, cx, cy, terrain):
    """Deterministic decoration marks for one hex, derived only from the
    world signature and the hex's col/row - the same world always draws
    the same detail. Returns a list of dicts:
      {"kind": "tree", "x", "y", "s"}     triangle canopy, s = half-width
      {"kind": "wave", "pts": [(x, y)..]} a small squiggle polyline
      {"kind": "peak", "x", "y", "s"}     a hill peak mark
      {"kind": "dot", "x", "y", "r"}      a snow sparkle dot
    Plains get no marks (they stay clean)."""
    seed = _seed(world_signature(world) + ":detail:" + str(col) + "," + str(row))
    rng = random.Random(seed)
    out = []
    if terrain == "forest":
        for _ in range(1 + seed % 3):
            out.append({"kind": "tree",
                        "x": cx + rng.uniform(-2.4, 2.4),
                        "y": cy + rng.uniform(-2.2, 2.2),
                        "s": rng.uniform(0.9, 1.4)})
    elif terrain == "sea":
        n_waves = 1 if seed % 2 == 0 else 2
        for _ in range(n_waves):
            wx = cx + rng.uniform(-2.2, 0.6)
            wy = cy + rng.uniform(-2.2, 2.2)
            pts = []
            for i in range(5):
                pts.append((wx + i * 0.75, wy + (0.45 if i % 2 else -0.45)))
            out.append({"kind": "wave", "pts": pts})
    elif terrain == "hills":
        out.append({"kind": "peak",
                    "x": cx + rng.uniform(-0.8, 0.8),
                    "y": cy + rng.uniform(-0.8, 0.8),
                    "s": rng.uniform(1.4, 1.9)})
    elif terrain == "snow":
        for _ in range(3):
            out.append({"kind": "dot",
                        "x": cx + rng.uniform(-2.8, 2.8),
                        "y": cy + rng.uniform(-2.8, 2.8),
                        "r": 0.3})
    return out


# ------------------------------------------------------- view transform
# A view transform is a tuple (scale, ox, oy): pixel = map * scale + o.
# Keeping it a plain tuple makes pan/zoom maths headless-testable.

def make_view_transform(canvas_w, canvas_h, zoom=1.0, pan_x=0.0, pan_y=0.0):
    """Fit the 0-100 map into the canvas (height-fit, centred), then
    apply zoom and pan (pan is in pixels)."""
    base = max(1.0, float(canvas_h)) / 100.0
    scale = base * float(zoom)
    ox = (float(canvas_w) - 100.0 * scale) / 2.0 + float(pan_x)
    oy = (float(canvas_h) - 100.0 * scale) / 2.0 + float(pan_y)
    return (scale, ox, oy)


def view_to_px(transform, ux, uy):
    scale, ox, oy = transform
    return (ux * scale + ox, uy * scale + oy)


def view_to_map(transform, px, py):
    scale, ox, oy = transform
    return ((px - ox) / scale, (py - oy) / scale)


def pan_to_center(transform, canvas_w, canvas_h, ux, uy, zoom):
    """The (pan_x, pan_y) that puts map point (ux, uy) at canvas centre
    for the same zoom. transform is the current transform (unused for
    the maths beyond API symmetry; kept for callers/tests)."""
    base = max(1.0, float(canvas_h)) / 100.0
    scale = base * float(zoom)
    pan_x = canvas_w / 2.0 - ux * scale - (canvas_w - 100.0 * scale) / 2.0
    pan_y = canvas_h / 2.0 - uy * scale - (canvas_h - 100.0 * scale) / 2.0
    return (pan_x, pan_y)


def location_at_point(world, transform, px, py, radius_px=42.0):
    """The location whose marker centre is nearest to pixel (px, py),
    within radius_px - or None. Pure: works for any pan/zoom transform."""
    best = None
    best_d = float(radius_px)
    for loc in world.locations:
        x, y = view_to_px(transform, loc.x, loc.y)
        d = math.hypot(px - x, py - y)
        if d < best_d:
            best_d = d
            best = loc
    return best


def tooltip_text(loc):
    """Hover tooltip body for a location marker."""
    return (loc.name + " - " + loc.kind + " of " + loc.kingdom +
            "\nEnshadow " + str(loc.enshadow) + "   Clues " + str(loc.clues) +
            "   Devotion " + str(loc.devotion))


# ------------------------------------------------------- ticker / roster

def latest_chronicle_text(world):
    """The event ticker's line: the world's most recent chronicle entry."""
    if world.chronicle:
        return world.chronicle[-1]
    return ""


def agent_location(world, agent):
    """Where an agent stands: their scheme target while scheming, else home."""
    if agent.scheme is not None and agent.scheme_loc:
        loc = world.loc(agent.scheme_loc)
        if loc is not None:
            return loc
    return world.loc(agent.home)


def roster_entries(world):
    """MINIONS-strip data: one entry per living agent, in roster order."""
    out = []
    for a in world.agents:
        if not a.alive:
            continue
        loc = agent_location(world, a)
        busy = a.scheme is not None
        out.append({"name": a.name, "initials": person_initials(a.name),
                    "busy": busy, "turns_left": int(a.scheme_left) if busy else 0,
                    "scheme_name": SCHEMES[a.scheme]["name"] if busy and a.scheme in SCHEMES else "",
                    "loc_name": loc.name if loc is not None else a.home,
                    "ring": "#7a7585" if busy else "#b366ff",
                    "fill": "#191423" if busy else "#241333"})
    return out


def hunter_count(world):
    return len([h for h in world.heroes if h.alive])


def green_paths(world, selected, agent):
    """Green planning-path lines (Shadows draws its agent paths green):
    pairs of locations to join. Covers the picked agent's scheme target
    and the agent<->selected-location link. Returns [(loc_a, loc_b)]."""
    out = []

    def add(a, b):
        if a is not None and b is not None and a.name != b.name:
            pair = (a, b)
            if pair not in out and (b, a) not in out:
                out.append(pair)

    if agent is not None and getattr(agent, "alive", False):
        aloc = agent_location(world, agent)
        if agent.scheme is not None and agent.scheme_loc:
            add(aloc, world.loc(agent.scheme_loc))
        if selected is not None:
            add(aloc, selected)
    return out


# ------------------------------------------------------- god cards

def god_card_data():
    """Chooser-card data for all four gods, in engine order."""
    out = []
    for key in sorted(GODS.keys()):
        g = GODS[key]
        pres = GOD_PRESENTATION.get(key, {"sigil": "?", "color": "#22222a", "accent": GOLD_LIGHT})
        out.append({"key": key, "name": g["name"], "title": g["title"],
                    "desc": g["desc"], "gift": g["gift"],
                    "sigil": pres["sigil"], "color": pres["color"],
                    "accent": pres["accent"]})
    return out


# ---------------------------------------------------------------- borders

def convex_hull(points):
    """Andrew monotone chain. points: list of (x, y). Returns hull points
    counter-clockwise, no duplicated closing point."""
    pts = sorted(set(points))
    if len(pts) <= 1:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def kingdom_border_points(world, kingdom_name):
    """A smoothed, expanded hull around a kingdom's locations - the
    honest Tk approximation of Shadows' hex-edge political border.
    Returns a closed list of (x, y) in map units (first != last)."""
    mine = [(loc.x, loc.y) for loc in world.locations if loc.kingdom == kingdom_name]
    if not mine:
        return []
    if len(mine) < 3:
        cx = sum(p[0] for p in mine) / len(mine)
        cy = sum(p[1] for p in mine) / len(mine)
        return [(cx + 12 * math.cos(math.radians(a)), cy + 12 * math.sin(math.radians(a)))
                for a in range(0, 360, 45)]
    hull = convex_hull(mine)
    cx = sum(p[0] for p in hull) / len(hull)
    cy = sum(p[1] for p in hull) / len(hull)
    expanded = []
    for (px, py) in hull:
        dx = px - cx
        dy = py - cy
        dist = math.hypot(dx, dy) or 1.0
        nx = cx + dx * 1.35 + dx / dist * 5.0
        ny = cy + dy * 1.35 + dy / dist * 5.0
        expanded.append((max(1.0, min(99.0, nx)), max(1.0, min(99.0, ny))))
    # Subdivide: insert each edge midpoint, pushed slightly outward,
    # so the stroked polygon reads smooth rather than triangular.
    smooth = []
    n = len(expanded)
    for i in range(n):
        p = expanded[i]
        q = expanded[(i + 1) % n]
        smooth.append(p)
        mx = (p[0] + q[0]) / 2.0
        my = (p[1] + q[1]) / 2.0
        dx = mx - cx
        dy = my - cy
        dist = math.hypot(dx, dy) or 1.0
        smooth.append((mx + dx / dist * 2.0, my + dy / dist * 2.0))
    return smooth


# ---------------------------------------------------------------- links

def compute_map_links(world):
    """The white link graph: capital<->each of its locations, each
    location to its nearest same-kingdom neighbour, capitals to the
    nearest foreign capital, and short cross-kingdom links (< 34 units).
    Returns a sorted list of (name_a, name_b, is_cross)."""
    links = set()
    locs = list(world.locations)
    by_kingdom = {}
    for loc in locs:
        by_kingdom.setdefault(loc.kingdom, []).append(loc)
    capitals = {}
    for loc in locs:
        if loc.kind == "Capital":
            capitals[loc.kingdom] = loc

    def add(a, b):
        if a.name == b.name:
            return
        key = tuple(sorted([a.name, b.name]))
        links.add((key[0], key[1], a.kingdom != b.kingdom))

    for kingdom_name, mine in by_kingdom.items():
        cap = capitals.get(kingdom_name)
        for loc in mine:
            if cap is not None:
                add(cap, loc)
            nearest = None
            nd = None
            for other in mine:
                if other is loc:
                    continue
                d = math.hypot(loc.x - other.x, loc.y - other.y)
                if nd is None or d < nd:
                    nd = d
                    nearest = other
            if nearest is not None:
                add(loc, nearest)
    for loc in locs:
        nearest = None
        nd = None
        for other in locs:
            if other.kingdom == loc.kingdom:
                continue
            d = math.hypot(loc.x - other.x, loc.y - other.y)
            if nd is None or d < nd:
                nd = d
                nearest = other
        if nearest is not None and nd is not None and nd < 34.0:
            add(loc, nearest)
    caps = list(capitals.values())
    for cap in caps:
        nearest = None
        nd = None
        for other in caps:
            if other is cap:
                continue
            d = math.hypot(cap.x - other.x, cap.y - other.y)
            if nd is None or d < nd:
                nd = d
                nearest = other
        if nearest is not None:
            add(cap, nearest)
    return sorted(links)


# ---------------------------------------------------------------- tokens

def person_initials(name):
    parts = [w for w in str(name).split() if w.lower() != "the"]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if parts:
        return parts[0][:2].upper()
    return "??"


TOKEN_OFFSETS = [(-30, 20), (30, 20), (-30, 44), (30, 44), (0, 52), (-52, 32), (52, 32)]


def tokens_at(world, loc):
    """Portrait tokens standing on a location: living agents whose home
    or current scheme is here (purple ring), living heroes hunting from
    here (gold/red ring). Returns dicts with pixel offsets."""
    out = []
    for a in world.agents:
        if a.alive and (a.home == loc.name or a.scheme_loc == loc.name):
            out.append({"kind": "agent", "name": a.name,
                        "initials": person_initials(a.name), "ring": "#b366ff",
                        "fill": "#241333"})
    for h in world.heroes:
        if h.alive and h.home == loc.name:
            out.append({"kind": "hero", "name": h.name + ", " + h.kind,
                        "initials": person_initials(h.name), "ring": "#e5484d",
                        "fill": "#33140f"})
    for i, tok in enumerate(out):
        dx, dy = TOKEN_OFFSETS[i % len(TOKEN_OFFSETS)]
        tok["dx"] = dx
        tok["dy"] = dy
    return out


# ---------------------------------------------------------------- masks / stats

def awakening_percent(world):
    # Awakening % = average of seals progress and world Enshadow:
    # how close the god is to waking, in one honest number.
    seals_pct = (sum(1 for s in world.seals if s) / 3.0) * 100.0
    return int(round((seals_pct + world.world_enshadow()) / 2.0))


def mask_percent(world, loc, mode):
    """The % shown on a location's shield badge in a view-mask mode."""
    if mode == "Enshadow":
        return int(clamp(getattr(loc, "enshadow", 0)))
    if mode == "Clues":
        return int(clamp(getattr(loc, "clues", 0)))
    return None


def scheme_clue_estimate(scheme_key):
    """Profile/Menace analogue for a scheme: its expected clue footprint,
    risk x 4 (risk is 1-3 in the engine, so this reads 4 / 8 / 12)."""
    s = SCHEMES.get(scheme_key)
    if s is None:
        return 0
    return int(s["risk"]) * 4


def power_cost(world, power_key):
    cost = POWERS[power_key]["cost"]
    if world.god_key == "1" and power_key == "3":
        cost = cost // 2
    return cost


def action_rows(world, loc):
    """Right-panel ACTIONS list data for a location: schemes first, then
    powers, in the engine's own order. Pure logic - no Tk."""
    rows = []
    for key in sorted(SCHEMES.keys()):
        s = SCHEMES[key]
        rows.append({"type": "scheme", "key": key, "name": s["name"],
                     "detail": "Risk: " + str(s["risk"]) + "  Clues: +" + str(scheme_clue_estimate(key)),
                     "sub": s["desc"], "color": "#4b2066"})
    for key in sorted(POWERS.keys()):
        p = POWERS[key]
        rows.append({"type": "power", "key": key, "name": p["name"],
                     "detail": "Cost: " + str(power_cost(world, key)) + " Power",
                     "sub": p["desc"], "color": "#27436e"})
    return rows


# ---------------------------------------------------------------- tiles

def generate_tile_grid(loc):
    """Deterministic 18x12 tile grid for a location, seeded by its name,
    kingdom and kind. Pure logic - no Tk, stable across runs/machines."""
    seed = veilfall._name_seed(loc.name + "|" + loc.kingdom + "|" + loc.kind)
    rng = random.Random(seed)
    grid = [["." for _ in range(TILE_COLS)] for _ in range(TILE_ROWS)]
    if loc.kind == "Port":
        for y in range(TILE_ROWS):
            for x in range(TILE_COLS - 3, TILE_COLS):
                grid[y][x] = "~"
    road_y = TILE_ROWS // 2
    road_x = TILE_COLS // 2 - 2
    for x in range(TILE_COLS):
        if grid[road_y][x] != "~":
            grid[road_y][x] = "="
    for y in range(TILE_ROWS):
        if grid[y][road_x] != "~":
            grid[y][road_x] = "="
    for y in range(TILE_ROWS - 4, TILE_ROWS - 1):
        for x in range(1, 4):
            grid[y][x] = "G"
    grid[2][3] = "S"
    if loc.kind == "Abbey":
        grid[2][4] = "S"
        grid[3][3] = "S"
        grid[3][4] = "S"
    houses = {"Capital": 10, "Town": 7, "Abbey": 4, "Port": 7, "Village": 4}.get(loc.kind, 6)
    placed = 0
    tries = 0
    while placed < houses and tries < 200:
        tries += 1
        x = road_x + rng.randint(-4, 4)
        y = road_y + rng.randint(-3, 3)
        if 0 <= x < TILE_COLS and 0 <= y < TILE_ROWS and grid[y][x] == ".":
            grid[y][x] = "H"
            placed += 1
    for _ in range(16):
        x = rng.randrange(TILE_COLS)
        y = rng.randrange(TILE_ROWS)
        if grid[y][x] == ".":
            grid[y][x] = "T"
    return ["".join(row) for row in grid]


def tile_appearance(loc, tile, x, y):
    """(fill, glyph, glyph_colour) for one tile, reflecting location state."""
    seed = veilfall._name_seed(loc.name)
    v = (x * 37 + y * 91 + seed) % 100
    en = getattr(loc, "enshadow", 0)
    creep = v < en * 0.6
    if tile == "G" and getattr(loc, "undead", 0) > 0 and (x + y) % 2 == 0:
        return ("#4c4750", "U", "#d8d3e0")
    if tile == "S" and getattr(loc, "devotion", 50) < 35:
        return ("#2a0f0f", "x", "#c0392b")
    if tile == "H" and getattr(loc, "plague", 0) > 0 and (x + y) % 3 == 0:
        return ("#4d621f", "+", "#b6ff5e")
    if tile == "H" and getattr(loc, "cult", 0) > 0 and (x * 7 + y) % 6 == 0:
        return ("#3a2140", "o", "#d9a0ff")
    base = {
        ".": ("#57683a" if v % 3 else "#4d5f34", "", "#000000"),
        "T": ("#3d5228", "T", "#8fbf6a"),
        "=": ("#7a6748", "=", "#a68d5f"),
        "~": ("#274b63", "~", "#7fb6d9"),
        "H": ("#6e5136", "H", "#e8cf9f"),
        "S": ("#8a7433", "+", "#ffe98a"),
        "G": ("#5b5b52", "g", "#cfccc0"),
        "U": ("#4c4750", "U", "#d8d3e0"),
    }
    fill, glyph, colour = base.get(tile, ("#444444", tile, "#ffffff"))
    if creep and tile in (".", "T"):
        fill = "#33203f"
        if tile == ".":
            glyph = "."
            colour = "#7a4d99"
    return (fill, glyph, colour)


# ---------------------------------------------------------------- actions
# Thin GUI wrappers over the same rules/costs as veilfall.do_* (which are
# bound to input()). Each returns a human-readable result string.

def gui_whisper(world, loc):
    chance = 0.55 + (0.15 if world.god_key == "2" else 0) - loc.devotion / 400.0
    if random.random() < chance:
        a = Agent(loc.notable, loc.name)
        world.agents.append(a)
        loc.notable = person_name()
        loc.shadow = clamp(loc.shadow + 10)
        world.log("You whisper to " + a.name + " in " + loc.name + ". They listen. They do not sleep again, but they listen. (" + a.trait + "; wants " + a.ambition + ")")
        return "Recruited: " + a.name + " (" + a.trait + ", skill " + str(a.skill) + ", wants " + a.ambition + ")"
    loc.clues = clamp(loc.clues + 5)
    world.log("You whisper to " + loc.notable + " in " + loc.name + ". They run to a priest instead. A clue is born.")
    return "They refused, and told a priest. +Clues in " + loc.name + "."


def gui_start_scheme(world, agent, scheme_key, loc):
    if agent is None or not agent.alive or agent.scheme is not None:
        return "Pick an idle, living agent first."
    if scheme_key not in SCHEMES:
        return "Pick a scheme first."
    cost = 2 if (world.god_key == "1" and scheme_key == "5") else 5
    if world.power < cost:
        return "Not enough Power (need " + str(cost) + ")."
    world.power -= cost
    agent.scheme = scheme_key
    agent.scheme_loc = loc.name
    agent.scheme_left = SCHEMES[scheme_key]["turns"]
    agent.home = loc.name
    return agent.name + " begins: " + SCHEMES[scheme_key]["name"] + " in " + loc.name + "."


def gui_cast_power(world, power_key, loc):
    if power_key not in POWERS:
        return "Pick a power first."
    cost = POWERS[power_key]["cost"]
    if world.god_key == "1" and power_key == "3":
        cost = cost // 2
    if world.power < cost:
        return "Not enough Power (have " + str(world.power) + ", need " + str(cost) + ")."
    world.power -= cost
    if power_key == "6":
        for other in world.locations:
            other.enshadow = clamp(other.enshadow + 7)
            other.clues = clamp(other.clues + 5)
            other.devotion = clamp(other.devotion - 5)
        world.log("ECLIPSE. For one day the sun does not rise. Every field, every altar, every face turns up at a black sky.")
        return "The sun goes out for a day. (Everywhere)"
    if power_key == "1":
        loc.plague = 3
        loc.clues = clamp(loc.clues + 6)
        world.log("You breathe plague into " + loc.name + ".")
        return "Plague breathed into " + loc.name + "."
    if power_key == "2":
        amt = 18 if world.god_key == "4" else 12
        loc.devotion = clamp(loc.devotion - amt)
        loc.shadow = clamp(loc.shadow + amt)
        world.log("All of " + loc.name + " dreams the same dream: you, at the foot of every bed.")
        return "Nightmares over " + loc.name + "."
    if power_key == "3":
        n = random.randint(15, 40)
        loc.undead += n
        loc.enshadow = clamp(loc.enshadow + 12)
        loc.clues = clamp(loc.clues + 12)
        world.log("CORPSE-HOST: " + str(n) + " dead stand up in " + loc.name + " at your word.")
        return str(n) + " dead stand up in " + loc.name + "."
    if power_key == "4":
        k = None
        for cand in world.kingdoms:
            if cand.name == loc.kingdom:
                k = cand
        if k is not None and random.random() < 0.45:
            k.corrupted = True
            world.log("MADNESS TAKES THE THRONE: " + k.ruler + " of " + k.name + " breaks, beautifully, and is yours.")
            return "Madness takes the throne of " + k.name + "."
        loc.unrest = clamp(loc.unrest + 20)
        loc.clues = clamp(loc.clues + 6)
        world.log("Madness blooms in " + loc.name + ". The notable is found laughing in the well.")
        return "Madness blooms in " + loc.name + "."
    if power_key == "5":
        loc.cult = clamp(loc.cult + 20)
        loc.enshadow = clamp(loc.enshadow + 12)
        loc.devotion = clamp(loc.devotion - 8)
        world.log("A DARK MIRACLE in " + loc.name + ": the dead child sits up at her funeral and asks for you by name.")
        return "A dark miracle in " + loc.name + "."
    return "?"


# ---------------------------------------------------------------- Tk app

if tk is not None:

    def serif(size, bold=False):
        return (SERIF, size, "bold") if bold else (SERIF, size)

    class VeilfallApp:
        def __init__(self, root, world):
            self.root = root
            self.world = ensure_map_positions(world)
            self.selected = self.world.locations[0] if self.world.locations else None
            self.mask_mode = "World"
            self.idle_agents = []
            self._status_text = ""
            self.zoom = 1.0
            self.pan_x = 0.0
            self.pan_y = 0.0
            self.hover_loc = None
            self._drag = None
            self._redraw_pending = False
            self.roster_items = []
            root.title("VEILFALL - " + self.world.god + " - Turn " + str(self.world.turn))
            root.geometry("1440x920")
            root.configure(bg=CHROME_BG)

            self.notebook = ttk.Notebook(root)
            self.notebook.pack(fill="both", expand=True)

            # ---------- MAP TAB ----------
            self.map_tab = tk.Frame(self.notebook, bg=CHROME_BG)
            self.notebook.add(self.map_tab, text="World Map")
            # event ticker: one black/gold line under the map (packed
            # first so it docks at the bottom), latest chronicle entry.
            self.ticker = tk.Frame(self.map_tab, bg="#000000", highlightbackground=GOLD,
                                   highlightthickness=1)
            self.ticker.pack(side="bottom", fill="x")
            self.ticker_lbl = tk.Label(self.ticker, text="", bg="#000000", fg=GOLD_LIGHT,
                                       font=serif(9), anchor="w")
            self.ticker_lbl.pack(fill="x", padx=8, pady=3)
            self.ticker.bind("<Button-1>", lambda _e: self.open_chronicle())
            self.ticker_lbl.bind("<Button-1>", lambda _e: self.open_chronicle())
            self.map_canvas = tk.Canvas(self.map_tab, bg="#0d1622", highlightthickness=0)
            self.map_canvas.pack(fill="both", expand=True)
            self.map_canvas.bind("<ButtonPress-1>", self.on_map_press)
            self.map_canvas.bind("<B1-Motion>", self.on_map_drag)
            self.map_canvas.bind("<ButtonRelease-1>", self.on_map_release)
            self.map_canvas.bind("<Motion>", self.on_map_hover)
            self.map_canvas.bind("<Leave>", lambda _e: self.clear_hover())
            self.map_canvas.bind("<MouseWheel>", self.on_map_wheel)
            self.map_canvas.bind("<Button-4>", self.on_map_wheel)
            self.map_canvas.bind("<Button-5>", self.on_map_wheel)
            self.map_canvas.bind("<Configure>", lambda _e: self.draw_map())

            # god panel, top-left
            self.god_panel = tk.Frame(self.map_tab, bg=PANEL_BG, highlightbackground=GOLD,
                                      highlightthickness=1)
            self.god_panel.place(x=10, y=10, width=276)
            self.god_name_lbl = tk.Label(self.god_panel, text="", bg=PANEL_BG, fg=GOLD_LIGHT,
                                         font=serif(13, True), anchor="w", wraplength=264)
            self.god_name_lbl.pack(anchor="w", padx=8, pady=(6, 0))
            self.god_stats_lbl = tk.Label(self.god_panel, text="", bg=PANEL_BG, fg="#cfc39f",
                                          font=serif(10), anchor="w", justify="left")
            self.god_stats_lbl.pack(anchor="w", padx=8, pady=(0, 6))
            self.banner_lbl = tk.Label(self.god_panel, text="", bg=PANEL_BG, fg="#ff6b6b",
                                       font=serif(11, True), anchor="w")
            self.banner_lbl.pack(anchor="w", padx=8)

            # selected-location panel, left under god panel
            self.loc_panel = tk.Frame(self.map_tab, bg=PANEL_BG, highlightbackground=GOLD,
                                      highlightthickness=1)
            self.loc_panel.place(x=10, y=158, width=276)
            self.loc_name_lbl = tk.Label(self.loc_panel, text="", bg=PANEL_BG, fg=GOLD,
                                         font=serif(15, True), anchor="w", wraplength=264)
            self.loc_name_lbl.pack(anchor="w", padx=8, pady=(6, 0))
            self.loc_sub_lbl = tk.Label(self.loc_panel, text="", bg=PANEL_BG, fg="#9d9276",
                                        font=serif(9), anchor="w", wraplength=264)
            self.loc_sub_lbl.pack(anchor="w", padx=8)
            self.stats_frame = tk.Frame(self.loc_panel, bg=PANEL_BG)
            self.stats_frame.pack(fill="x", padx=8, pady=4)
            self.loc_people = tk.Text(self.loc_panel, height=6, wrap="word", bg="#0a0a0e",
                                      fg="#d9cfa8", font=serif(9), relief="flat")
            self.loc_people.pack(fill="x", padx=8, pady=2)
            tk.Label(self.loc_panel, text="AGENT FOR SCHEMES", bg=PANEL_BG, fg=GOLD,
                     font=serif(8, True), anchor="w").pack(anchor="w", padx=8)
            self.agent_var = tk.StringVar()
            self.agent_box = ttk.Combobox(self.loc_panel, textvariable=self.agent_var, state="readonly")
            self.agent_box.pack(fill="x", padx=8, pady=(0, 4))
            tk.Label(self.loc_panel, text="MINIONS", bg=PANEL_BG, fg=GOLD,
                     font=serif(8, True), anchor="w").pack(anchor="w", padx=8)
            self.roster_canvas = tk.Canvas(self.loc_panel, height=64, bg="#0a0a0e",
                                           highlightbackground="#2c2c30", highlightthickness=1)
            self.roster_canvas.pack(fill="x", padx=8, pady=(0, 2))
            self.roster_canvas.bind("<Button-1>", self.on_roster_click)
            self.hunters_lbl = tk.Label(self.loc_panel, text="", bg=PANEL_BG, fg="#e0a8a0",
                                        font=serif(8), anchor="w")
            self.hunters_lbl.pack(anchor="w", padx=8, pady=(0, 2))
            row = tk.Frame(self.loc_panel, bg=PANEL_BG)
            row.pack(fill="x", padx=8, pady=(0, 8))
            tk.Button(row, text="Watch 12 Months", command=self.act_watch, bg="#241d33",
                      fg="#f0e6c8", font=serif(9)).pack(side="left", fill="x", expand=True, padx=(0, 4))
            tk.Button(row, text="Save", command=self.act_save, bg="#241d33",
                      fg="#f0e6c8", font=serif(9)).pack(side="left", fill="x", expand=True)

            # turn panel, top-right
            self.turn_panel = tk.Frame(self.map_tab, bg=PANEL_BG, highlightbackground=GOLD,
                                       highlightthickness=1)
            self.turn_panel.place(relx=1.0, x=-10, y=10, anchor="ne", width=250)
            self.turn_lbl = tk.Label(self.turn_panel, text="", bg=PANEL_BG, fg=GOLD_LIGHT,
                                     font=serif(14, True), anchor="e")
            self.turn_lbl.pack(anchor="e", padx=8, pady=(6, 0))
            self.turn_stats_lbl = tk.Label(self.turn_panel, text="", bg=PANEL_BG, fg="#cfc39f",
                                           font=serif(10), anchor="e", justify="right")
            self.turn_stats_lbl.pack(anchor="e", padx=8, pady=(0, 6))

            # actions + threats panel, right
            self.actions_panel = tk.Frame(self.map_tab, bg=PANEL_BG, highlightbackground=GOLD,
                                          highlightthickness=1)
            self.actions_panel.place(relx=1.0, x=-10, y=140, anchor="ne", width=296)
            tk.Label(self.actions_panel, text="ACTIONS", bg=PANEL_BG, fg=GOLD,
                     font=serif(13, True)).pack(pady=(6, 0))
            tk.Label(self.actions_panel, text="Actions at the selected location.\nClick a row to begin it.",
                     bg=PANEL_BG, fg="#c9a86a", font=serif(8), justify="center").pack()
            self.rows_frame = tk.Frame(self.actions_panel, bg=PANEL_BG)
            self.rows_frame.pack(fill="x", padx=6, pady=4)
            tk.Label(self.actions_panel, text="THREATS", bg=PANEL_BG, fg=GOLD,
                     font=serif(12, True)).pack(pady=(4, 0))
            self.threats_text = tk.Text(self.actions_panel, height=6, wrap="word", bg="#0a0a0e",
                                        fg="#e0b0a8", font=serif(9), relief="flat")
            self.threats_text.pack(fill="x", padx=6, pady=(0, 8))

            # bottom-left controls (Shadows layout)
            self.controls = tk.Frame(self.map_tab, bg=PANEL_BG, highlightbackground=GOLD,
                                     highlightthickness=1)
            self.controls.place(x=10, rely=1.0, y=-10, anchor="sw")
            self.end_turn_btn = tk.Button(self.controls, text="END TURN", command=self.act_advance,
                                          bg="#8c1414", fg="#ffe9c9", font=serif(14, True),
                                          width=11, height=2, activebackground="#b02020")
            self.end_turn_btn.grid(row=0, column=0, rowspan=2, padx=6, pady=6)
            tk.Button(self.controls, text="USE POWER", command=self.open_power_chooser,
                      bg="#3d1663", fg="#ecd9ff", font=serif(11, True), width=13).grid(row=0, column=1, padx=(0, 6), pady=(6, 2))
            tk.Button(self.controls, text="CREATE AGENT", command=self.act_whisper,
                      bg="#16355e", fg="#d3e6ff", font=serif(11, True), width=13).grid(row=1, column=1, padx=(0, 6), pady=(2, 6))

            # view-mask toggle, bottom centre
            self.mask_bar = tk.Frame(self.map_tab, bg=PANEL_BG, highlightbackground=GOLD,
                                     highlightthickness=1)
            self.mask_bar.place(relx=0.5, rely=1.0, y=-10, anchor="s")
            tk.Label(self.mask_bar, text="MASK:", bg=PANEL_BG, fg=GOLD,
                     font=serif(10, True)).pack(side="left", padx=(8, 2), pady=4)
            self.mask_btns = {}
            for mode in ("World", "Enshadow", "Clues"):
                b = tk.Button(self.mask_bar, text=mode.upper(), font=serif(10, True),
                              command=lambda m=mode: self.set_mask(m))
                b.pack(side="left", padx=2, pady=4)
                self.mask_btns[mode] = b

            # status line, bottom-right
            self.status = tk.Label(self.map_tab, text="", bg=PANEL_BG, fg="#9fe89f",
                                   font=serif(10), wraplength=380, justify="right",
                                   highlightbackground=GOLD, highlightthickness=1)
            self.status.place(relx=1.0, x=-10, rely=1.0, y=-40, anchor="se")

            # zoom controls, top centre
            self.view_bar = tk.Frame(self.map_tab, bg=PANEL_BG, highlightbackground=GOLD,
                                     highlightthickness=1)
            self.view_bar.place(relx=0.5, y=10, anchor="n")
            tk.Label(self.view_bar, text="VIEW:", bg=PANEL_BG, fg=GOLD,
                     font=serif(9, True)).pack(side="left", padx=(6, 2), pady=3)
            tk.Button(self.view_bar, text="-", command=self.zoom_out, bg="#241d33",
                      fg="#f0e6c8", font=serif(10, True), width=2).pack(side="left", padx=1, pady=3)
            tk.Button(self.view_bar, text="+", command=self.zoom_in, bg="#241d33",
                      fg="#f0e6c8", font=serif(10, True), width=2).pack(side="left", padx=1, pady=3)
            tk.Button(self.view_bar, text="RESET VIEW", command=self.reset_view, bg="#241d33",
                      fg="#f0e6c8", font=serif(9, True)).pack(side="left", padx=(1, 6), pady=3)

            # hover tooltip (hidden until a marker is hovered)
            self.tooltip = tk.Label(self.map_tab, text="", bg="#000000", fg=GOLD_LIGHT,
                                    font=serif(9), justify="left", anchor="w",
                                    highlightbackground=GOLD, highlightthickness=1, padx=6, pady=3)

            # ---------- TILE TAB ----------
            tile_tab = tk.Frame(self.notebook, bg=CHROME_BG)
            self.notebook.add(tile_tab, text="Location (Ruinarch)")
            self.tile_title = tk.Label(tile_tab, text="", bg=CHROME_BG, fg=GOLD,
                                       font=serif(14, True))
            self.tile_title.pack(anchor="w", padx=10, pady=(8, 0))
            self.tile_canvas = tk.Canvas(tile_tab, width=720, height=480, bg="#101010",
                                         highlightthickness=1, highlightbackground=GOLD)
            self.tile_canvas.pack(padx=10, pady=8, anchor="w")
            tk.Label(tile_tab, text=LEGEND_TEXT, bg=CHROME_BG, fg="#cbbf9f",
                     justify="left", font=serif(9)).pack(anchor="w", padx=10)

            # ---------- CHRONICLE TAB ----------
            chron_tab = tk.Frame(self.notebook, bg=CHROME_BG)
            self.chron_tab = chron_tab
            self.notebook.add(chron_tab, text="Chronicle")
            self.chronicle_text = tk.Text(chron_tab, wrap="word", bg="#0a0a0e",
                                          fg="#d9cfa8", font=serif(10))
            self.chronicle_text.pack(fill="both", expand=True, padx=8, pady=8)

            self.notebook.bind("<<NotebookTabChanged>>", lambda _e: self.refresh())
            root.bind_all("<space>", self.on_key_space)
            root.bind_all("<KeyPress-w>", self.on_key_watch)
            root.bind_all("<KeyPress-W>", self.on_key_watch)
            root.bind_all("<Escape>", self.on_key_escape)
            self.refresh()

        # ----- view transform -----
        def _canvas_size(self):
            w = max(200, self.map_canvas.winfo_width())
            h = max(200, self.map_canvas.winfo_height())
            return w, h

        def _transform(self):
            w, h = self._canvas_size()
            return make_view_transform(w, h, self.zoom, self.pan_x, self.pan_y)

        def _view(self):
            """(w, h, transform) for the current canvas size + pan/zoom."""
            w, h = self._canvas_size()
            return w, h, self._transform()

        def _zoom_factor(self):
            """Marker/font scale factor: current zoom, gently clamped so
            ribbons stay readable at the extremes."""
            return max(0.65, min(2.0, self.zoom))

        def to_px(self, loc):
            return view_to_px(self._transform(), loc.x, loc.y)

        def _xy(self, ux, uy):
            return view_to_px(self._transform(), ux, uy)

        def _schedule_redraw(self):
            if self._redraw_pending:
                return
            self._redraw_pending = True

            def _do():
                self._redraw_pending = False
                self.draw_map()
                self.draw_hover_halo()

            self.root.after(16, _do)

        # ----- drawing -----
        def draw_map(self):
            if not hasattr(self, "map_canvas"):
                return
            c = self.map_canvas
            c.delete("all")
            w, h, t = self._view()
            dim = self.mask_mode != "World"
            c.create_rectangle(0, 0, w, h, fill="#0a141f", outline="")
            # hex terrain, full-bleed, with Enshadow creep in the fill
            mx0, _my0 = view_to_map(t, 0, 0)
            mx1, _my1 = view_to_map(t, w, h)
            for (col, row, cx, cy, terrain, variant) in hex_grid(self.world, mx0 - 8, mx1 + 8):
                pts = []
                for (ux, uy) in hex_corners(cx, cy):
                    px, py = self._xy(ux, uy)
                    pts.extend([px, py])
                c.create_polygon(pts, fill=hex_display_fill(self.world, cx, cy, terrain, variant, dim),
                                 outline="#060a10" if not dim else "#04070b", width=1)
                self.draw_terrain_detail(col, row, cx, cy, terrain, dim)
            # political borders: glowing multi-stroke hull per kingdom
            for kingdom in self.world.kingdoms:
                border = kingdom_border_points(self.world, kingdom.name)
                if len(border) < 3:
                    continue
                pts = []
                for (ux, uy) in border:
                    px, py = self._xy(ux, uy)
                    pts.extend([px, py])
                glow = kingdom_glow(self.world, kingdom.name)
                base = kingdom_color(self.world, kingdom.name)
                c.create_polygon(pts, fill="", outline="#000000", width=10, joinstyle="round")
                c.create_polygon(pts, fill="", outline=base, width=7, joinstyle="round")
                c.create_polygon(pts, fill="", outline=glow, width=3, joinstyle="round")
                c.create_polygon(pts, fill="", outline="#f5ecd2", width=1, joinstyle="round")
            # white link graph
            loc_by_name = {}
            for loc in self.world.locations:
                loc_by_name[loc.name] = loc
            selected_names = set()
            if self.selected is not None:
                selected_names.add(self.selected.name)
            for (na, nb, cross) in compute_map_links(self.world):
                a = loc_by_name.get(na)
                b = loc_by_name.get(nb)
                if a is None or b is None:
                    continue
                x1, y1 = self.to_px(a)
                x2, y2 = self.to_px(b)
                hot = na in selected_names or nb in selected_names
                c.create_line(x1, y1, x2, y2, fill=GOLD if hot else "#cfd4d8",
                              width=2 if hot else 1)
            # green scheme/planning path of the picked agent (Shadows green)
            try:
                picked = self._picked_agent()
            except Exception:
                picked = None
            for (la, lb) in green_paths(self.world, self.selected, picked):
                x1, y1 = self.to_px(la)
                x2, y2 = self.to_px(lb)
                c.create_line(x1, y1, x2, y2, fill="#123d22", width=5)
                c.create_line(x1, y1, x2, y2, fill="#39d353", width=2, dash=(7, 4), arrow="last")
            # locations, tokens, banners
            for loc in self.world.locations:
                self.draw_location(loc)
            for loc in self.world.locations:
                self.draw_tokens(loc)
            # mask badges on top
            if dim:
                for loc in self.world.locations:
                    self.draw_mask_badge(loc)
            self._draw_halo_items()
            self.draw_vignette(w, h)

        def draw_terrain_detail(self, col, row, cx, cy, terrain, dim=False):
            c = self.map_canvas
            scale = self._transform()[0]
            for mark in terrain_detail(self.world, col, row, cx, cy, terrain):
                kind = mark["kind"]
                if kind == "tree":
                    x, y = self._xy(mark["x"], mark["y"])
                    s = mark["s"] * scale
                    c.create_polygon(x, y - 1.7 * s, x - 1.1 * s, y + 0.6 * s,
                                     x + 1.1 * s, y + 0.6 * s,
                                     fill="#16290f" if dim else "#20381a",
                                     outline="#0a1806", width=1)
                    c.create_line(x, y + 0.6 * s, x, y + 1.3 * s,
                                  fill="#3a2a16", width=max(1, int(scale * 0.22)))
                elif kind == "wave":
                    pts = []
                    for (ux, uy) in mark["pts"]:
                        px, py = self._xy(ux, uy)
                        pts.extend([px, py])
                    c.create_line(pts, fill="#1d3247" if dim else "#4a7ca3", width=1, smooth=True)
                elif kind == "peak":
                    x, y = self._xy(mark["x"], mark["y"])
                    s = mark["s"] * scale
                    c.create_line(x - s, y + 0.7 * s, x, y - 0.8 * s, x + s, y + 0.7 * s,
                                  fill="#efe8cc", width=1)
                elif kind == "dot":
                    x, y = self._xy(mark["x"], mark["y"])
                    c.create_oval(x - 1.6, y - 1.6, x + 1.6, y + 1.6,
                                  fill="#e8f2f5", outline="")

        def _draw_halo_items(self):
            """Bright gold halo around the hovered location (tag-managed,
            so hover motion never needs a full redraw)."""
            c = self.map_canvas
            c.delete("hover_halo")
            loc = self.hover_loc
            if loc is None:
                return
            x, y = self.to_px(loc)
            zf = self._zoom_factor()
            r = 26 * zf
            c.create_oval(x - r, y - r, x + r, y + r, outline="#ffe98a", width=3, tags="hover_halo")
            c.create_oval(x - r - 5, y - r - 5, x + r + 5, y + r + 5,
                          outline=GOLD, width=1, tags="hover_halo")

        def draw_hover_halo(self):
            self._draw_halo_items()

        def draw_vignette(self, w, h):
            """Layered dark edge lines - Tk has no alpha, so the vignette
            is faked with nested outline rectangles of decreasing weight."""
            c = self.map_canvas
            for (inset, width, colour) in [(0, 16, "#000000"), (12, 8, "#04050a"),
                                           (20, 5, "#080a0f"), (26, 3, "#0e1118")]:
                c.create_rectangle(inset, inset, w - inset, h - inset,
                                   outline=colour, width=width)

        def draw_location(self, loc):
            c = self.map_canvas
            x, y = self.to_px(loc)
            zf = self._zoom_factor()
            selected = self.selected is loc
            is_cap = loc.kind == "Capital"
            glow = kingdom_glow(self.world, loc.kingdom)
            if selected:
                sr = 24 * zf
                c.create_oval(x - sr, y - sr, x + sr, y + sr, outline=GOLD_LIGHT, width=3)
                c.create_oval(x - sr - 5, y - sr - 5, x + sr + 5, y + sr + 5, outline=GOLD, width=1)
            r = (15 if is_cap else 12) * zf
            # shield: hexagon with a pointed bottom, soft drop shadow first
            pts = [x - r, y - r, x + r, y - r, x + r, y + r * 0.35,
                   x, y + r * 1.45, x - r, y + r * 0.35]
            shadow_pts = [v + (4 if i % 2 == 0 else 5) for i, v in enumerate(pts)]
            c.create_polygon(shadow_pts, fill="#000000", stipple="gray50", outline="")
            fill = enshadow_color(loc.enshadow)
            outline = GOLD if is_cap else "#d8d8d8"
            c.create_polygon(pts, fill=fill, outline=outline, width=2 if is_cap else 1)
            c.create_text(x, y - 1, text=KIND_GLYPH.get(loc.kind, "?"), fill="#f5ecd2",
                          font=serif(max(7, int(10 * zf)), True))
            # black ribbon name banner (with its own soft shadow)
            label = loc.name.upper()
            tw = (7.2 * len(label) + 12) * zf
            by = y + r * 1.45 + 3
            bh = 14 * zf
            c.create_rectangle(x - tw / 2 + 3, by + 3, x + tw / 2 + 3, by + bh + 3,
                               fill="#000000", stipple="gray50", outline="")
            c.create_rectangle(x - tw / 2, by, x + tw / 2, by + bh, fill="#000000", outline="#2c2c30")
            c.create_text(x, by + bh / 2, text=label, fill="#e8ddba",
                          font=serif(max(6, int(7 * zf))))
            # state badges (corners of the shield)
            if loc.plague > 0:
                c.create_oval(x + r - 2, y - r - 8, x + r + 10, y - r + 4, fill="#2e6b1e", outline="#ffffff")
                c.create_text(x + r + 4, y - r - 2, text="+", fill="#d8ffb0", font=serif(8, True))
            if loc.cult > 0:
                c.create_oval(x - r - 10, y + r * 0.2, x - r + 2, y + r * 0.2 + 12, fill="#4b2066", outline="#ffffff")
                c.create_text(x - r - 4, y + r * 0.2 + 6, text="o", fill="#e2b6ff", font=serif(8, True))
            if loc.undead > 0:
                c.create_rectangle(x + r - 4, y + r * 0.2, x + r + 14, y + r * 0.2 + 12,
                                   fill="#3c3c44", outline="#9a97a3")
                c.create_text(x + r + 5, y + r * 0.2 + 6, text=str(loc.undead), fill="#e8e6f0", font=serif(7))
            if is_cap:
                self.draw_capital_banner(loc, x, by + bh)

        def draw_capital_banner(self, loc, x, top):
            """Heraldic banner hanging below a capital's name ribbon:
            kingdom colour, pointed tail, original sigil, kingdom label."""
            c = self.map_canvas
            zf = self._zoom_factor()
            colour = kingdom_color(self.world, loc.kingdom)
            sigil = kingdom_sigil(self.world, loc.kingdom)
            bw = 46 * zf
            bh = 52 * zf
            label = ("Kingdom of " + loc.kingdom).upper()
            tw = (6.4 * len(label) + 10) * zf
            c.create_rectangle(x - tw / 2, top + 2, x + tw / 2, top + 15,
                               fill="#000000", outline="#2c2c30")
            c.create_text(x, top + 9, text=label, fill=GOLD_LIGHT, font=serif(7, True))
            pts = [x - bw / 2, top + 17, x + bw / 2, top + 17,
                   x + bw / 2, top + 17 + bh, x, top + 17 + bh - 13 * zf,
                   x - bw / 2, top + 17 + bh]
            shadow_pts = [v + (4 if i % 2 == 0 else 5) for i, v in enumerate(pts)]
            c.create_polygon(shadow_pts, fill="#000000", stipple="gray50", outline="")
            c.create_polygon(pts, fill=colour, outline=GOLD, width=1)
            c.create_text(x, top + 17 + bh / 2 - 4, text=sigil, fill="#f5ecd2",
                          font=serif(max(10, int(20 * zf)), True))

        def draw_tokens(self, loc):
            c = self.map_canvas
            x, y = self.to_px(loc)
            zf = self._zoom_factor()
            for tok in tokens_at(self.world, loc):
                tx = x + tok["dx"] * zf
                ty = y + tok["dy"] * zf
                r = 11 * zf
                c.create_oval(tx - r + 3, ty - r + 4, tx + r + 3, ty + r + 4,
                              fill="#000000", stipple="gray50", outline="")
                c.create_oval(tx - r - 2, ty - r - 2, tx + r + 2, ty + r + 2,
                              outline=tok["ring"], width=3)
                c.create_oval(tx - r, ty - r, tx + r, ty + r, fill=tok["fill"], outline="#000000")
                c.create_text(tx, ty, text=tok["initials"], fill="#f5ecd2",
                              font=serif(max(6, int(8 * zf)), True))

        def draw_mask_badge(self, loc):
            c = self.map_canvas
            x, y = self.to_px(loc)
            pct = mask_percent(self.world, loc, self.mask_mode)
            if pct is None:
                return
            fill = "#5e2a72" if self.mask_mode == "Enshadow" else "#6e1423"
            r = 13
            pts = []
            for i in range(6):
                ang = math.radians(60 * i - 30)
                pts.extend([x + r * math.cos(ang), y - 30 + r * math.sin(ang)])
            c.create_polygon(pts, fill=fill, outline="#000000", width=1)
            c.create_text(x, y - 30, text=str(pct) + "%", fill="#ffffff", font=serif(8, True))

        def draw_tiles(self):
            c = self.tile_canvas
            c.delete("all")
            loc = self.selected
            if loc is None:
                self.tile_title.config(text="")
                return
            self.tile_title.config(text=loc.name.upper() + "  -  " + loc.kind + " of " + loc.kingdom)
            grid = generate_tile_grid(loc)
            ts = 40
            for yy, row in enumerate(grid):
                for xx, tile in enumerate(row):
                    fill, glyph, colour = tile_appearance(loc, tile, xx, yy)
                    x0 = xx * ts
                    y0 = yy * ts
                    c.create_rectangle(x0, y0, x0 + ts, y0 + ts,
                                       fill=fill, outline="#0a0a0c")
                    self._draw_tile_shape(c, loc, tile, glyph, colour, x0, y0, ts)
                    # state glyphs stay on top of the shapes
                    if glyph in ("U", "+", "x", "o", "."):
                        c.create_text(x0 + ts - 9, y0 + 10, text=glyph,
                                      fill=colour, font=serif(12, True))

        def _draw_tile_shape(self, c, loc, tile, glyph, colour, x0, y0, ts):
            """Render-layer shapes per tile type (v0.4): the grid and the
            state logic are untouched - this only draws prettier tiles."""
            cx = x0 + ts // 2
            cy = y0 + ts // 2
            if tile == "H":
                # house: wall rectangle + roof triangle + door
                c.create_polygon(x0 + 6, y0 + 17, x0 + ts - 6, y0 + 17, cx, y0 + 5,
                                 fill="#5a3220", outline="#2e1a0e")
                c.create_rectangle(x0 + 10, y0 + 17, x0 + ts - 10, y0 + ts - 5,
                                   fill="#8a6a44", outline="#4a3520")
                c.create_rectangle(cx - 3, y0 + ts - 15, cx + 3, y0 + ts - 5,
                                   fill="#3a2412", outline="")
            elif tile == "T":
                foliage = "#3f6126"
                # enshadow creep recolors the field fill; match the tree too
                fill_now, _g, _col = tile_appearance(loc, tile, x0 // ts, y0 // ts)
                if fill_now == "#33203f":
                    foliage = "#3a2145"
                c.create_rectangle(cx - 2, cy + 4, cx + 2, y0 + ts - 6,
                                   fill="#4a3418", outline="")
                c.create_polygon(cx, y0 + 4, x0 + 9, cy + 8, x0 + ts - 9, cy + 8,
                                 fill=foliage, outline="#22331a")
                c.create_polygon(cx, y0 + 12, x0 + 12, cy + 13, x0 + ts - 12, cy + 13,
                                 fill=foliage, outline="#22331a")
            elif tile == "S":
                if glyph == "x":
                    # desecrated: broken pillars and a fallen lintel
                    c.create_line(x0 + 11, y0 + ts - 6, x0 + 15, y0 + 14, fill="#8a7433", width=4)
                    c.create_line(x0 + ts - 11, y0 + ts - 6, x0 + ts - 17, y0 + 18, fill="#8a7433", width=4)
                    c.create_line(x0 + 9, y0 + ts - 10, x0 + ts - 9, y0 + ts - 17, fill="#6e5a28", width=4)
                else:
                    # shrine: two pillars + lintel
                    c.create_rectangle(x0 + 10, y0 + 13, x0 + 16, y0 + ts - 6,
                                       fill="#cbb26a", outline="#6e5a28")
                    c.create_rectangle(x0 + ts - 16, y0 + 13, x0 + ts - 10, y0 + ts - 6,
                                       fill="#cbb26a", outline="#6e5a28")
                    c.create_rectangle(x0 + 7, y0 + 7, x0 + ts - 7, y0 + 13,
                                       fill="#e3cd85", outline="#6e5a28")
            elif tile == "~":
                for wy in (cy - 7, cy + 5):
                    pts = []
                    for i in range(5):
                        pts.extend([x0 + 6 + i * 7, wy + (3 if i % 2 else -3)])
                    c.create_line(pts, fill=colour, width=2, smooth=True)
            elif tile == "G":
                # gravestone: slab with a rounded top
                c.create_arc(x0 + 12, y0 + 7, x0 + ts - 12, y0 + 23,
                             start=0, extent=180, fill="#8b897e", outline="#55534a")
                c.create_rectangle(x0 + 12, y0 + 15, x0 + ts - 12, y0 + ts - 7,
                                   fill="#8b897e", outline="#55534a")
                c.create_line(x0 + 17, y0 + 22, x0 + ts - 17, y0 + 22, fill="#55534a", width=1)
            elif tile == "=":
                c.create_line(x0 + 3, cy, x0 + ts - 3, cy, fill="#a68d5f",
                              width=2, dash=(5, 4))
                c.create_line(cx, y0 + 3, cx, y0 + ts - 3, fill="#a68d5f",
                              width=1, dash=(5, 4))
            elif tile == ".":
                if glyph == ".":
                    for (dx, dy) in [(10, 12), (24, 26), (30, 10)]:
                        c.create_oval(x0 + dx - 2, y0 + dy - 2, x0 + dx + 2, y0 + dy + 2,
                                      fill="#7a4d99", outline="")
                elif (x0 // ts * 13 + y0 // ts * 7) % 5 == 0:
                    c.create_line(x0 + 12, y0 + ts - 9, x0 + 15, y0 + ts - 16,
                                  fill="#6d8148", width=2)
                    c.create_line(x0 + 26, y0 + ts - 9, x0 + 29, y0 + ts - 15,
                                  fill="#6d8148", width=2)

        # ----- refresh -----
        def refresh(self):
            w = self.world
            living = len([a for a in w.agents if a.alive])
            broken = sum(1 for s in w.seals if s)
            self.god_name_lbl.config(text=w.god.upper())
            self.god_stats_lbl.config(
                text="POWER: " + str(w.power) +
                     "\nSEALS BROKEN: " + str(broken) + " OF 3" +
                     "\nAGENTS: " + str(living) + " living")
            self.banner_lbl.config(text=("*** " + w.ended + " ***") if w.ended else "")
            self.root.title("VEILFALL - " + w.god + " - Turn " + str(w.turn))
            self.ticker_lbl.config(text=latest_chronicle_text(w))
            self.turn_lbl.config(text="TURN: " + str(w.turn))
            self.turn_stats_lbl.config(
                text="WORLD AWARENESS: " + str(w.awareness) + "%" +
                     "\nAWAKENING: " + str(awakening_percent(w)) + "%" +
                     "\nYear " + str(w.turn // 12 + 1) + ", Month " + str(w.turn % 12 + 1))
            for mode, btn in self.mask_btns.items():
                active = mode == self.mask_mode
                btn.config(bg="#5e2a72" if active else "#241d33", fg="#ffffff" if active else "#cbbf9f")
            self.refresh_location_panel()
            self.refresh_actions()
            self.draw_map()
            self.draw_tiles()
            self.chronicle_text.delete("1.0", "end")
            self.chronicle_text.insert("1.0", "\n".join(w.chronicle))
            self.chronicle_text.see("end")
            if self._status_text:
                self.status.config(text=self._status_text)

        def refresh_location_panel(self):
            w = self.world
            loc = self.selected
            for child in self.stats_frame.winfo_children():
                child.destroy()
            self.loc_people.delete("1.0", "end")
            # preserve the chosen agent across refreshes when possible
            prev = self.agent_var.get()
            self.idle_agents = [a for a in w.agents if a.alive and a.scheme is None]
            self.agent_box["values"] = [a.name + " (" + a.trait + ", skill " + str(a.skill) + ")"
                                        for a in self.idle_agents]
            names = [a.name for a in self.idle_agents]
            if prev.split(" (")[0] in names:
                self.agent_box.current(names.index(prev.split(" (")[0]))
            elif self.idle_agents:
                self.agent_box.current(0)
            else:
                self.agent_var.set("")
            if loc is None:
                self.loc_name_lbl.config(text="NO LOCATION")
                self.loc_sub_lbl.config(text="")
                self.draw_roster()
                return
            kingdom = None
            for k in w.kingdoms:
                if k.name == loc.kingdom:
                    kingdom = k
            self.loc_name_lbl.config(text=loc.name.upper())
            self.loc_sub_lbl.config(text=loc.kind + " of " + loc.kingdom +
                                    ("  -  " + kingdom_sigil(w, loc.kingdom) if kingdom else ""))
            stats = [("Population", loc.population), ("Devotion", loc.devotion),
                     ("Shadow", loc.shadow), ("Enshadow", loc.enshadow),
                     ("Clues", loc.clues), ("Unrest", loc.unrest),
                     ("Cult", loc.cult), ("Undead", loc.undead)]
            for i, (label, value) in enumerate(stats):
                tk.Label(self.stats_frame, text=label, bg=PANEL_BG, fg="#9d9276",
                         font=serif(9), anchor="w").grid(row=i // 2, column=(i % 2) * 2, sticky="w", pady=1)
                tk.Label(self.stats_frame, text=str(value), bg=PANEL_BG, fg="#f0e6c8",
                         font=serif(9, True), anchor="e").grid(row=i // 2, column=(i % 2) * 2 + 1, sticky="e", padx=(2, 10), pady=1)
            lines = []
            if kingdom is not None:
                lines.append("Ruler: " + kingdom.ruler + " (" + kingdom.ruler_trait +
                             ", " + str(kingdom.ruler_age) + ")" +
                             (" - CORRUPTED" if kingdom.corrupted else "") +
                             (" - at war with " + kingdom.at_war_with if kingdom.at_war_with else ""))
            lines.append("Notable: " + loc.notable + " (" + loc.notable_trait + ")")
            for tok in tokens_at(w, loc):
                lines.append(("Agent: " if tok["kind"] == "agent" else "HUNTER: ") + tok["name"])
            for a in w.agents:
                if not a.alive and (a.home == loc.name or a.scheme_loc == loc.name):
                    lines.append("Agent lost here: " + a.name)
            self.loc_people.insert("1.0", "\n".join(lines))
            self.draw_roster()

        def draw_roster(self):
            """The MINIONS strip: one portrait token per living agent.
            Busy agents are grey-ringed with their turns-left beneath."""
            c = self.roster_canvas
            c.delete("all")
            self.roster_items = []
            entries = roster_entries(self.world)
            self.hunters_lbl.config(text="Hunters in the field: " + str(hunter_count(self.world)) +
                                    ("   -   click a minion to go to them" if entries else ""))
            if not entries:
                c.create_text(8, 32, text="No agents yet - CREATE AGENT whispers for one.",
                              fill="#9d9276", font=serif(8), anchor="w")
                return
            for i, e in enumerate(entries):
                cx = 30 + i * 56
                cy = 24
                r = 15
                c.create_oval(cx - r + 2, cy - r + 3, cx + r + 2, cy + r + 3,
                              fill="#000000", stipple="gray50", outline="")
                c.create_oval(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2,
                              outline=e["ring"], width=3)
                c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=e["fill"], outline="#000000")
                c.create_text(cx, cy, text=e["initials"], fill="#f5ecd2", font=serif(9, True))
                label = e["name"].split()[0][:9]
                if e["busy"]:
                    label += " " + str(e["turns_left"]) + "t"
                c.create_text(cx, cy + r + 10, text=label,
                              fill="#8f887a" if e["busy"] else "#d9cfa8", font=serif(7))
                self.roster_items.append((cx - 26, 2, cx + 26, 62, e["name"]))

        def on_roster_click(self, event):
            for (x1, y1, x2, y2, name) in self.roster_items:
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    self.select_agent(name)
                    return

        def select_agent(self, name):
            """Roster click: choose the agent (if idle) and pan/select
            the location they stand on."""
            agent = None
            for a in self.world.agents:
                if a.alive and a.name == name:
                    agent = a
                    break
            if agent is None:
                return
            loc = agent_location(self.world, agent)
            if loc is not None:
                self.selected = loc
                self.center_on(loc.x, loc.y)
            idle_names = [a.name for a in self.idle_agents]
            if agent.name in idle_names:
                self.agent_box.current(idle_names.index(agent.name))
                self._status_text = "Agent chosen: " + agent.name
            elif agent.scheme is not None:
                self._status_text = (agent.name + " is busy: " +
                                     SCHEMES[agent.scheme]["name"] + " (" +
                                     str(agent.scheme_left) + " turns left)")
            self.status.config(text=self._status_text)
            self.refresh()

        def center_on(self, ux, uy):
            w, h = self._canvas_size()
            self.pan_x, self.pan_y = pan_to_center(self._transform(), w, h, ux, uy, self.zoom)

        def refresh_actions(self):
            for child in self.rows_frame.winfo_children():
                child.destroy()
            loc = self.selected
            if loc is None:
                return
            current_section = None
            for rowdata in action_rows(self.world, loc):
                section = "SCHEMES" if rowdata["type"] == "scheme" else "POWERS"
                if section != current_section:
                    current_section = section
                    tk.Label(self.rows_frame, text=section, bg=PANEL_BG, fg=GOLD_LIGHT,
                             font=serif(9, True), anchor="w").pack(anchor="w", pady=(4, 1))
                self._action_row(rowdata)
            # threats
            w = self.world
            lines = ["World Awareness: " + str(w.awareness) + "%"]
            if w.awareness >= 80:
                lines.append("THE HOLY ALLIANCE HAS FORMED.")
            elif w.awareness >= 55:
                lines.append("The churches are comparing notes.")
            elif w.awareness >= 30:
                lines.append("Someone is asking questions.")
            alive_heroes = [hh for hh in w.heroes if hh.alive]
            if not alive_heroes:
                lines.append("No hunters in the field yet.")
            for hh in alive_heroes:
                lines.append(hh.name + ", " + hh.kind + " - hunting from " + hh.home)
            self.threats_text.delete("1.0", "end")
            self.threats_text.insert("1.0", "\n".join(lines))

        def _action_row(self, rowdata):
            frame = tk.Frame(self.rows_frame, bg="#181820", highlightbackground="#2c2c30",
                             highlightthickness=1)
            frame.pack(fill="x", pady=1)
            icon = tk.Label(frame, text="", bg=rowdata["color"], width=2)
            icon.pack(side="left", fill="y")
            tk.Label(frame, text=rowdata["name"], bg="#181820", fg=GOLD_LIGHT,
                     font=serif(9, True), anchor="w").pack(side="left", padx=4)
            tk.Label(frame, text=rowdata["detail"], bg="#181820", fg="#b8ad8f",
                     font=serif(8), anchor="e").pack(side="right", padx=4)
            handler = lambda _e, r=rowdata: self.run_action_row(r)
            for widget in (frame, icon):
                widget.bind("<Button-1>", handler)
            for widget in frame.winfo_children():
                widget.bind("<Button-1>", handler)

        def run_action_row(self, rowdata):
            if self.selected is None:
                return
            if rowdata["type"] == "scheme":
                self._status_text = gui_start_scheme(self.world, self._picked_agent(),
                                                     rowdata["key"], self.selected)
            else:
                self._status_text = gui_cast_power(self.world, rowdata["key"], self.selected)
            self.refresh()

        # ----- interaction -----
        def _select_radius(self):
            return max(24.0, 42.0 * self._zoom_factor())

        def on_map_press(self, event):
            self._drag = {"x": event.x, "y": event.y, "pan_x": self.pan_x,
                          "pan_y": self.pan_y, "moved": False}

        def on_map_drag(self, event):
            if self._drag is None:
                return
            dx = event.x - self._drag["x"]
            dy = event.y - self._drag["y"]
            if abs(dx) + abs(dy) > 4:
                self._drag["moved"] = True
            if self._drag["moved"]:
                w, h = self._canvas_size()
                self.pan_x = max(-w, min(w, self._drag["pan_x"] + dx))
                self.pan_y = max(-h, min(h, self._drag["pan_y"] + dy))
                self._schedule_redraw()

        def on_map_release(self, event):
            drag = self._drag
            self._drag = None
            if drag is not None and drag["moved"]:
                self.draw_map()
                self.draw_hover_halo()
                return
            # a plain click: select the location under the cursor
            loc = location_at_point(self.world, self._transform(), event.x, event.y,
                                    self._select_radius())
            if loc is not None:
                self.selected = loc
                self._status_text = ""
                self.status.config(text="")
                self.refresh()

        def on_map_hover(self, event):
            loc = location_at_point(self.world, self._transform(), event.x, event.y,
                                    self._select_radius())
            if loc is not self.hover_loc:
                self.hover_loc = loc
                self.draw_hover_halo()
                if loc is not None:
                    self.tooltip.config(text=tooltip_text(loc))
                    self.tooltip.place(x=event.x + 18, y=event.y + 20)
                else:
                    self.tooltip.place_forget()
            elif loc is not None:
                self.tooltip.place(x=event.x + 18, y=event.y + 20)

        def clear_hover(self):
            self.hover_loc = None
            if hasattr(self, "map_canvas"):
                self.map_canvas.delete("hover_halo")
            if hasattr(self, "tooltip"):
                self.tooltip.place_forget()

        def on_map_wheel(self, event):
            delta = 0
            if getattr(event, "delta", 0):
                delta = 1 if event.delta > 0 else -1
            elif getattr(event, "num", None) == 4:
                delta = 1
            elif getattr(event, "num", None) == 5:
                delta = -1
            if delta:
                self.zoom_at(event.x, event.y, 1.12 if delta > 0 else 1 / 1.12)

        def zoom_at(self, px, py, factor):
            """Zoom toward the cursor: the map point under (px, py) stays
            under (px, py) after the zoom."""
            t = self._transform()
            ux, uy = view_to_map(t, px, py)
            self.zoom = max(0.6, min(3.0, self.zoom * factor))
            w, h = self._canvas_size()
            t2 = make_view_transform(w, h, self.zoom, self.pan_x, self.pan_y)
            nx, ny = view_to_px(t2, ux, uy)
            self.pan_x += px - nx
            self.pan_y += py - ny
            self.draw_map()
            self.draw_hover_halo()

        def zoom_in(self):
            w, h = self._canvas_size()
            self.zoom_at(w // 2, h // 2, 1.25)

        def zoom_out(self):
            w, h = self._canvas_size()
            self.zoom_at(w // 2, h // 2, 1 / 1.25)

        def reset_view(self):
            self.zoom = 1.0
            self.pan_x = 0.0
            self.pan_y = 0.0
            self.draw_map()
            self.draw_hover_halo()

        def open_chronicle(self):
            self.notebook.select(self.chron_tab)

        # ----- keys -----
        def _typing_focus(self):
            try:
                focus = self.root.focus_get()
            except Exception:
                return False
            if focus is None:
                return False
            return focus.winfo_class() in ("Entry", "TEntry", "Text", "TCombobox", "Button", "TButton")

        def on_key_space(self, _event):
            if self._typing_focus():
                return
            self.act_advance()
            return "break"

        def on_key_watch(self, _event):
            if self._typing_focus():
                return
            self.act_watch()
            return "break"

        def on_key_escape(self, _event):
            self.selected = None
            self.clear_hover()
            self.refresh()
            return "break"

        def set_mask(self, mode):
            self.mask_mode = mode
            self.refresh()

        def _picked_agent(self):
            idx = self.agent_box.current()
            if 0 <= idx < len(self.idle_agents):
                return self.idle_agents[idx]
            if self.idle_agents:
                return self.idle_agents[0]
            return None

        # ----- actions -----
        def act_whisper(self):
            if self.selected is not None:
                self._status_text = gui_whisper(self.world, self.selected)
            self.refresh()

        def act_power_via(self, power_key):
            if self.selected is not None:
                self._status_text = gui_cast_power(self.world, power_key, self.selected)
            self.refresh()

        def open_power_chooser(self):
            if self.selected is None:
                return
            win = tk.Toplevel(self.root)
            win.title("Use Power on " + self.selected.name)
            win.configure(bg=PANEL_BG)
            tk.Label(win, text="USE POWER", bg=PANEL_BG, fg=GOLD,
                     font=serif(13, True)).pack(padx=12, pady=(10, 2))
            tk.Label(win, text="Target: " + self.selected.name + "  -  Power available: " + str(self.world.power),
                     bg=PANEL_BG, fg="#cfc39f", font=serif(9)).pack(padx=12)
            var = tk.StringVar(value=sorted(POWERS.keys())[0])
            for key in sorted(POWERS.keys()):
                p = POWERS[key]
                text = p["name"] + " (" + str(power_cost(self.world, key)) + " Power) - " + p["desc"]
                tk.Radiobutton(win, text=text, variable=var, value=key, bg=PANEL_BG,
                               fg="#e8d9a0", selectcolor="#33284a", justify="left",
                               font=serif(9), wraplength=420, anchor="w").pack(anchor="w", padx=12, pady=2)

            def cast():
                self.act_power_via(var.get())
                win.destroy()

            tk.Button(win, text="Cast", command=cast, bg="#3d1663", fg="#ecd9ff",
                      font=serif(11, True)).pack(pady=10)

        def act_advance(self):
            self.world.step_turn()
            self._status_text = "A month passes. (END TURN)"
            self.refresh()

        def act_watch(self):
            for _ in range(12):
                self.world.step_turn()
                if self.world.ended:
                    break
            self._status_text = "Twelve months roll by. The world did things."
            self.refresh()

        def act_save(self):
            save_world(self.world)
            self._status_text = "Saved to world.pkl"
            self.refresh()

    def choose_god(root):
        """Four presentation cards, one per god: sigil swatch, gold name,
        title, description, gift. Clicking a card chooses that god."""
        cards = god_card_data()
        win = tk.Toplevel(root)
        win.title("Choose the god you are")
        win.configure(bg=CHROME_BG)
        var = tk.StringVar(value=cards[0]["key"])
        tk.Label(win, text="CHOOSE THE GOD YOU ARE", bg=CHROME_BG, fg=GOLD_LIGHT,
                 font=serif(16, True)).pack(pady=(12, 2))
        tk.Label(win, text="Click a card to begin, sealed.", bg=CHROME_BG, fg="#9d9276",
                 font=serif(9)).pack(pady=(0, 8))
        grid = tk.Frame(win, bg=CHROME_BG)
        grid.pack(padx=12, pady=(0, 12))

        def choose(key):
            var.set(key)
            win.destroy()

        for i, card in enumerate(cards):
            frame = tk.Frame(grid, bg=PANEL_BG, highlightbackground=card["accent"],
                             highlightthickness=1, width=300, height=238)
            frame.grid(row=i // 2, column=i % 2, padx=6, pady=6)
            frame.pack_propagate(False)
            swatch = tk.Frame(frame, bg=card["color"], height=64)
            swatch.pack(fill="x")
            swatch.pack_propagate(False)
            tk.Label(swatch, text=card["sigil"], bg=card["color"], fg=card["accent"],
                     font=serif(30, True)).pack(pady=6)
            tk.Label(frame, text=card["name"].upper(), bg=PANEL_BG, fg=GOLD_LIGHT,
                     font=serif(12, True), wraplength=280, justify="center").pack(pady=(8, 0))
            tk.Label(frame, text=card["title"], bg=PANEL_BG, fg="#c9a86a",
                     font=serif(9), wraplength=280, justify="center").pack()
            tk.Label(frame, text=card["desc"], bg=PANEL_BG, fg="#cfc39f",
                     font=serif(9), wraplength=280, justify="center").pack(pady=(6, 2))
            tk.Label(frame, text=card["gift"], bg=PANEL_BG, fg="#9fe8c9",
                     font=serif(8), wraplength=280, justify="center").pack()
            widgets = [frame, swatch] + frame.winfo_children() + swatch.winfo_children()
            for widget in widgets:
                widget.bind("<Button-1>", lambda _e, k=card["key"]: choose(k))
            win.bind("<KeyPress-" + card["key"] + ">", lambda _e, k=card["key"]: choose(k))
        root.wait_window(win)
        return var.get()

    def main(argv=None):
        if argv is None:
            argv = sys.argv[1:]
        if tk is None:
            print("Tkinter is not available in this Python install.")
            print("On Windows, the standard python.org installer includes it - reinstall with tcl/tk ticked.")
            return 1
        root = tk.Tk()
        root.withdraw()
        world = None
        save_exists = os.path.exists(veilfall.SAVE_PATH)
        if "--continue" in argv and save_exists:
            world = ensure_map_positions(veilfall.load_world())
        elif save_exists and messagebox.askyesno("VEILFALL", "A saved world exists. Continue it?"):
            world = ensure_map_positions(veilfall.load_world())
        if world is None:
            world = World(choose_god(root))
        root.deiconify()
        VeilfallApp(root, world)
        root.mainloop()
        return 0

else:  # no Tk: keep a main() that explains, so imports/tests still work

    def main(argv=None):
        print("Tkinter is not available in this Python install.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

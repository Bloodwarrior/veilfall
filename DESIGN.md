# VEILFALL (working title) — Design v0.1
A sealed-god game in the niche of Shadow Behind the Throne, Ruinarch,
Shadows of Forbidden Gods, and That Which Sleeps.

Rename it whenever. The name is a placeholder, not a decision.

## What the four reference games actually share

| Game | The piece we steal |
|---|---|
| That Which Sleeps | You are a sealed Old One. The world is fully simulated *without* you. You spend scarce influence through agents, you must manage *clues* — if the world figures out you exist and unites, you lose. Prophecies, mutually hostile kingdoms you keep divided. A chronicle ending. |
| Shadows of Forbidden Gods | Turn-based map of locations. Agents with traits run multi-turn *schemes* (infiltrate, corrupt, desecrate). Each location tracks Shadow / Enshadowment. Holy orders, heroes and a rising Awareness fight back. Different gods = different playstyles. |
| Shadow Behind the Throne | Political manipulation over raw destruction: corrupt the ruler, the court follows, the kingdom follows. Power is indirect and deniable. |
| Ruinarch | The toy-box side: direct, cruel, funny god powers you can drop on a living sim *right now* — plague, madness, raising the dead — even when the long game doesn't need them. |

## Fitted to how Aidan actually plays

1. **Observer-first.** The world ticks without you. Kingdoms feud, rulers die,
   heroes are born, churches schism — whether you touch anything or not.
   Press Watch and a decade rolls by. Intervention is optional, always.
2. **You wield power personally.** This is not a management sandbox.
   Schemes are the slow knife; Powers are your own hand — cast directly,
   costs Power, leaves clues.
3. **No rival god.** No other god competing for a scoreboard. The opposition
   is mortal: churches, inquisitors, heroes, and kingdoms uniting once
   they understand. That is the That Which Sleeps shape.
4. **Agents are people, not tokens.** Names, traits, ambitions, fear,
   loyalty that can crack. An idle agent does not wait — they pursue
   their own ambition inside your cult, for better and worse.
5. **The clue economy is the game.** Every dark act risks Evidence.
   Evidence raises Awareness. Awareness founds inquisitions, spawns
   heroes, and finally forges the Holy Alliance. Play loud and fast
   (Ruinarch) or silent and slow (That Which Sleeps) — both are viable,
   they are different games.
6. **A chronicle, not a score screen.** Win or lose, the game ends by
   telling the story of what happened, year by year, cause linked to cause.

## Core loop

```
Choose a Sealed God (4 in v0.1, each changes the game, not just stats)
  -> World is generated: 4 kingdoms, 12 locations, rulers, churches, heroes yet unborn
  -> Each turn = 1 month
       1. World acts on its own (politics, war, faith, death, birth of notables)
       2. Your agents progress their schemes (or act on their own ambition)
       3. Counterplay reacts to clues (investigations, purges, hero quests)
       4. You act: whisper to a mortal / start a scheme / cast a power / or Watch
  -> Break the Three Seals to Awaken and win:
       Seal I   — fully Enshadow one kingdom's capital
       Seal II  — corrupt or kill every ruler of one kingdom / corrupt a ruler outright
       Seal III — raise Enshadow across the world past the threshold
     …before Awareness reaches 100 and the Holy Alliance seals you forever.
  -> Sandbox continues after either ending if you want it to.
```

## Systems in v0.1 (playable now)

- Procedural world: kingdom / location / ruler / notable generation
- 4 gods: Devouring Maw, Whispering Saint, Drowned King, Hollow Child
- Agents: recruitment by Whisper, traits, loyalty, ambition-driven autonomy
- 7 schemes: Infiltrate Court, Spread Cult, Desecrate Shrine, Corrupt Ruler,
  Raise the Dead, Incite Rebellion, Forge Prophecy
- 6 direct powers: Plague, Nightmares, Corpse-Host, Tempt Madness,
  Dark Miracle, Eclipse
- Location state: Devotion, Shadow, Enshadow, Clues, Unrest, Plague, Undead
- Global state: Power (resource), Awareness, Seals, Holy Alliance, heroes/inquisitors
- Autonomous world simulation between your actions
- Chronicle log + end-of-game chronicle, save/load, headless `--auto N` watch mode

## Graphics (v0.2, reworked in v0.3)

- Locations now carry deterministic map coordinates (`x`/`y`, 0–100):
  each kingdom occupies a quadrant, its capital at the region centre,
  the other locations ringed around it (`assign_map_positions` in
  `veilfall.py`). v0.1 saves have no coordinates — the GUI generates
  the layout on load (`ensure_map_positions` in `veilfall_gui.py`).
- `veilfall_gui.py` (Tkinter, stdlib only; launch `play_gui.py` /
  `play_gui.bat`) has three tabs: World Map, Location, Chronicle.
- **v0.3 world map — modelled on Shadows of Forbidden Gods screenshots
  (all art original, drawn in Canvas code):**
  - Full-bleed pointy-top **hex terrain**: dark blue sea far from any
    location, snow in the north (cy ≤ 15), forest/plains/hills near
    locations by stable hash (`terrain_for_hex` / `hex_grid`).
  - Locations are **shield icons** (fill slides gold→purple-black with
    Enshadow) over **black ribbon name banners** in small caps, joined
    by a **white link graph** (`compute_map_links`: capital links,
    nearest-neighbour links, cross-kingdom links under 34 units,
    capital-to-capital links).
  - **Political borders**: Shadows traces hex edges; we approximate
    honestly with a glowing multi-stroke outline (black under-stroke,
    kingdom colour, bright glow, pale core) around an expanded,
    subdivided convex hull of the kingdom's locations
    (`kingdom_border_points`).
  - **Capitals** wear a vertical **heraldic banner** in the kingdom
    colour with an original sigil glyph (◆ ☾ ✦ ♠, derived from kingdom
    order — never stored on pickled objects) and a "KINGDOM OF X" plate.
  - **People as portrait tokens**: agents (purple ring) and hunters
    (red ring) stand at their location as circles with initials,
    stacked on fixed offsets (`tokens_at`).
  - **Black + gold chrome**: god panel top-left (god, POWER, SEALS
    BROKEN n OF 3, AGENTS n living); turn panel top-right (TURN,
    WORLD AWARENESS %, AWAKENING % — defined as the average of seals
    progress % and world Enshadow %, see `awakening_percent`);
    selected-location panel left (big gold serif name, stat grid,
    ruler/notable/agent rows, agent chooser, Watch + Save); ACTIONS
    panel right (schemes show "Risk: n  Clues: +n" — clues = risk×4 —
    powers show "Cost: n Power"; clicking a row runs it) with a
    THREATS section under it; big red **END TURN** bottom-left with
    purple USE POWER (opens a power chooser) and blue CREATE AGENT
    (= Whisper at the selected location); **view-mask toggle**
    World / Enshadow / Clues (mask modes dim the terrain and badge
    each location with that stat's % shield, like Shadows'
    Modifier Finder).
  - The **Ruinarch-style location view** (deterministic 18×12 tile
    grid per location whose tiles reflect undead, plague, desecration,
    cult and Enshadow state; view-only for now) and the Chronicle tab
    are kept, recoloured to the same black/gold chrome.
  - Generation logic is kept Tk-free so it can be tested headless;
    sigils/terrain/borders are all derived from names/positions, so
    pre-v0.3 saves need no new fields.
- The text game is unchanged (VERSION 0.3) and shares the same save.

## Graphics polish (v0.4)

A feel pass only — no engine rules changed (veilfall.py: VERSION 0.4).
All new maths is in Tk-free helpers in `veilfall_gui.py`:

- **Pan + zoom** via a pure view transform `(scale, ox, oy)`
  (`make_view_transform` / `view_to_px` / `view_to_map`): drag pans,
  the wheel zooms toward the cursor (the map point under the cursor
  stays put), +/- and Reset View buttons, `pan_to_center` for jumps.
  Click and hover both resolve through `location_at_point(world,
  transform, px, py, radius)`, so they stay accurate at any zoom/pan;
  marker sizes/fonts scale with a clamped zoom factor so name ribbons
  stay readable.
- **Hover**: gold halo (tag-managed canvas items — no full redraw on
  mouse motion) plus a black/gold tooltip (`tooltip_text`: kind,
  kingdom, Enshadow/Clues/Devotion).
- **Terrain detail** (`terrain_detail`, seeded by world signature +
  hex col/row): 1–3 tree triangles per forest hex, wave squiggles on
  sea, a peak mark on hills, sparkle dots on snow; plains stay clean.
- **Enshadow hex creep** (`enshadow_at_point` / `hex_display_fill`):
  each hex blends its terrain colour toward the deep purple-black of
  `enshadow_color(100)` by the strongest nearby location's Enshadow —
  full within 8 map units, zero past 22 — in World mask mode too, so
  corruption visibly eats the map.
- **Depth**: soft drop shadows (offset black, `gray50` stipple) under
  shields, capital banners and portrait tokens; layered dark edge
  rectangles fake a vignette (Tk has no alpha); a dashed green line
  (`green_paths`) joins the picked agent, their scheme target and the
  selected location, like Shadows' green agent paths.
- **Event ticker**: one black/gold line docked under the map showing
  `latest_chronicle_text` (the last chronicle entry); clicking it
  opens the Chronicle tab.
- **Agent roster**: a MINIONS strip in the left panel (`roster_entries`:
  living agents as initial tokens, purple ring idle / grey ring busy
  with turns-left under), plus a hunters-in-the-field count. Clicking
  a token selects the agent in the chooser (when idle), selects their
  location and pans the view to it.
- **Tile view shapes**: render-layer only — houses get walls + roof,
  trees a trunk + canopy, the shrine pillars + lintel (broken lines
  when desecrated), water gets wave lines, gravestones a rounded slab;
  the state glyphs (U / + / x / o / creep dots) draw on top.
  `generate_tile_grid` / `tile_appearance` are untouched.
- **God chooser cards** (`god_card_data`): four cards with a big sigil
  on a per-god colour swatch (Maw Ψ bone/moss, Saint ✝ candle gold,
  Drowned King ♚ deep teal, Hollow Child ☽ charcoal violet), gold
  name, title, description and gift; click (or press 1–4) to choose.
- **Keys**: Space = END TURN, W = Watch 12, Esc = clear selection
  (all ignored while typing in a field or when a button has focus, so
  Space never double-fires a focused button). The window title shows
  god + turn.

## Deliberately NOT in yet (next, in rough order)

- Tile-level gameplay in the location view (it is a view in v0.2)
- Agent-to-agent relationships / cult internal schisms (scaffolded by traits)
- Named holy orders with their own politics, prophecy deck, bloodlines
- God-specific win paths per god, mod/content packs

## Tech rules (same as AEGIS, because they worked)

- Pure Python, stdlib only. No dependencies, no API key.
- Python >= 3.9 compatible — must run on Aidan's Python 3.11 on Windows.
- No curses. Plain `input()` menus, ANSI only where safe.
- One save file (`world.pkl`), `--continue` to resume, `--auto N` to watch/test.

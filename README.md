# VEILFALL (working title)

A sealed-god game in the niche of *Shadow Behind the Throne*, *Ruinarch*,
*Shadows of Forbidden Gods*, and *That Which Sleeps*.

You are a god sealed outside the world. You cannot walk in it.
You whisper to mortals, run schemes through them, and — when you must —
reach in directly with plague, nightmares, madness and eclipses.
Break the Three Seals and Awaken. Or be discovered, named, and sealed
forever by a world that finally unites against you.

Or do nothing. The world runs either way.

## Play

```
python3 play.py              # text game: new game
python3 play.py --continue   # text game: resume
python3 play.py --auto 240   # watch mode: 240 months, god-AI plays, chronicle prints
python3 play_gui.py          # graphical game (Tkinter): new game or continue a save
python3 play_gui.py --continue
```

On Windows: double-click `play.bat` (text) or `play_gui.bat` (graphics).

Pure Python, standard library only — the GUI uses Tkinter, which ships
with the standard python.org Windows installer. No dependencies, no API key.
Python 3.9 or newer.

## The two map views (GUI)

- **World Map (Shadows-style, reworked in v0.3):** a full-bleed hex
  terrain map — dark blue sea, green forest/plains land, snow in the
  north — with the locations as shield icons on black ribbon name
  banners, joined by a white link graph (within and between kingdoms).
  Each kingdom's territory is outlined by a glowing border in its own
  heraldic colour, and each capital wears a hanging banner with the
  kingdom's sigil. Agents and hunters stand on the map as circular
  portrait tokens (purple ring = your agents, red ring = hunters).
  Black-and-gold chrome frames it: your god and Power top-left, Turn /
  World Awareness / Awakening top-right, the selected location's stats
  on the left, a clickable ACTIONS list (plus a THREATS section) on the
  right, a big red END TURN button bottom-left next to USE POWER and
  CREATE AGENT, and a World / Enshadow / Clues view-mask toggle that
  dims the terrain and badges every location with that stat's %.
- **Location view (Ruinarch-style):** the selected place as an 18x12 tile
  grid — fields, houses, shrine/abbey, graveyard, roads, trees, water at
  ports — generated deterministically from the place itself, so it is the
  same every visit. Since v0.4 the tiles are drawn as shapes (roofed
  houses, pillar shrines, wavy water, gravestones) with the state marks
  on top. The tiles react to the sim: gravestones stand up as
  undead (U) when the dead rise, houses turn plague-green, the shrine
  breaks when Desecrated/Devotion falls, purple Enshadow creeps across
  the fields, and cult households appear. View only in this version —
  no tile gameplay yet.

**v0.4 polish on the world map:** drag to pan, mouse-wheel to zoom
toward the cursor (+/- and Reset View buttons too); hover a location
for a gold halo and a tooltip; the terrain itself is decorated (trees,
waves, peaks, snow sparkle) and Enshadow visibly *creeps* across the
hexes around corrupted places; shadows under shields, banners and
tokens; a green path line for your chosen agent; an event ticker under
the map with the latest chronicle entry (click it for the Chronicle);
a MINIONS roster strip — click an agent to jump to them; the god
chooser is now four presentation cards. Keys: **Space** = END TURN,
**W** = Watch 12 months, **Esc** = clear selection.

Saves are shared between the text and GUI versions (`world.pkl`);
v0.1 saves without map coordinates load fine — positions are generated
for them on load.

## How it plays

- **Whisper** to a location's notable to recruit them as an agent.
  Agents have a trait, a skill, and an ambition of their own — idle
  agents pursue that ambition without you.
- **Schemes** (multi-turn, agent-run): Infiltrate Court, Spread Cult,
  Desecrate Shrine, Corrupt Ruler, Raise the Dead, Incite Rebellion,
  Forge Prophecy.
- **Powers** (direct, costly, loud): Plague, Nightmares, Corpse-Host,
  Tempt Madness, Dark Miracle, Eclipse.
- Everything dark leaves **Clues**. Clues raise **Awareness**.
  Awareness spawns inquisitors and heroes who investigate, purge
  cults, and take your agents — and at 100, the Holy Alliance seals
  you forever.
- **Three Seals:** enshadow a capital completely; corrupt a ruler;
  enshadow the world itself past 45%. Break all three to Awaken.

See `DESIGN.md` for the full design and what comes next.

## Status

v0.4 — playable prototype. Text interface plus a Tkinter GUI whose
world map is modelled on Shadows of Forbidden Gods (hex terrain,
ribbon name banners, glowing political borders, capital banners,
portrait tokens, black/gold chrome, view masks) and a Ruinarch-style
tile view of each location; v0.4 added pan/zoom, hover tooltips,
terrain detail, Enshadow hex creep, drop shadows, the event ticker,
the agent roster, tile shapes and god cards. Procedural world
(4 kingdoms, 12 locations), 4 playable gods, save/load shared between
both interfaces, chronicle. All art is original and drawn in code.

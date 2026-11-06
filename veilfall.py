"""VEILFALL - a sealed-god game. Pure Python stdlib. Python 3.9+.
You are a god sealed outside the world. Work through agents and schemes,
break the Three Seals and Awaken - before the world learns your name,
unites, and seals you forever. Or just watch. The world runs either way.
"""
import os
import pickle
import random
import sys

VERSION = "0.4"
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world.pkl")

FIRST = ["Aldric", "Berta", "Cassian", "Odile", "Rurik", "Sanna", "Tomas", "Ysolt",
         "Emmerich", "Falka", "Gideon", "Hedwig", "Ivo", "Joscelin", "Kaspar", "Lotte",
         "Marek", "Nessa", "Osric", "Petra", "Quill", "Ragnild", "Sten", "Theda",
         "Ulric", "Vera", "Waldo", "Xenia", "Yorick", "Zelda", "Anselm", "Brunhild"]
LAST = ["the Miller", "Vane", "of the Ford", "Blackwood", "the Lame", "Corvath",
        "Miller", "the Quiet", "Holloway", "Brandt", "the Younger", "Severin",
        "Ashdown", "the Pale", "Kett", "Marlowe", "the Widow", "Ostrov", "Fenn", "Grale"]
KINGDOM_A = ["Val", "Thorn", "Ost", "Bel", "Kar", "Mor", "Fen", "Ald"]
KINGDOM_B = ["doria", "mark", "gard", "reach", "fell", "heim", "wick", "land"]
PLACE_A = ["Port", "Fort", "San", "Kirch", "Bran", "Ost", "Mil", "Ravens"]
PLACE_B = ["haven", "hold", "minster", "burg", "feld", "wick", "moor", "thorpe"]
TRAITS = ["Ambitious", "Zealous", "Greedy", "Cruel", "Scholarly", "Pious",
          "Paranoid", "Charismatic", "Bitter", "Curious", "Lustful", "Grieving"]
AMBITIONS = ["power", "wealth", "revenge", "forbidden knowledge", "to be loved",
             "to outlive death", "to see the Church fall", "to be remembered"]

GODS = {
    "1": {"name": "The Devouring Maw", "title": "hunger under the earth",
          "gift": "Raise the Dead and Corpse-Host cost half Power. Undead never decay.",
          "desc": "It does not whisper. It waits, mouth open, under every grave."},
    "2": {"name": "The Whispering Saint", "title": "the saint who was never canonised",
          "gift": "Whispers and Corrupt Ruler are far likelier to succeed. Cults spread faster.",
          "desc": "Pilgrims pray to it at a shrine the Church keeps quietly demolishing."},
    "3": {"name": "The Drowned King", "title": "the court beneath the sea",
          "gift": "Plague spreads between ports. Your Power returns faster in grief and flood.",
          "desc": "His kingdom sank in a night. He has been holding court, and his breath, since."},
    "4": {"name": "The Hollow Child", "title": "the child in the empty house",
          "gift": "Nightmares and Tempt Madness are stronger. Heroes fear you: investigations falter.",
          "desc": "Every village has a house nobody will buy. It is standing in the window."},
}

SCHEMES = {
    "1": {"name": "Infiltrate Court", "turns": 3, "risk": 1,
          "desc": "Slip into a ruler's household. +Shadow, opens Corrupt Ruler."},
    "2": {"name": "Spread Cult", "turns": 3, "risk": 1,
          "desc": "Gather worshippers in secret. +Enshadow, +Power each turn after."},
    "3": {"name": "Desecrate Shrine", "turns": 2, "risk": 3,
          "desc": "Ruin a holy place. -Devotion, +Enshadow, loud."},
    "4": {"name": "Corrupt Ruler", "turns": 4, "risk": 2,
          "desc": "Turn the ruler themselves. Needs Shadow here first. Kingdom follows."},
    "5": {"name": "Raise the Dead", "turns": 2, "risk": 3,
          "desc": "The graveyard empties. +Undead, +Enshadow, very loud."},
    "6": {"name": "Incite Rebellion", "turns": 3, "risk": 2,
          "desc": "Feed every grievance. +Unrest; may start a revolt or a war."},
    "7": {"name": "Forge Prophecy", "turns": 3, "risk": 1,
          "desc": "Plant a prophecy of your return. -Awareness effect over time, +cult pull."},
}

POWERS = {
    "1": {"name": "Plague", "cost": 20, "desc": "Sicken a location. Deaths feed you Power."},
    "2": {"name": "Nightmares", "cost": 10, "desc": "A location dreams of you for a month. -Devotion, +Shadow."},
    "3": {"name": "Corpse-Host", "cost": 30, "desc": "Every grave in a location stands up at once."},
    "4": {"name": "Tempt Madness", "cost": 15, "desc": "Break a ruler or notable. Random, sometimes wonderful."},
    "5": {"name": "Dark Miracle", "cost": 15, "desc": "Answer a prayer, monstrously. +Cult, +Enshadow."},
    "6": {"name": "Eclipse", "cost": 40, "desc": "Blot the sun for a day. Everywhere: +Enshadow, +Clues."},
}


def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, int(v)))


def pick(seq):
    return random.choice(seq)


def person_name():
    return pick(FIRST) + " " + pick(LAST)


REGION_CENTERS = [(25, 25), (75, 25), (25, 75), (75, 75)]


def _name_seed(text):
    total = 0
    for i, ch in enumerate(text):
        total += (i + 1) * ord(ch)
    return total


def assign_map_positions(locations, kingdoms):
    """Deterministic 0-100 map layout: each kingdom gets a quadrant,
    its capital sits near the region centre, other locations ring it."""
    for ki, kingdom in enumerate(kingdoms):
        cx, cy = REGION_CENTERS[ki % len(REGION_CENTERS)]
        mine = [x for x in locations if x.kingdom == kingdom.name]
        for j, loc in enumerate(mine):
            if j == 0:
                loc.x = float(cx)
                loc.y = float(cy)
            else:
                angle = (j - 1) * 2.39996  # golden-angle spread, deterministic
                seed = _name_seed(loc.name)
                dist = 11.0 + (seed % 5)
                jitter_x = ((seed // 7) % 5) - 2
                jitter_y = ((seed // 13) % 5) - 2
                import math
                loc.x = float(max(4, min(96, cx + dist * math.cos(angle) + jitter_x)))
                loc.y = float(max(4, min(96, cy + dist * math.sin(angle) + jitter_y)))
    return locations


class Location:
    def __init__(self, name, kind, kingdom):
        self.name = name
        self.kind = kind
        self.kingdom = kingdom
        self.x = 0.0
        self.y = 0.0
        self.population = random.randint(400, 9000)
        self.devotion = random.randint(35, 80)
        self.shadow = 0
        self.enshadow = 0
        self.clues = 0
        self.unrest = random.randint(0, 30)
        self.plague = 0
        self.undead = 0
        self.cult = 0
        self.notable = person_name()
        self.notable_trait = pick(TRAITS)


class Kingdom:
    def __init__(self, name):
        self.name = name
        self.ruler = person_name()
        self.ruler_trait = pick(TRAITS)
        self.ruler_age = random.randint(24, 61)
        self.corrupted = False
        self.dead_ruler_count = 0
        self.at_war_with = None
        self.allied_to_light = False


class Agent:
    def __init__(self, name, home):
        self.name = name
        self.home = home
        self.trait = pick(TRAITS)
        self.ambition = pick(AMBITIONS)
        self.loyalty = random.randint(45, 85)
        self.skill = random.randint(3, 9)
        self.scheme = None
        self.scheme_loc = None
        self.scheme_left = 0
        self.alive = True
        self.captured = False
        self.deeds = 0


class Hero:
    def __init__(self, name, home):
        self.name = name
        self.home = home
        self.kind = pick(["Inquisitor", "Paladin", "Witch-Hunter", "Prophet"])
        self.skill = random.randint(4, 9)
        self.alive = True


class World:
    def __init__(self, god_key, seed=None):
        self.rng_state = None
        self.god_key = god_key
        self.god = GODS[god_key]["name"]
        self.turn = 0
        self.power = 30
        self.awareness = 0
        self.seals = [False, False, False]
        self.kingdoms = []
        self.locations = []
        self.agents = []
        self.heroes = []
        self.chronicle = []
        self.ended = None
        self.prophecy_active = False
        self._gen()

    def _gen(self):
        used = set()
        for _ in range(4):
            while True:
                n = pick(KINGDOM_A) + pick(KINGDOM_B)
                if n not in used:
                    used.add(n)
                    break
            self.kingdoms.append(Kingdom(n))
        kinds = ["Capital", "Town", "Abbey", "Port", "Town", "Village"]
        for k in self.kingdoms:
            for i in range(3):
                kind = kinds[0] if i == 0 else pick(kinds[1:])
                while True:
                    n = pick(PLACE_A) + pick(PLACE_B)
                    if n not in [x.name for x in self.locations]:
                        break
                self.locations.append(Location(n, kind, k.name))
        assign_map_positions(self.locations, self.kingdoms)
        self.log("The world is made, and does not know your name. You are sealed, and patient.")

    def log(self, text):
        entry = "Year " + str(self.turn // 12 + 1) + ", Month " + str(self.turn % 12 + 1) + ": " + text
        self.chronicle.append(entry)

    def loc(self, name):
        for x in self.locations:
            if x.name == name:
                return x
        return None

    def world_enshadow(self):
        if not self.locations:
            return 0
        return sum(x.enshadow for x in self.locations) // len(self.locations)

    # ---------- world acting on its own ----------
    def world_tick(self):
        for k in self.kingdoms:
            k.ruler_age += 0
            if random.random() < 0.008:
                old = k.ruler
                k.ruler = person_name()
                k.ruler_trait = pick(TRAITS)
                k.ruler_age = random.randint(19, 45)
                k.corrupted = False
                k.dead_ruler_count += 1
                self.log("The ruler of " + k.name + ", " + old + ", has died. " + k.ruler + " now reigns.")
            if k.at_war_with is None and random.random() < 0.03:
                other = pick([x for x in self.kingdoms if x.name != k.name])
                k.at_war_with = other.name
                other.at_war_with = k.name
                self.log(k.name + " declares war on " + other.name + ". The world bleeds without your help.")
            elif k.at_war_with and random.random() < 0.08:
                self.log("Peace is made between " + k.name + " and " + k.at_war_with + ".")
                for x in self.kingdoms:
                    if x.name == k.at_war_with:
                        x.at_war_with = None
                k.at_war_with = None
        for loc in self.locations:
            if loc.plague > 0:
                deaths = int(loc.population * 0.02 * loc.plague)
                if deaths > 0:
                    loc.population = max(50, loc.population - deaths)
                    self.power += 1
                    if random.random() < 0.4:
                        self.log("Plague takes " + str(deaths) + " souls in " + loc.name + ". You drink deep.")
                loc.plague = max(0, loc.plague - 1)
            if loc.undead > 0 and self.god_key != "1":
                loc.undead = max(0, loc.undead - random.randint(0, 3))
            if loc.unrest > 70 and random.random() < 0.25:
                loc.unrest = 30
                self.log("REVOLT in " + loc.name + "! The streets rise, banners unknown, prayers unsanctioned.")
                loc.devotion = clamp(loc.devotion - 15)
                loc.enshadow = clamp(loc.enshadow + 8)
            if loc.cult > 0:
                self.power += loc.cult // 10
                loc.enshadow = clamp(loc.enshadow + loc.cult // 12)
            loc.devotion = clamp(loc.devotion + (1 if random.random() < 0.3 else 0))
            loc.clues = max(0, loc.clues - (1 if random.random() < 0.4 else 0))
        if self.prophecy_active and self.awareness > 0 and random.random() < 0.5:
            self.awareness = max(0, self.awareness - 1)

    # ---------- counterplay ----------
    def counterplay_tick(self):
        total_clues = sum(x.clues for x in self.locations)
        if total_clues > 0 and random.random() < 0.5:
            gain = max(1, total_clues // 12)
            self.awareness = clamp(self.awareness + gain)
            if gain >= 2:
                self.log("Word travels. Too many strange tales agree with each other. Awareness rises.")
        if self.awareness >= 30 and not self.heroes and random.random() < 0.4:
            h = Hero(person_name(), pick(self.locations).name)
            self.heroes.append(h)
            self.log("A " + h.kind + " has taken up the hunt: " + h.name + ".")
        if self.awareness >= 55 and random.random() < 0.25:
            h = Hero(person_name(), pick(self.locations).name)
            self.heroes.append(h)
            self.log("Another hunter rises: " + h.name + ", " + h.kind + ". The net tightens.")
        for h in list(self.heroes):
            if not h.alive:
                continue
            loc = self.loc(h.home)
            if loc is None:
                continue
            if loc.clues >= 15 and random.random() < 0.55:
                loc.clues = max(0, loc.clues - 12)
                loc.cult = max(0, loc.cult - 15)
                loc.shadow = max(0, loc.shadow - 10)
                self.log(h.name + " investigates " + loc.name + ": arrests, burnings at dawn, silence after.")
                for a in self.agents:
                    if a.alive and a.scheme_loc == loc.name and random.random() < 0.3:
                        a.alive = False
                        self.log("Your agent " + a.name + " is taken in " + loc.name + " and does not return.")
            elif random.random() < 0.25:
                worst = max(self.locations, key=lambda x: x.clues)
                h.home = worst.name
        if self.awareness >= 80:
            for k in self.kingdoms:
                k.allied_to_light = True

    # ---------- agents ----------
    def agent_tick(self):
        for a in self.agents:
            if not a.alive:
                continue
            if a.scheme is None:
                self._agent_autonomy(a)
                continue
            a.scheme_left -= 1
            loc = self.loc(a.scheme_loc)
            if loc is None:
                a.scheme = None
                continue
            risk = SCHEMES[a.scheme]["risk"]
            if random.random() < risk * 0.06:
                loc.clues = clamp(loc.clues + random.randint(4, 10))
            if a.scheme_left > 0:
                continue
            self._scheme_finish(a, loc)
            a.scheme = None
            a.scheme_loc = None

    def _agent_autonomy(self, a):
        loc = self.loc(a.home)
        if loc is None:
            return
        if a.ambition == "to see the Church fall" and loc.devotion > 20:
            loc.devotion = clamp(loc.devotion - 3)
            loc.shadow = clamp(loc.shadow + 3)
        elif a.ambition == "power":
            loc.shadow = clamp(loc.shadow + 2)
        elif a.ambition == "forbidden knowledge":
            loc.enshadow = clamp(loc.enshadow + 2)
            loc.clues = clamp(loc.clues + 1)
        if random.random() < 0.12:
            self.log(a.name + ", idle, follows their own ambition (" + a.ambition + ") in " + loc.name + ".")

    def _scheme_finish(self, a, loc):
        s = a.scheme
        roll = random.randint(1, 10) + a.skill
        if a.trait in ("Zealous", "Charismatic"):
            roll += 1
        if self.god_key == "2" and s in ("2", "4"):
            roll += 2
        a.deeds += 1
        if roll <= 5:
            loc.clues = clamp(loc.clues + 12)
            a.loyalty = clamp(a.loyalty - 10)
            self.log(a.name + "'s " + SCHEMES[s]["name"] + " in " + loc.name + " FAILS, and leaves witnesses.")
            return
        if s == "1":
            loc.shadow = clamp(loc.shadow + 35)
            self.log(a.name + " is inside the household of " + loc.name + " now. Doors open from within.")
        elif s == "2":
            add = 25 if self.god_key == "2" else 18
            loc.cult = clamp(loc.cult + add)
            loc.enshadow = clamp(loc.enshadow + 10)
            loc.shadow = clamp(loc.shadow + 10)
            self.log("A cult of " + self.god + " takes root in " + loc.name + ". They pray facing down.")
        elif s == "3":
            loc.devotion = clamp(loc.devotion - 30)
            loc.enshadow = clamp(loc.enshadow + 18)
            loc.clues = clamp(loc.clues + 8)
            self.log("The shrine at " + loc.name + " is desecrated. What was done there is not described.")
        elif s == "4":
            k = None
            for x in self.kingdoms:
                if x.name == loc.kingdom:
                    k = x
            if loc.shadow < 25:
                self.log(a.name + " reaches for the ruler of " + loc.kingdom + " and finds no purchase. Infiltrate first.")
                return
            if k is not None:
                k.corrupted = True
                loc.enshadow = clamp(loc.enshadow + 25)
                for other in self.locations:
                    if other.kingdom == k.name:
                        other.enshadow = clamp(other.enshadow + 6)
                self.log("THE RULER FALLS: " + k.ruler + " of " + k.name + " now serves " + self.god + " in secret.")
        elif s == "5":
            n = random.randint(8, 25)
            loc.undead += n
            loc.enshadow = clamp(loc.enshadow + 15)
            loc.clues = clamp(loc.clues + 10)
            loc.devotion = clamp(loc.devotion - 10)
            self.log("The dead of " + loc.name + " rise (" + str(n) + "). The bells ring themselves.")
        elif s == "6":
            loc.unrest = clamp(loc.unrest + 35)
            loc.shadow = clamp(loc.shadow + 8)
            self.log("Whispers in " + loc.name + " turn to knives. Unrest boils.")
        elif s == "7":
            self.prophecy_active = True
            loc.cult = clamp(loc.cult + 8)
            self.log("A prophecy surfaces in " + loc.name + ": the Sealed One returns when the seals sing. It spreads because it frightens people pleasantly.")

    # ---------- seals / endings ----------
    def check_seals(self):
        capitals = [x for x in self.locations if x.kind == "Capital"]
        if not self.seals[0] and any(x.enshadow >= 80 for x in capitals):
            self.seals[0] = True
            self.log("*** SEAL I BREAKS: a capital is wholly Enshadowed. Something under the world rolls over. ***")
        if not self.seals[1] and any(k.corrupted for k in self.kingdoms):
            self.seals[1] = True
            self.log("*** SEAL II BREAKS: a crowned head bows to you. ***")
        if not self.seals[2] and self.world_enshadow() >= 45:
            self.seals[2] = True
            self.log("*** SEAL III BREAKS: the world's shadow is now its substance. ***")
        if all(self.seals) and self.ended is None:
            self.ended = "AWAKENED"
            self.log("YOU AWAKEN. The chronicle ends; the age that follows has no chroniclers.")
        if self.awareness >= 100 and self.ended is None:
            self.ended = "SEALED FOREVER"
            self.log("The Holy Alliance speaks your true name in unison, and the door shuts forever.")

    def step_turn(self):
        self.turn += 1
        self.power += 3
        self.world_tick()
        self.agent_tick()
        self.counterplay_tick()
        self.check_seals()


# ---------------- player actions ----------------

def do_whisper(w):
    cands = [x for x in w.locations]
    print("\nWhisper to a notable - choose a location:")
    for i, loc in enumerate(cands, 1):
        print(" " + str(i) + ". " + loc.name + " (" + loc.kingdom + ") - " + loc.notable + ", " + loc.notable_trait)
    sel = input("> ").strip()
    if not sel.isdigit() or not (1 <= int(sel) <= len(cands)):
        print("No whisper sent.")
        return
    loc = cands[int(sel) - 1]
    chance = 0.55 + (0.15 if w.god_key == "2" else 0) - loc.devotion / 400.0
    if random.random() < chance:
        a = Agent(loc.notable, loc.name)
        w.agents.append(a)
        loc.notable = person_name()
        loc.shadow = clamp(loc.shadow + 10)
        w.log("You whisper to " + a.name + " in " + loc.name + ". They listen. They do not sleep again, but they listen. (" + a.trait + "; wants " + a.ambition + ")")
        print("Recruited: " + a.name + " - " + a.trait + ", skill " + str(a.skill) + ", wants " + a.ambition)
    else:
        loc.clues = clamp(loc.clues + 5)
        w.log("You whisper to " + loc.notable + " in " + loc.name + ". They run to a priest instead. A clue is born.")
        print("They refused, and told a priest. +Clues in " + loc.name + ".")


def do_scheme(w):
    idle = [a for a in w.agents if a.alive and a.scheme is None]
    if not idle:
        print("No idle living agents.")
        return
    for i, a in enumerate(idle, 1):
        print(" " + str(i) + ". " + a.name + " at " + a.home + " (" + a.trait + ", skill " + str(a.skill) + ")")
    sel = input("Agent > ").strip()
    if not sel.isdigit() or not (1 <= int(sel) <= len(idle)):
        return
    a = idle[int(sel) - 1]
    for k, s in SCHEMES.items():
        print(" " + k + ". " + s["name"] + " (" + str(s["turns"]) + " turns) - " + s["desc"])
    sk = input("Scheme > ").strip()
    if sk not in SCHEMES:
        return
    for i, loc in enumerate(w.locations, 1):
        print(" " + str(i) + ". " + loc.name + " (" + loc.kingdom + ", " + loc.kind + ") Dev " + str(loc.devotion) + " Shadow " + str(loc.shadow) + " Ensh " + str(loc.enshadow))
    ls = input("Location > ").strip()
    if not ls.isdigit() or not (1 <= int(ls) <= len(w.locations)):
        return
    loc = w.locations[int(ls) - 1]
    cost = 5
    if w.god_key == "1" and sk == "5":
        cost = 2
    if w.power < cost:
        print("Not enough Power (need " + str(cost) + ").")
        return
    w.power -= cost
    a.scheme = sk
    a.scheme_loc = loc.name
    a.scheme_left = SCHEMES[sk]["turns"]
    a.home = loc.name
    print(a.name + " begins: " + SCHEMES[sk]["name"] + " in " + loc.name + ".")


def do_power(w):
    for k, p in POWERS.items():
        c = p["cost"]
        if w.god_key == "1" and k == "3":
            c = c // 2
        print(" " + k + ". " + p["name"] + " (" + str(c) + " Power) - " + p["desc"])
    sel = input("Power > ").strip()
    if sel not in POWERS:
        return
    cost = POWERS[sel]["cost"]
    if w.god_key == "1" and sel == "3":
        cost = cost // 2
    if w.power < cost:
        print("Not enough Power (have " + str(w.power) + ", need " + str(cost) + ").")
        return
    if sel == "6":
        w.power -= cost
        for loc in w.locations:
            loc.enshadow = clamp(loc.enshadow + 7)
            loc.clues = clamp(loc.clues + 5)
            loc.devotion = clamp(loc.devotion - 5)
        w.log("ECLIPSE. For one day the sun does not rise. Every field, every altar, every face turns up at a black sky.")
        print("The sun goes out for a day.")
        return
    for i, loc in enumerate(w.locations, 1):
        print(" " + str(i) + ". " + loc.name + " (" + loc.kingdom + ") pop " + str(loc.population))
    ls = input("Location > ").strip()
    if not ls.isdigit() or not (1 <= int(ls) <= len(w.locations)):
        return
    loc = w.locations[int(ls) - 1]
    w.power -= cost
    if sel == "1":
        loc.plague = 3
        loc.clues = clamp(loc.clues + 6)
        w.log("You breathe plague into " + loc.name + ".")
    elif sel == "2":
        amt = 18 if w.god_key == "4" else 12
        loc.devotion = clamp(loc.devotion - amt)
        loc.shadow = clamp(loc.shadow + amt)
        w.log("All of " + loc.name + " dreams the same dream: you, at the foot of every bed.")
    elif sel == "3":
        n = random.randint(15, 40)
        loc.undead += n
        loc.enshadow = clamp(loc.enshadow + 12)
        loc.clues = clamp(loc.clues + 12)
        w.log("CORPSE-HOST: " + str(n) + " dead stand up in " + loc.name + " at your word.")
    elif sel == "4":
        k = None
        for x in w.kingdoms:
            if x.name == loc.kingdom:
                k = x
        if k is not None and random.random() < 0.45:
            k.corrupted = True
            w.log("MADNESS TAKES THE THRONE: " + k.ruler + " of " + k.name + " breaks, beautifully, and is yours.")
        else:
            loc.unrest = clamp(loc.unrest + 20)
            loc.clues = clamp(loc.clues + 6)
            w.log("Madness blooms in " + loc.name + ". The notable is found laughing in the well.")
    elif sel == "5":
        loc.cult = clamp(loc.cult + 20)
        loc.enshadow = clamp(loc.enshadow + 12)
        loc.devotion = clamp(loc.devotion - 8)
        w.log("A DARK MIRACLE in " + loc.name + ": the dead child sits up at her funeral and asks for you by name.")


def show_world(w):
    print("\n=== " + w.god + " - Year " + str(w.turn // 12 + 1) + ", Month " + str(w.turn % 12 + 1) + " ===")
    print("Power " + str(w.power) + " | Awareness " + str(w.awareness) + "/100 | World Enshadow " + str(w.world_enshadow()) + "%")
    print("Seals: " + " ".join(["[BROKEN]" if s else "[whole]" for s in w.seals]))
    print("God-gift: " + GODS[w.god_key]["gift"])
    for k in w.kingdoms:
        flag = " CORRUPTED" if k.corrupted else (" ALLIANCE" if k.allied_to_light else "")
        war = (" at war with " + k.at_war_with) if k.at_war_with else ""
        print(" " + k.name + ": " + k.ruler + " (" + k.ruler_trait + ", " + str(k.ruler_age) + ")" + flag + war)
    print(" Locations:")
    for loc in w.locations:
        extra = ""
        if loc.cult:
            extra += " cult " + str(loc.cult)
        if loc.undead:
            extra += " undead " + str(loc.undead)
        if loc.plague:
            extra += " PLAGUE"
        print("  " + loc.name + " (" + loc.kingdom + ", " + loc.kind + ") pop " + str(loc.population) +
              " Dev " + str(loc.devotion) + " Shd " + str(loc.shadow) + " Ens " + str(loc.enshadow) +
              " Clues " + str(loc.clues) + " Unrest " + str(loc.unrest) + extra)
    print(" Agents: " + str(len([a for a in w.agents if a.alive])) + " living / " + str(len(w.agents)) + " ever")
    for a in w.agents:
        state = "dead/taken" if not a.alive else (SCHEMES[a.scheme]["name"] + " in " + str(a.scheme_loc) + " (" + str(a.scheme_left) + " left)" if a.scheme else "idle in " + a.home)
        print("  " + a.name + " - " + a.trait + ", wants " + a.ambition + " - " + state)
    for h in w.heroes:
        if h.alive:
            print(" Hunter: " + h.name + ", " + h.kind + ", hunting from " + h.home)


def show_chronicle(w, last=25):
    print("\n--- Chronicle (last " + str(last) + ") ---")
    for e in w.chronicle[-last:]:
        print(" " + e)


def save_world(w):
    with open(SAVE_PATH, "wb") as f:
        pickle.dump(w, f)
    print("Saved.")


def load_world():
    with open(SAVE_PATH, "rb") as f:
        return pickle.load(f)


def auto_play(w, turns):
    """Headless / watch mode: a simple god-AI plays, or nobody does - world still runs."""
    for _ in range(turns):
        if w.ended:
            break
        if len([a for a in w.agents if a.alive]) < 3 and w.turn % 3 == 0:
            loc = pick(w.locations)
            a = Agent(loc.notable, loc.name)
            w.agents.append(a)
            loc.notable = person_name()
            w.log("You whisper to " + a.name + " in " + loc.name + ", and they listen.")
        for a in w.agents:
            if a.alive and a.scheme is None and random.random() < 0.7:
                sk = pick(list(SCHEMES.keys()))
                loc = pick(w.locations)
                a.scheme = sk
                a.scheme_loc = loc.name
                a.scheme_left = SCHEMES[sk]["turns"]
                a.home = loc.name
        w.step_turn()
    return w


def main(argv):
    if "--auto" in argv:
        n = 120
        idx = argv.index("--auto")
        if idx + 1 < len(argv) and argv[idx + 1].isdigit():
            n = int(argv[idx + 1])
        w = World(pick(list(GODS.keys())))
        auto_play(w, n)
        show_world(w)
        show_chronicle(w, 60)
        print("\nEnded: " + str(w.ended) + " after " + str(w.turn) + " months.")
        return
    print("VEILFALL v" + VERSION + " - a sealed-god game")
    w = None
    if "--continue" in argv and os.path.exists(SAVE_PATH):
        w = load_world()
        print("Resumed: " + w.god + ", turn " + str(w.turn))
    if w is None:
        print("\nChoose the god you are:")
        for k, g in GODS.items():
            print(" " + k + ". " + g["name"] + ", " + g["title"])
            print("    " + g["desc"])
            print("    Gift: " + g["gift"])
        sel = input("> ").strip()
        if sel not in GODS:
            sel = "1"
        w = World(sel)
    while True:
        show_world(w)
        if w.ended:
            print("\n*** " + w.ended + " *** (you may keep playing the sandbox, or Q to quit)")
        print("\n1 Whisper (recruit)  2 Scheme  3 Power  4 Advance 1 month  5 Watch 12 months  6 Chronicle  7 Save  Q Quit")
        cmd = input("> ").strip().lower()
        if cmd == "q":
            save_world(w)
            break
        elif cmd == "1":
            do_whisper(w)
        elif cmd == "2":
            do_scheme(w)
        elif cmd == "3":
            do_power(w)
        elif cmd == "4":
            w.step_turn()
            show_chronicle(w, 8)
        elif cmd == "5":
            for _ in range(12):
                w.step_turn()
                if w.ended:
                    break
            show_chronicle(w, 20)
        elif cmd == "6":
            show_chronicle(w, 100)
        elif cmd == "7":
            save_world(w)
        else:
            print("?")


if __name__ == "__main__":
    main(sys.argv[1:])

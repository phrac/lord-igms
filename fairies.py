"""Fairies for flux/bbs's LORD in-game modules: a jar each player carries
from place to place (FAIRIES.DAT in LORD's folder), filled at Willow
Pond, where one now and then comes up tangled in a line, and emptied
wherever a fairy can help: she whispers a digit at the Hermit's
Terminal, sniffs a virus off one of Dusty's floppies, steadies Rusk's
wheel, or charms Brakka into his best work.

LORD's own fairy (the one from the forest, that saves its player from
death) is LORD's to keep: modules can see it (`lord_fairy`) but not take
it. Not a module itself: the others import it from their folder.
"""
import json
import os
import random
import time

STATE = "FAIRIES.DAT"
JAR = 3
NAMES = ["Tisha", "Nolan", "Glimmer", "Pip", "Bramble", "Wisp", "Fennel", "Sorrel", "Thistle", "Moss"]


def _load():
    try:
        return json.load(open(STATE))
    except (OSError, ValueError):
        return {}


def _save(s):
    tmp = STATE + ".new"
    with open(tmp, "w") as f:
        json.dump(s, f)
    os.replace(tmp, STATE)


def _mine(s, g):
    p = s.get(str(g.account))
    # A new game reuses accounts: the jar is theirs only with their name.
    if not p or p.get("name") != g.player.name:
        p = {"name": g.player.name, "fairies": []}
        s[str(g.account)] = p
    return p


def jar(g):
    """The fairies in the player's jar, by name."""
    return list(_mine(_load(), g)["fairies"])


def count(g):
    return len(jar(g))


def catch(g):
    """A fairy into the jar: her name, or None if the jar's full."""
    s = _load()
    me = _mine(s, g)
    if len(me["fairies"]) >= JAR:
        return None
    name = random.choice([n for n in NAMES if n not in me["fairies"]] or NAMES)
    me["fairies"].append(name)
    me["day"] = time.strftime("%Y-%m-%d")
    _save(s)
    return name


def release(g):
    """One fairy out of the jar (the first in): her name, or None."""
    s = _load()
    me = _mine(s, g)
    if not me["fairies"]:
        return None
    name = me["fairies"].pop(0)
    _save(s)
    return name


def lord_fairy(g):
    """LORD's own fairy is with the player (it says so in INFO)."""
    return bool(g.info.get("fairy"))


def offer(g, why):
    """Ask whether to spend a fairy on `why`; her name if spent."""
    if not count(g):
        return None
    name = jar(g)[0]
    k = g.key(f"  `#{name}`2 stirs in your jar.  {why} [`0Y`2/`0N`2] : ", "YN", "N")
    return release(g) if k == "Y" else None


if __name__ == "__main__":
    print(__doc__)

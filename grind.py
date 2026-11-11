"""Old Rusk's Grindstone: a LORD in-game module, native to flux/bbs.

Old Rusk sharpens weapons by the road, and drinks. Each day he's sober,
tipsy, drunk or plastered (the same for everyone), and anyone may buy him
an ale or pour him a coffee, for whoever comes next. Once a day he puts
an edge on a player's weapon, for a fee: sober he's careful and the edge
is small but sure; the drunker he is, the wider it goes: blunted and
chipped blades, a brawl, a picked pocket, and, only drunk, now and then
a masterwork that makes the Daily Happenings.

An edge is strength added (or taken off, for a blunted blade), and it
lasts until the player's next visit on a later day or with another
weapon, when it comes off first. LORD takes a weapon's own number off
strength when it's sold, so a lasting bonus could be sold and bought
again; this way nobody holds more than one day's edge, and a nick stays
until Rusk sees the blade again. The edges and Rusk's day are in
GRIND.DAT in LORD's folder.

Install: this folder where the board's `[dos.native] "*"` points
(README.md), then `python3 grind.py install /path/to/LORD` adds it to LORD's
3RDPARTY.DAT, with the GRIND.IGM LORD looks for (`uninstall` takes them
off again).
"""
import json
import os
import random
import sys
import time

NAME = "GRIND"
SHOWN = "`0O`2ld `0R`2usk's `0G`2rindstone"
STATE = "GRIND.DAT"

MOODS = ["sober", "tipsy", "drunk", "plastered"]
MOOD_ODDS = [25, 35, 25, 15]
LOOKS = [
    "Rusk is bent over the wheel, clear-eyed, humming a hymn.",
    "Rusk greets you a little too warmly.  There's a mug by the wheel.",
    "Rusk is swaying.  The wheel isn't the only thing spinning.",
    "Rusk is singing to the grindstone.  Three empty kegs lie about him.",
]
SAYS = [
    ["\"Steel's like people.  Treat it right, it treats you right.\"",
     "\"Never touch the stuff before noon.  Or after.\"",
     "\"That blade's seen some things.  I can tell.\""],
    ["\"Just the one, to steady the hand.  Or two.\"",
     "\"Did I ever tell you about the time I sharpened a dragon's tooth?\"",
     "\"You've got an honest face.  Bit lopsided, but honest.\""],
    ["\"I love you, you know that?  I love everyone.  Hic.\"",
     "\"The wheel goes round... and round... and...\"",
     "\"Sharpest man in the realm, me.  Sharpest.  Where's my stone?\""],
    ["\"*hic*  WHO WANTS A SONG?\"",
     "\"I can see three of you.  I'll sharpen the middle one.\"",
     "\"The Red Dragon owes me four silver.  FOUR.\""],
]

# What a sharpening comes to: (name, odds for each mood).
OUTCOMES = [
    ("keen", [55, 35, 20, 10]),
    ("razor", [5, 8, 12, 14]),
    ("masterwork", [0, 0, 3, 7]),
    ("polish", [30, 25, 15, 10]),
    ("blunt", [8, 18, 22, 22]),
    ("chipped", [2, 6, 12, 15]),
    ("brawl", [0, 4, 9, 13]),
    ("pickpocket", [0, 4, 7, 9]),
]
# Each edge as a share of strength.
EDGE = {"keen": 0.03, "razor": 0.06, "masterwork": 0.10, "polish": 0.0, "blunt": -0.03, "chipped": -0.06}


def today():
    return time.strftime("%Y-%m-%d")


def load():
    try:
        s = json.load(open(STATE))
    except (OSError, ValueError):
        s = {}
    s.setdefault("players", {})
    if s.get("rusk", {}).get("day") != today():
        s["rusk"] = {"day": today(), "mood": random.choices(range(4), MOOD_ODDS)[0]}
    return s


def save(s):
    tmp = STATE + ".new"
    with open(tmp, "w") as f:
        json.dump(s, f)
    os.replace(tmp, STATE)


def price(g):
    return 20 + 30 * max(1, g.player.level)


def mine(s, g):
    p = s["players"].get(str(g.account))
    if not p or p.get("name") != g.player.name:
        p = {"name": g.player.name, "day": "", "edge": 0, "weapon": g.player.weapon_num}
        s["players"][str(g.account)] = p
    return p


def settle(g, s):
    """Yesterday's edge (or another weapon's) off before anything else."""
    me, p = mine(s, g), g.player
    if me["edge"] and (me["day"] != today() or me["weapon"] != p.weapon_num):
        p.strength = max(1, p.strength - me["edge"])
        if me["weapon"] != p.weapon_num:
            g.say("  `2Your old blade's edge went with it.")
        elif me["edge"] > 0:
            g.say("  `2The edge Rusk put on your weapon has worn off.")
        else:
            g.say("  `2Rusk squints at the nick he left and grinds it out, muttering.")
        g.say()
        me["edge"] = 0
        save(s)
        g.save()


def edge(g, share):
    return max(1, round(g.player.strength * abs(share))) * (1 if share > 0 else -1)


def sharpen(g, s):
    me, p = mine(s, g), g.player
    mood = s["rusk"]["mood"]
    cost = price(g)
    if me["day"] == today():
        g.say()
        g.say("  `0\"Already done yours today.  Any sharper and it'd cut the air.\"")
        g.say()
        g.more()
        return
    if p.gold < cost:
        g.say()
        g.say(f"  `0\"{cost:,} gold, friend.  The ale doesn't pay for itself.\"")
        g.say()
        g.more()
        return
    p.gold -= cost
    me.update(day=today(), weapon=p.weapon_num, edge=0)
    save(s)
    g.save()
    g.title("Old Rusk's Grindstone")
    g.say(f"  `2You hand Rusk `${cost:,} gold`2 (`${p.gold:,}`2 left) and your `0{p.weapon}`2.")
    g.say(f"  `2He's `0{MOODS[mood]}`2 today.")
    g.say()
    g.write("  `3")
    for _ in range(5):
        g.write("*skreee* ")
        g.pause(0.4)
    g.say()
    g.say()
    names, odds = zip(*OUTCOMES)
    what = random.choices(names, [o[mood] for o in odds])[0]
    # A fairy from the jar (fairies.py) can steady his hand, when it's
    # going wrong.
    if what in ("blunt", "chipped", "brawl", "pickpocket"):
        import fairies

        name = fairies.offer(g, "Rusk's hand is wandering.  Let her steady the wheel?")
        if name:
            g.say(f"  `#{name}`2 lands on the wheel and glares at Rusk until he behaves.")
            g.say("  `2Then she's off into the trees.")
            g.say()
            what = "keen"
    if what in EDGE and EDGE[what]:
        d = edge(g, EDGE[what])
        p.strength = max(1, p.strength + d)
        me["edge"] = d
    if what == "keen":
        g.say("  `2He tests it on his thumb, winces, and hands it back.  A fine edge:")
        g.say(f"  `0+{me['edge']} strength`2 until it wears off.")
    elif what == "razor":
        g.say("  `2It sings coming off the wheel.  You could shave a gnat with it:")
        g.say(f"  `0+{me['edge']} strength`2 until it wears off.")
    elif what == "masterwork":
        g.say("  `2Rusk stops singing.  His hands go still and sure, the way they")
        g.say("  `2were forty years ago.  When he's done, the blade looks new-made.")
        g.say(f"  `%A drunken masterwork!  `0+{me['edge']} strength`2 until it wears off.")
        g.news(f"`0{p.name}`2's `0{p.weapon} `2got a drunken masterwork from `0Old Rusk`2!")
    elif what == "polish":
        g.say("  `2He forgets the wheel and polishes it with his sleeve instead.")
        g.say("  `2It's very shiny.  It's exactly as sharp as before.")
    elif what == "blunt":
        g.say("  `2He holds it to the wheel at quite the wrong angle, for quite a")
        g.say(f"  `2while.  It comes back duller: `4{me['edge']} strength`2, until he sees it again.")
    elif what == "chipped":
        g.say("  `2There's a crack, a curse, and a chunk of your blade skitters off")
        g.say(f"  `2into the grass.  `4{me['edge']} strength`2, until he sees it again.")
        g.news(f"`0Old Rusk `2chipped `0{p.name}`2's `0{p.weapon}`2.  He says it was like that.")
    elif what == "brawl":
        hurt = min(max(1, p.hit_max // 7), max(0, p.hit_points - 1))
        p.hit_points -= hurt
        g.say("  `2\"You calling me DRUNK?\"  You weren't.  He swings anyway, and")
        g.say(f"  `2lands one.  `4-{hurt} hit points`2.  Your weapon's no sharper, either.")
        g.news(f"`0Old Rusk `2took a swing at `0{p.name}`2.  Nobody's sure why.")
    elif what == "pickpocket":
        # A fifth of the purse, but no more than five sharpenings' worth.
        lost = min(p.gold // 5, price(g) * 5)
        p.gold -= lost
        d = edge(g, EDGE["keen"])
        p.strength += d
        me["edge"] = d
        g.say("  `2A fine edge, `0+{0} strength`2.  It's only on the road home that".format(d))
        g.say(f"  `2you find your purse lighter: `4-{lost:,} gold`2.")
    save(s)
    g.say()
    g.more()


def drink(g, s, ale):
    p = g.player
    cost = (15 if ale else 10) * max(1, p.level)
    rusk = s["rusk"]
    if p.gold < cost:
        g.say()
        g.say(f"  `2That's `${cost:,} gold`2.  You haven't got it on you.")
        g.say()
        g.more()
        return
    if ale and rusk["mood"] >= 3:
        g.say()
        g.say("  `2Rusk is asleep under the grindstone.  Even he has limits.")
        g.say()
        g.more()
        return
    if not ale and rusk["mood"] == 0:
        g.say()
        g.say("  `0\"Coffee?  I'm sober as a priest.  Drink it yourself.\"")
        g.say()
        g.more()
        return
    p.gold -= cost
    rusk["mood"] += 1 if ale else -1
    save(s)
    g.say()
    if ale:
        g.say(f"  `2You buy Rusk an ale (`${cost:,} gold`2).  He drinks it in one go.")
    else:
        g.say(f"  `2You pour Rusk a strong coffee (`${cost:,} gold`2).  He makes a face.")
    g.say(f"  `2He's `0{MOODS[rusk['mood']]}`2 now, for whoever's next.")
    g.say()
    g.more()


def main():
    import lordigm

    with lordigm.Igm() as g:
        g.title("Old Rusk's Grindstone")
        s = load()
        settle(g, s)
        while True:
            s = load()
            me, p = mine(s, g), g.player
            mood = s["rusk"]["mood"]
            g.title("Old Rusk's Grindstone")
            g.say("  `2By the road stands a grindstone on a cart, and beside it Old Rusk,")
            g.say("  `2who has sharpened every blade in the realm, some of them twice.")
            g.say("  `2" + LOOKS[mood])
            g.say()
            if me["edge"] > 0 and me["day"] == today():
                g.say(f"  `2Your `0{p.weapon}`2 has his edge on it today: `0+{me['edge']} strength`2.")
            elif me["edge"] < 0:
                g.say(f"  `2Your `0{p.weapon}`2 still has his nick in it: `4{me['edge']} strength`2.")
            g.say()
            done = me["day"] == today()
            g.say(f"  `2(`0S`2)harpen your weapon   `2({price(g):,} gold" + (", done today)" if done else ")"))
            g.say(f"  `2(`0A`2)le for Rusk          `2({15 * max(1, p.level):,} gold)")
            g.say(f"  `2(`0C`2)offee for Rusk       `2({10 * max(1, p.level):,} gold)")
            g.say("  `2(`0T`2)alk to Rusk")
            g.say("  `2(`0R`2)eturn to town")
            g.say()
            g.say(f"  `2You have `${p.gold:,} gold`2 on hand.")
            k = g.key("  `2Your choice? [`0R`2] : ", "SACTR", "R")
            if k == "S":
                sharpen(g, s)
            elif k in "AC":
                drink(g, s, k == "A")
            elif k == "T":
                g.say()
                g.say("  `0" + random.choice(SAYS[mood]))
                g.say()
                g.more()
            else:
                g.say()
                g.say("  `2You leave Rusk to his wheel.")
                g.pause(0.6)
                return


def install(folder, remove=False):
    """Add the two lines to (or take them off) LORD's 3RDPARTY.DAT, with
    GRIND.IGM beside it: LORD only sends players to a program it can
    find, and the board runs this in its place."""
    find = lambda n: next((f for f in os.listdir(folder) if f.upper() == n), n)
    path = os.path.join(folder, find("3RDPARTY.DAT"))
    stub = os.path.join(folder, find(NAME + ".IGM"))
    lines = open(path, "rb").read().decode("cp437").replace("\r", "").split("\n") if os.path.exists(path) else []
    out, i = [], 0
    while i < len(lines):
        first = lines[i].strip().upper().split(" ")[0]
        if first.rsplit("\\", 1)[-1].split(".")[0] == NAME:
            i += 2
            continue
        out.append(lines[i])
        i += 1
    while out and not out[-1].strip():
        out.pop()
    if remove:
        if os.path.exists(stub):
            os.remove(stub)
    else:
        out += [f"{NAME}.IGM *", SHOWN]
        with open(stub, "wb") as f:
            f.write(b"Old Rusk's Grindstone: a flux/bbs native module ([dos] native).\r\n")
    open(path, "wb").write(("\r\n".join(out) + "\r\n").encode("cp437"))
    print(("took Old Rusk's Grindstone off " if remove else "added Old Rusk's Grindstone to ") + path)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("install", "uninstall"):
        install(sys.argv[2] if len(sys.argv) > 2 else ".", sys.argv[1] == "uninstall")
    else:
        main()

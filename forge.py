"""Brakka's Forge: a LORD in-game module, native to flux/bbs.

Brakka the dwarf reinforces armor, and his hands are only steady on
dragon scale, ground fine and taken up the nose. Each day he's clean,
buzzed, high or soaring (the same for everyone), and anyone may buy him
a pinch of scale or a dipper of cold water, for whoever comes next.
Once a day he works a player's armor, for a fee, and it's Rusk the
other way round: clean he fumbles (dents, cracks), and the higher he
is, the better the work, up to dragonforged plate that makes the Daily
Happenings, though soaring he may hide under the anvil from dragons
only he can see. He adores fairies: LORD's own fairy at a player's
side lifts his work a step, and a fairy from the jar (fairies.py) given
to him makes his best.

The work is defense added (or taken off, for a dent), lasting until the
player's next visit on a later day or with other armor, when it comes
off first: LORD takes armor's own number off when it's sold, so it
can't last. His day and the work are in FORGE.DAT in LORD's folder.

Install: this folder where the board's `[dos.native] "*"` points
(README.md), then `python3 forge.py install /path/to/LORD` adds it to LORD's
3RDPARTY.DAT, with the FORGE.IGM LORD looks for (`uninstall` takes them
off again).
"""
import json
import os
import random
import sys
import time

NAME = "FORGE"
SHOWN = "`0B`2rakka's `0F`2orge"
STATE = "FORGE.DAT"

MOODS = ["clean", "buzzed", "high", "soaring"]
MOOD_ODDS = [30, 35, 25, 10]
LOOKS = [
    "Brakka glares at the anvil.  His hands shake.  He hasn't had his scale.",
    "Brakka hums at the bellows, eyes bright.  A little dish of red dust sits by the tongs.",
    "Brakka is grinning at nothing.  The sparks seem to like him.",
    "Brakka's pupils are the size of shields.  He's talking to the forge, and it's answering.",
]
SAYS = [
    ["\"Don't look at me like that.  It's MEDICINAL.\"",
     "\"Can't feel the metal today.  Can't feel anything.\"",
     "\"Come back when I've had my scale.  Or don't.  Ugh.\""],
    ["\"Ahh, that's better.  Now we can talk.\"",
     "\"Dragon scale.  Best thing about dragons, if you ask me.\"",
     "\"You've got a fairy?  No?  Pity.  I love the little ones.\""],
    ["\"I can hear the iron, you know.  It wants to be a breastplate.\"",
     "\"Everything's so SHINY.\"",
     "\"Bring me a fairy and I'll make you armor the Dragon cries about.\""],
    ["\"The DRAGON is HERE.  No, wait.  That's my apron.\"",
     "\"I am one with the anvil.  The anvil is one with me.\"",
     "\"Fairies!  Where are the FAIRIES?  I'll make them little helmets.\""],
]

# What the work comes to: (name, odds for each mood).
OUTCOMES = [
    ("riveted", [30, 40, 35, 25]),
    ("plated", [5, 15, 25, 30]),
    ("dragonforged", [0, 2, 8, 15]),
    ("buffed", [20, 15, 10, 6]),
    ("dented", [30, 15, 8, 4]),
    ("cracked", [15, 8, 4, 2]),
    ("burned", [0, 5, 5, 8]),
    ("hiding", [0, 0, 5, 10]),
]
GOOD = {"riveted", "plated", "dragonforged"}
WORK = {"riveted": 0.03, "plated": 0.06, "dragonforged": 0.10, "dented": -0.03, "cracked": -0.06}


def today():
    return time.strftime("%Y-%m-%d")


def load():
    try:
        s = json.load(open(STATE))
    except (OSError, ValueError):
        s = {}
    s.setdefault("players", {})
    if s.get("brakka", {}).get("day") != today():
        s["brakka"] = {"day": today(), "mood": random.choices(range(4), MOOD_ODDS)[0]}
    return s


def save(s):
    tmp = STATE + ".new"
    with open(tmp, "w") as f:
        json.dump(s, f)
    os.replace(tmp, STATE)


def price(g):
    return 20 + 35 * max(1, g.player.level)


def mine(s, g):
    p = s["players"].get(str(g.account))
    if not p or p.get("name") != g.player.name:
        p = {"name": g.player.name, "day": "", "work": 0, "armor": g.player.armour_num}
        s["players"][str(g.account)] = p
    return p


def settle(g, s):
    """Yesterday's work (or other armor's) off before anything else."""
    me, p = mine(s, g), g.player
    if me["work"] and (me["day"] != today() or me["armor"] != p.armour_num):
        p.defense = max(1, p.defense - me["work"])
        if me["armor"] != p.armour_num:
            g.say("  `2Brakka's work went with your old armor.")
        elif me["work"] > 0:
            g.say("  `2The plates Brakka riveted on have worked loose again.")
        else:
            g.say("  `2Brakka hammers out yesterday's dent without a word.")
        g.say()
        me["work"] = 0
        save(s)
        g.save()


def amount(g, share):
    return max(1, round(g.player.defense * abs(share))) * (1 if share > 0 else -1)


def work(g, s):
    import fairies

    me, p = mine(s, g), g.player
    mood = s["brakka"]["mood"]
    cost = price(g)
    if me["day"] == today():
        g.say()
        g.say("  `0\"Did yours already.  Any more iron on you and you'd sink.\"")
        g.say()
        g.more()
        return
    if p.gold < cost:
        g.say()
        g.say(f"  `0\"{cost:,} gold.  Scale isn't cheap, and neither am I.\"")
        g.say()
        g.more()
        return
    p.gold -= cost
    me.update(day=today(), armor=p.armour_num, work=0)
    save(s)
    g.save()
    g.title("Brakka's Forge")
    g.say(f"  `2You hand Brakka `${cost:,} gold`2 (`${p.gold:,}`2 left) and your `0{p.armour}`2.")
    g.say(f"  `2He's `0{MOODS[mood]}`2 today.")
    lift = 0
    if fairies.lord_fairy(g):
        g.say("  `2Your fairy flutters round the forge.  Brakka is beside himself.")
        lift = 1
    gift = None
    if fairies.count(g):
        gift = fairies.offer(g, "Give her to Brakka for his best work?")
        if gift:
            g.say(f"  `2Brakka cups `#{gift}`2 in his hands and weeps a little.  Then he")
            g.say("  `2rolls up his sleeves.")
    g.say()
    g.write("  `3")
    for _ in range(5):
        g.write("*CLANG* ")
        g.pause(0.4)
    g.say()
    g.say()
    names, odds = zip(*OUTCOMES)
    if gift:
        what = random.choices(["plated", "dragonforged"], [65, 35])[0]
    else:
        what = random.choices(names, [o[min(3, mood + lift)] for o in odds])[0]
    if what in WORK:
        d = amount(g, WORK[what])
        p.defense = max(1, p.defense + d)
        me["work"] = d
    if what == "riveted":
        g.say("  `2He rivets a few extra plates where they'll do the most good:")
        g.say(f"  `0+{me['work']} defense`2 until they work loose.")
    elif what == "plated":
        g.say("  `2He hammers on a second skin of steel, humming the whole time:")
        g.say(f"  `0+{me['work']} defense`2 until it works loose.")
    elif what == "dragonforged":
        g.say("  `2He works the metal like dough, red to white and back, singing")
        g.say("  `2something in dwarvish.  It cools with a dragon's shimmer on it.")
        g.say(f"  `%Dragonforged!  `0+{me['work']} defense`2 until it works loose.")
        g.news(f"`0Brakka `2dragonforged `0{p.name}`2's `0{p.armour}`2.  It shimmers.")
    elif what == "buffed":
        g.say("  `2He polishes it for a long time and calls it done.  It gleams.")
        g.say("  `2It's exactly as strong as before.")
    elif what == "dented":
        g.say("  `2Her hammer misses the rivet and finds the plate.  Twice.")
        g.say(f"  `4{me['work']} defense`2, until he sees it again.")
    elif what == "cracked":
        g.say("  `2He quenches it too fast.  *CRACK*.  \"That's... character.\"")
        g.say(f"  `4{me['work']} defense`2, until he sees it again.")
        g.news(f"`0Brakka `2cracked `0{p.name}`2's `0{p.armour}`2.  He blames the water.")
    elif what == "burned":
        hurt = min(max(1, p.hit_max // 8), max(0, p.hit_points - 1))
        p.hit_points -= hurt
        g.say("  `2He hands it back straight out of the forge.  You catch it.")
        g.say(f"  `4-{hurt} hit points`2.  The armor's no better, either.")
    elif what == "hiding":
        p.gold += cost
        g.say("  `2Brakka screams, drops everything and dives under the anvil.")
        g.say("  `0\"DRAGONS!  In the CHIMNEY!\"  `2There are no dragons in the chimney.")
        g.say(f"  `2He pushes your `${cost:,} gold`2 back out with his foot.  Come back tomorrow.")
    save(s)
    g.say()
    g.more()


def scale(g, s, up):
    p = g.player
    cost = (20 if up else 5) * max(1, p.level)
    b = s["brakka"]
    if p.gold < cost:
        g.say()
        g.say(f"  `2That's `${cost:,} gold`2.  You haven't got it on you.")
        g.say()
        g.more()
        return
    if up and b["mood"] >= 3:
        g.say()
        g.say("  `0\"More?  I can see SOUNDS already.\"  `2He waves it away.")
        g.say()
        g.more()
        return
    if not up and b["mood"] == 0:
        g.say()
        g.say("  `0\"Water.  Wonderful.  Exactly what I need.\"  `2He pours it on your boots.")
        g.say()
        g.more()
        return
    p.gold -= cost
    b["mood"] += 1 if up else -1
    save(s)
    g.say()
    if up:
        g.say(f"  `2You buy Brakka a pinch of dragon scale (`${cost:,} gold`2).  *SNORT*")
    else:
        g.say(f"  `2You hand Brakka a dipper of cold water (`${cost:,} gold`2).  He gulps it.")
    g.say(f"  `2He's `0{MOODS[b['mood']]}`2 now, for whoever's next.")
    g.say()
    g.more()


def main():
    import fairies
    import lordigm

    with lordigm.Igm() as g:
        g.title("Brakka's Forge")
        s = load()
        settle(g, s)
        while True:
            s = load()
            me, p = mine(s, g), g.player
            mood = s["brakka"]["mood"]
            g.title("Brakka's Forge")
            g.say("  `2Behind the smithy, a squat stone forge, and Brakka the dwarf,")
            g.say("  `2armorer to three kings and a dragon (he won't say which).")
            g.say("  `2" + LOOKS[mood])
            g.say()
            if me["work"] > 0 and me["day"] == today():
                g.say(f"  `2Your `0{p.armour}`2 has his work on it today: `0+{me['work']} defense`2.")
            elif me["work"] < 0:
                g.say(f"  `2Your `0{p.armour}`2 still has his dent in it: `4{me['work']} defense`2.")
            n = fairies.count(g)
            if n:
                g.say(f"  `2Fairies in your jar: `#{', '.join(fairies.jar(g))}`2.")
            g.say()
            done = me["day"] == today()
            g.say(f"  `2(`0W`2)ork on your armor     `2({price(g):,} gold" + (", done today)" if done else ")"))
            g.say(f"  `2(`0S`2)cale for Brakka       `2({20 * max(1, p.level):,} gold)")
            g.say(f"  `2(`0C`2)old water for Brakka  `2({5 * max(1, p.level):,} gold)")
            g.say("  `2(`0T`2)alk to Brakka")
            g.say("  `2(`0R`2)eturn to town")
            g.say()
            g.say(f"  `2You have `${p.gold:,} gold`2 on hand.")
            k = g.key("  `2Your choice? [`0R`2] : ", "WSCTR", "R")
            if k == "W":
                work(g, s)
            elif k in "SC":
                scale(g, s, k == "S")
            elif k == "T":
                g.say()
                g.say("  `0" + random.choice(SAYS[mood]))
                g.say()
                g.more()
            else:
                g.say()
                g.say("  `2You leave Brakka to his forge.")
                g.pause(0.6)
                return


def install(folder, remove=False):
    """Add the two lines to (or take them off) LORD's 3RDPARTY.DAT, with
    FORGE.IGM beside it: LORD only sends players to a program it can
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
            f.write(b"Brakka's Forge: a flux/bbs native module ([dos] native).\r\n")
    open(path, "wb").write(("\r\n".join(out) + "\r\n").encode("cp437"))
    print(("took Brakka's Forge off " if remove else "added Brakka's Forge to ") + path)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("install", "uninstall"):
        install(sys.argv[2] if len(sys.argv) > 2 else ".", sys.argv[1] == "uninstall")
    else:
        main()

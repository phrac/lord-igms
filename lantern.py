"""The Velvet Lantern: a LORD in-game module, native to flux/bbs.

A house of ill repute down the alley behind the Inn, kept by Madam
Rouge. A visit, once a day and for a price, teaches a player a thing or
two: Violet (or, for a woman, Seth Able the bard) likes someone with a
little experience, so the first visits of a week make them more
charming, and count in LORD's own tally of lays. But she doesn't want a
regular of the Velvet Lantern: past two visits in seven days the town
starts talking, and past three it reaches her: charm lost, a line in the
Daily Happenings, and she won't look at them today. A fairy from the jar
(fairies.py) can keep a lookout for one visit, so nobody sees them go
in. A married player risks their spouse finding out.

With LORD's clean mode on (the SysOp's choice, in LORDCFG) it's a dance
hall instead, with the same rules and none of the winking, and LORD's
tally isn't touched. Visits are kept in LANTERN.DAT in LORD's folder.

Install: this folder where the board's `[dos.native] "*"` points
(README.md), then `python3 lantern.py install /path/to/LORD` adds it to LORD's
3RDPARTY.DAT, with the LANTERN.IGM LORD looks for (`uninstall` takes
them off again).
"""
import json
import os
import random
import sys
import time

NAME = "LANTERN"
SHOWN = "`0T`2he `0V`2elvet `0L`2antern"
STATE = "LANTERN.DAT"
WEEK = 7
# Visits in a week: up to this many help; one more and the town talks;
# past that, she hears.
HELPS = 2


def today():
    return time.strftime("%Y-%m-%d")


def days_ago(day):
    try:
        return int((time.time() - time.mktime(time.strptime(day, "%Y-%m-%d"))) // 86400)
    except ValueError:
        return 999


def load():
    try:
        s = json.load(open(STATE))
    except (OSError, ValueError):
        s = {}
    s.setdefault("players", {})
    return s


def save(s):
    tmp = STATE + ".new"
    with open(tmp, "w") as f:
        json.dump(s, f)
    os.replace(tmp, STATE)


def mine(s, g):
    p = s["players"].get(str(g.account))
    if not p or p.get("name") != g.player.name:
        p = {"name": g.player.name, "visits": []}
        s["players"][str(g.account)] = p
    p["visits"] = [d for d in p["visits"] if days_ago(d) < WEEK]
    return p


def clean_mode(g):
    """LORD's clean mode (INFO's last line), set by the SysOp."""
    info = getattr(g, "_info", [])
    return any(l.strip().upper() == "CLEAN MODE ON" for l in info)


def price(g):
    return 40 + 40 * max(1, g.player.level)


class Words:
    """What's said, by the house's kind (clean mode a dance hall)."""

    def __init__(self, g):
        self.clean = clean_mode(g)
        self.female = g.player.female
        self.sweet = "Seth Able" if self.female else "Violet"
        self.she = "he" if self.female else "she"
        self.her = "him" if self.female else "her"
        # The player: a woman or a man.
        self.kind = "woman" if self.female else "man"
        self.they = "she" if self.female else "he"
        if self.clean:
            self.place = "the Velvet Lantern dance hall"
            self.title = "The Velvet Lantern"
            self.intro = [
                "Down the alley behind the Inn, music spills out of a lantern-lit",
                "hall.  `0Madam Rouge`2 teaches the realm's finest to dance, for a fee,",
                "and keeps a very good memory for faces.",
            ]
            self.visit = "Take a lesson"
            self.doing = [
                "Madam Rouge pairs you with a partner who has clearly done this",
                "before.  Three hours later your feet know things they didn't.",
            ]
        else:
            self.place = "the Velvet Lantern"
            self.title = "The Velvet Lantern"
            who = "gentleman" if self.female else "lady"
            self.intro = [
                "Down the alley behind the Inn, a red lantern sways over a door with",
                f"no sign.  Inside, velvet and perfume, and `0Madam Rouge`2, who has",
                "seen everything twice and charges for both.",
            ]
            self.visit = f"Spend an evening with a {who} of the house"
            self.doing = [
                f"Madam Rouge introduces you to a {who} who has clearly done this",
                "before.  The door closes.  You come out the next morning knowing",
                "things you didn't, and walking a little differently.",
            ]


def visit(g, s):
    import fairies

    w, p, me = Words(g), g.player, mine(s, g)
    cost = price(g)
    if today() in me["visits"]:
        g.say()
        g.say("  `0\"Once a night, love.  Even the best need their rest.\"")
        g.say()
        g.more()
        return
    if p.gold < cost:
        g.say()
        g.say(f"  `0\"{cost:,} gold, love.  We don't run tabs.\"")
        g.say()
        g.more()
        return
    p.gold -= cost
    me["visits"].append(today())
    save(s)
    g.save()
    n = len(me["visits"])
    g.title(w.title)
    g.say(f"  `2You pay Madam Rouge `${cost:,} gold`2 (`${p.gold:,}`2 left).")
    g.say()
    # Seen going in?  Not with a fairy keeping watch.
    lookout = None
    if n > HELPS and fairies.count(g):
        lookout = fairies.offer(g, "Have her keep a lookout, so nobody sees you go in?")
        if lookout:
            g.say(f"  `#{lookout}`2 perches on the lantern, glaring at the street.")
            g.say()
    for line in w.doing:
        g.say("  `2" + line)
    g.say()
    if n <= HELPS or lookout:
        p.charm += 1
        if not w.clean:
            p.lays += 1
        g.say(f"  `2{w.sweet} likes a {w.kind} who knows what {w.they}'s doing: `0+1 charm`2.")
        if lookout:
            g.say(f"  `2And thanks to `#{lookout}`2, nobody saw a thing.  She's gone off to tell")
            g.say("  `2the other fairies everything, though.")
    elif n == HELPS + 1:
        g.say("  `2You feel very worldly.  On the way out, though, you catch the")
        g.say("  `2baker's wife watching from across the street.  People are starting")
        g.say(f"  `2to talk.  `0(No charm from this one.  Go easy, or {w.sweet} hears.)")
    else:
        lost = min(p.charm, 2 + (n - HELPS - 2))
        p.charm -= lost
        p.seen_violet = 5
        g.say(f"  `2It's all over town by noon, and {w.sweet} hears it from three people")
        g.say(f"  `2before lunch.  {w.sweet} doesn't want a regular of {w.place}.")
        g.say(f"  `4-{lost} charm`2, and {w.she} won't look at you today.")
        g.news(f"`0{w.sweet} `2heard `0{p.name} `2has been a regular at `0{w.place}`2.  {w.she.capitalize()}'s not impressed.")
    if p.married != -1 and not w.clean and not lookout and random.random() < 0.5:
        lost = min(p.charm, 3)
        p.charm -= lost
        g.say()
        g.say("  `2And your spouse found out.  The dishes are still being thrown.")
        g.say(f"  `4-{lost} charm`2.")
        g.news(f"`0{p.name}`2's spouse caught them coming out of `0{w.place}`2.")
    save(s)
    g.say()
    g.more()


SAYS = [
    "\"Everyone comes to the Lantern eventually.  Even kings.  ESPECIALLY kings.\"",
    "\"A little experience never hurt anyone's chances at the Inn.  A lot does.\"",
    "\"Discretion is what you're paying for, love.  The rest is extra.\"",
    "\"Barak's mother?  We don't talk about Barak's mother.\"",
    "\"Twice a week is worldly.  Every night is a reputation.\"",
    "\"The fairies are the worst gossips in the realm.  Unless they like you.\"",
]
SAYS_CLEAN = [
    "\"Everyone comes to dance eventually.  Even kings.  ESPECIALLY kings.\"",
    "\"A few lessons and they'll notice you at the Inn.  Too many and they'll talk.\"",
    "\"Mind your partner's feet, love.  They're paying too.\"",
    "\"Twice a week is graceful.  Every night is a reputation.\"",
]


def main():
    import fairies
    import lordigm

    with lordigm.Igm() as g:
        while True:
            s = load()
            w, me = Words(g), mine(s, g)
            n = len(me["visits"])
            g.title(w.title)
            for line in w.intro:
                g.say("  `2" + line)
            g.say()
            if n:
                g.say(f"  `2Visits this week: `0{n}`2.  " + ("Madam Rouge winks." if n <= HELPS else "Madam Rouge raises an eyebrow."))
            if fairies.count(g):
                g.say(f"  `2Fairies in your jar: `#{', '.join(fairies.jar(g))}`2.")
            g.say()
            done = today() in me["visits"]
            g.say(f"  `2(`0V`2)isit: {w.visit.lower()}   `2({price(g):,} gold" + (", done tonight)" if done else ")"))
            g.say("  `2(`0T`2)alk to Madam Rouge")
            g.say("  `2(`0R`2)eturn to town")
            g.say()
            g.say(f"  `2You have `${g.player.gold:,} gold`2 on hand.")
            k = g.key("  `2Your choice? [`0R`2] : ", "VTR", "R")
            if k == "V":
                visit(g, s)
            elif k == "T":
                g.say()
                g.say("  `0" + random.choice(SAYS_CLEAN if w.clean else SAYS))
                g.say()
                g.more()
            else:
                g.say()
                g.say("  `2You slip back out into the alley.")
                g.pause(0.6)
                return


def install(folder, remove=False):
    """Add the two lines to (or take them off) LORD's 3RDPARTY.DAT, with
    LANTERN.IGM beside it: LORD only sends players to a program it can
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
            f.write(b"The Velvet Lantern: a flux/bbs native module ([dos] native).\r\n")
    open(path, "wb").write(("\r\n".join(out) + "\r\n").encode("cp437"))
    print(("took The Velvet Lantern off " if remove else "added The Velvet Lantern to ") + path)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("install", "uninstall"):
        install(sys.argv[2] if len(sys.argv) > 2 else ".", sys.argv[1] == "uninstall")
    else:
        main()

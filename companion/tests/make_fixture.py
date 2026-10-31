"""Generate tests/fixtures/Silvercord.lua by playing scripted sessions
through the real addon code (Lua 5.1 + WoW stub).

The output is exactly what the addon would write. Re-run after changing the
addon:  python tests/make_fixture.py

Scenario (realm "Ashvale", WoW: Forever launch week):
  Grukk, Orc Warrior. A Mainline-style client, so no combat log.
    #1 Nov 4  Valley of Trials, levels 1-6, a few quests, an inferred death, notes
    #2 Nov 5  4-minute repair stop. Trivial.
    #3 Nov 6  Orgrimmar, then Ragefire Chasm with a group, bosses, a death, levels up
    #4 Nov 7  The Barrens grind, an inferred rare kill. Hits the event cap (lowered
              here to keep the fixture readable).
  Zen'jah, Troll Priest. Simulates a client that still has the combat log.
    #1 Nov 8  Echo Isles, a combat-log death. The session never got a clean stop.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harness import Client  # noqa: E402

OUT = Path(__file__).parent / "fixtures" / "Silvercord.lua"
EST = timezone(timedelta(hours=-5))


class Play:
    def __init__(self, sv: str | None, player: dict, start: datetime, *, level: int, money: int,
                 zone: str, sub: str | None, combatlog: bool = False, cap: int | None = None):
        self.c = Client(combatlog=combatlog, saved_variables=sv)
        w = self.c.g.WOW
        for k, v in player.items():
            w.player[k] = v
        w.now = int(start.timestamp())
        w.level, w.money, w.zone, w.sub = level, money, zone, sub
        if cap:
            self.c.S.MAX_EVENTS = cap
            self.c.S.HARD_MAX_EVENTS = cap + 25
        self.c.login()

    @property
    def w(self):
        return self.c.g.WOW

    def wait(self, minutes: float):
        self.w.now = self.w.now + int(minutes * 60)
        return self

    def zone(self, zone, sub=None, instance=None):
        self.w.zone, self.w.sub = zone, sub
        self.w.instance = self.c.lua.table_from([instance, "party"] if instance else [None, "none"])
        self.c.fire("ZONE_CHANGED_NEW_AREA")
        return self

    def sub(self, sub):
        self.w.sub = sub
        self.c.fire("ZONE_CHANGED")
        return self

    def level(self, n):
        self.w.level = n
        self.c.fire("PLAYER_LEVEL_UP", n)
        return self

    def quest(self, title, qid, xp=0, money=0):
        self.w.questTitle = title
        self.c.fire("QUEST_COMPLETE")
        self.c.fire("QUEST_TURNED_IN", qid, xp, money)
        if money:
            self.money(money)
        return self

    def loot(self, item, q, n=1, item_id=1, pushed=False):
        link = self.c.g.Link(item, q, item_id)
        verb = "item" if pushed else "loot"
        suffix = f"x{n}." if n > 1 else "."
        self.c.fire("CHAT_MSG_LOOT", f"You receive {verb}: {link}{suffix}")
        return self

    def money(self, delta):
        self.w.money = self.w.money + delta
        self.c.fire("PLAYER_MONEY")
        return self

    def target(self, name, guid, level, classification="normal", hostile=True):
        self.w.units["target"] = self.c.lua.table_from(
            {"name": name, "guid": guid, "hostile": hostile, "level": level,
             "classification": classification})
        self.c.fire("PLAYER_TARGET_CHANGED")
        return self

    def fight(self):
        self.w.inCombat = True
        self.c.fire("PLAYER_REGEN_DISABLED")
        return self

    def target_dies(self):
        self.w.units["target"]["dead"] = True
        self.c.fire("UNIT_HEALTH", "target")
        self.w.inCombat = False
        self.c.fire("PLAYER_REGEN_ENABLED")
        self.w.units["target"] = None
        return self

    def hit_by(self, source, spell=None, sub="SPELL_DAMAGE"):
        me = "Player-1-" + self.w.player.name
        payload = [0, sub, False, "Creature-0-9", source, 0, 0, me, self.w.player.name, 0, 0]
        if spell:
            payload += [1, spell]
        self.w.cleu = self.c.lua.table_from(payload)
        self.c.fire("COMBAT_LOG_EVENT_UNFILTERED")
        return self

    def die(self):
        self.w.inCombat = False
        self.c.fire("PLAYER_DEAD")
        return self

    def group(self, members):
        self.w.group = self.c.lua.table_from([self.c.lua.table_from(m) for m in members])
        self.c.fire("GROUP_ROSTER_UPDATE")
        return self

    def boss(self, name, eid):
        self.c.fire("ENCOUNTER_START", eid, name, 1, 5)
        self.c.fire("ENCOUNTER_END", eid, name, 1, 5, 1)
        return self

    def note(self, text):
        self.c.slash(text)
        return self

    def logout(self, clean=True) -> str:
        if clean:
            self.c.fire("PLAYER_LOGOUT")
        return self.c.saved_variables()


GRUKK = {"name": "Grukk", "class": "Warrior", "classToken": "WARRIOR", "race": "Orc",
         "raceToken": "Orc", "faction": "Horde", "realm": "Ashvale"}
ZENJAH = {"name": "Zen'jah", "class": "Priest", "classToken": "PRIEST", "race": "Troll",
          "raceToken": "Troll", "faction": "Horde", "realm": "Ashvale"}
PARTY = [
    {"name": "Thrallina", "class": "SHAMAN", "level": 13},
    {"name": "Mokvar", "class": "ROGUE", "level": 12},
    {"name": "Seylah", "class": "MAGE", "level": 14},
    {"name": "Brekk", "class": "WARLOCK", "level": 13},
]


def build() -> str:
    # --- Grukk #1: launch night ---------------------------------------------
    p = Play(None, GRUKK, datetime(2026, 11, 4, 19, 6, tzinfo=EST),
             level=1, money=0, zone="Durotar", sub="Valley of Trials")
    p.wait(2).note("Launch night. The queue was 3 hours. I have never been more ready to punch a boar.")
    p.wait(4).quest("Your Place In The World", 4641, 40)
    p.wait(9).quest("Cutting Teeth", 788, 170).level(2)
    p.wait(12).quest("Sarkoth", 790, 225).loot("Sarkoth's Mangled Claw", 1, pushed=True)
    p.wait(3).quest("Sarkoth", 804, 250, money=35).level(3)
    p.wait(14).quest("Vile Familiars", 792, 340).loot("Rugged Leather Pants", 2, item_id=2316, pushed=True)
    p.wait(6).level(4).sub("Burning Blade Coven")
    p.wait(8).target("Yarrog Baneshadow", "Creature-0-3", 5).fight().wait(1).die()
    p.note("Yarrog Baneshadow is a coward who hides in a cave full of his friends.")
    p.wait(5).target("Yarrog Baneshadow", "Creature-0-4", 5).fight().wait(1).target_dies()
    p.wait(1).loot("Burning Blade Medallion", 1)
    p.wait(6).quest("Burning Blade Medallion", 794, 450, money=95).level(5)
    p.loot("Tribal Warrior's Shield", 2, item_id=2489, pushed=True)
    p.wait(15).zone("Durotar", "Razor Hill").quest("Report to Sen'jin Village", 805, 50)
    p.wait(22).sub("Sen'jin Village").level(6)
    p.wait(8).money(-120).note("Trained Thunder Clap. The boars of Durotar should be worried.")
    p.wait(4)
    sv = p.logout()

    # --- Grukk #2: a quick repair stop (trivial) ------------------------------
    p = Play(sv, GRUKK, datetime(2026, 11, 5, 20, 1, tzinfo=EST),
             level=6, money=455, zone="Durotar", sub="Razor Hill")
    p.wait(2).money(-62).wait(2)
    sv = p.logout()

    # --- Grukk #3: Ragefire Chasm -------------------------------------------
    p = Play(sv, GRUKK, datetime(2026, 11, 6, 18, 32, tzinfo=EST),
             level=12, money=8130, zone="Durotar", sub="Razor Hill")
    p.wait(10).zone("Orgrimmar", "Valley of Strength").sub("Cleft of Shadow")
    p.wait(6).group(PARTY[:2]).wait(4).group(PARTY)
    p.wait(3).zone("Ragefire Chasm", None, instance="Ragefire Chasm")
    p.wait(12).boss("Oggleflint", 1443).loot("Ragefire Wand", 2, item_id=14149)
    p.wait(15).note("Brekk pulled the whole room. Brekk is no longer allowed to touch things.")
    p.target("Ragefire Trogg", "Creature-0-11", 11).fight().wait(1).die()
    p.wait(6).boss("Taragaman the Hungerer", 1444).loot("Cursed Felblade", 3, item_id=14145)
    p.level(13)
    p.wait(18).boss("Jergosh the Invoker", 1445)
    p.wait(9).boss("Bazzalan", 1446).loot("Bloodpike", 2, item_id=14150)
    p.money(1840)
    p.wait(4).zone("Orgrimmar", "Valley of Strength")
    p.group(PARTY[:1]).wait(2).group([])
    p.wait(20).money(-4500).note("Bought a better axe from the Valley of Honor. Spent most of my gold. Worth it.")
    p.wait(26).zone("Durotar", "Razor Hill").level(14)
    p.wait(15)
    sv = p.logout()

    # --- Grukk #4: Barrens grind (event cap lowered so the fixture stays small)
    p = Play(sv, GRUKK, datetime(2026, 11, 7, 19, 2, tzinfo=EST),
             level=14, money=4890, zone="Durotar", sub="Razor Hill", cap=20)
    p.wait(8).zone("The Barrens", "The Crossroads")
    p.quest("Crossroads Conscription", 842, 420, money=175)
    nooks = ["Far Watch Post", "The Dry Hills", "Lushwater Oasis", "Thorn Hill", "The Stagnant Oasis",
             "Forgotten Pools", "The Sludge Fen", "Grol'dom Farm", "Dreadmist Peak", "The Mor'shan Rampart",
             "Boulder Lode Mine", "Ratchet", "The Merchant Coast", "Northwatch Hold", "Southfury River"]
    for i, nook in enumerate(nooks):
        p.wait(6).sub(nook)
        p.loot("Kodo Meat", 1)
        p.loot("Plainstrider Beak" if i % 2 else "Zhevra Hooves", 1)
        if i % 3 == 0:
            p.loot("Raptor Hide Belt" if i % 2 else "Barbaric Cloth Robe", 2, item_id=4000 + i)
        if i == 5:
            p.level(15)
        if i == 8:
            p.target("Humar the Pridelord", "Creature-0-77", 23, "rare").fight().wait(2).target_dies()
            p.note("Humar the Pridelord, level 23, fell to a level 15 orc. I will be insufferable about this.")
        p.money(30 + i * 7)
    p.wait(10).quest("Plainstrider Menace", 844, 610).level(16)
    p.wait(5)
    sv = p.logout()

    # --- Zen'jah #1: combat-log client, ends without a clean logout ---------
    p = Play(sv, ZENJAH, datetime(2026, 11, 8, 21, 15, tzinfo=EST),
             level=8, money=1210, zone="Durotar", sub="Sen'jin Village", combatlog=True)
    p.wait(5).sub("Echo Isles").note("Zen’jah’s first rule of the Echo Isles: never trust a naga with a smile.")
    p.wait(7).quest("Minshina's Skull", 808, 520).loot("Voodoo Charm", 2, item_id=4421, pushed=True)
    p.wait(9).target("Zalazane", "Creature-0-90", 12, "elite").fight()
    p.hit_by("Zalazane", "Shadow Bolt").die()
    p.wait(6).level(9)
    p.wait(10)
    # Simulate a session that never logged out cleanly (e.g. the file was
    # copied mid-session, or written by an older addon build): no stop time.
    return p.logout(clean=False)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

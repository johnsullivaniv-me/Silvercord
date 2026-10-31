"""Offline tests for the Lua addon, run inside real Lua 5.1 via lupa.

These stub the WoW API (tests/wowstub.lua) and fire fake events. They
can't prove the addon works in the live client, but they catch logic bugs,
Lua errors, and SavedVariables-shape regressions before launch day.
"""

from pathlib import Path

import pytest

lupa = pytest.importorskip("lupa")

from silvercord.luaparse import parse_saved_variables  # noqa: E402

from harness import Client  # noqa: E402


@pytest.fixture
def wow():
    c = Client()
    c.login()
    return c


def test_login_starts_session_and_logs_zone(wow):
    assert wow.S.session.id == 1
    ev = wow.events()
    assert ev[0]["k"] == "session" and ev[0]["event"] == "start"
    zone = [e for e in ev if e["k"] == "zone"][0]
    assert zone["zone"] == "Durotar" and zone["first"] is True
    assert any(e["k"] == "subzone" and e["sub"] == "Valley of Trials" for e in ev)


def test_unknown_events_are_recorded_not_fatal(wow):
    assert wow.S.caps["BOSS_KILL"] is False
    assert wow.S.caps["PLAYER_DEAD"] is True
    assert wow.S.caps.combatlog is False


def test_no_chat_output_except_chron(wow):
    wow.fire("PLAYER_LEVEL_UP", 2)
    wow.fire("ZONE_CHANGED_NEW_AREA")
    assert wow.printed() == []
    wow.slash("Found a suspicious boar. Named him Kevin.")
    assert len(wow.printed()) == 1
    note = wow.events()[-1]
    assert note["k"] == "note" and "Kevin" in note["text"]


def test_level_quest_and_loot(wow):
    wow.fire("PLAYER_LEVEL_UP", 2)
    wow.g.WOW.questTitle = "Cutting Teeth"
    wow.fire("QUEST_COMPLETE")
    wow.fire("QUEST_TURNED_IN", 788, 170, 0)
    wow.fire("CHAT_MSG_LOOT", "You receive loot: " + wow.g.Link("Rough Boomerang", 1) + ".")
    wow.fire("CHAT_MSG_LOOT", "You receive loot: " + wow.g.Link("Scorpid Stinger", 2, 4890) + "x2.")
    wow.fire("CHAT_MSG_LOOT", "You receive item: " + wow.g.Link("Rugged Boots", 3) + ".")
    ev = wow.events()
    assert any(e["k"] == "level" and e["level"] == 2 for e in ev)
    quest = [e for e in ev if e["k"] == "quest"][0]
    assert quest["title"] == "Cutting Teeth" and quest["id"] == 788
    loot = [e for e in ev if e["k"] == "loot"]
    assert [l["item"] for l in loot] == ["Scorpid Stinger", "Rugged Boots"]
    assert loot[0]["n"] == 2 and loot[0]["id"] == 4890 and loot[1]["how"] == "received"


def test_death_without_combat_log_is_inferred(wow):
    wow.g.WOW.units["target"] = wow.lua.table_from(
        {"name": "Vile Familiar", "guid": "Creature-1", "hostile": True, "level": 3}
    )
    wow.fire("PLAYER_TARGET_CHANGED")
    wow.fire("PLAYER_DEAD")
    death = wow.events()[-1]
    assert death["k"] == "death"
    assert death["killer"] == "Vile Familiar" and death["inferred"] is True


def test_death_with_combat_log_is_not_inferred():
    c = Client(combatlog=True)
    c.login()
    assert c.S.caps.combatlog is True
    c.run('WOW.cleu = {0, "SPELL_DAMAGE", false, "Creature-9", "Gazz\'uz", 0, 0, '
          '"Player-1-Grukk", "Grukk", 0, 0, 172, "Corruption"}')
    c.fire("COMBAT_LOG_EVENT_UNFILTERED")
    c.fire("PLAYER_DEAD")
    death = c.events()[-1]
    assert death["killer"] == "Gazz'uz" and death["spell"] == "Corruption"
    assert death["source"] == "combatlog" and "inferred" not in death


def test_boss_kill_logged_once(wow):
    wow.g.WOW.instance = wow.lua.table_from(["Ragefire Chasm", "party"])
    wow.fire("ZONE_CHANGED_NEW_AREA")
    wow.fire("ENCOUNTER_END", 1443, "Taragaman the Hungerer", 1, 5, 1)
    wow.fire("ENCOUNTER_END", 1443, "Taragaman the Hungerer", 1, 5, 1)
    wow.fire("ENCOUNTER_END", 1444, "Jergosh the Invoker", 1, 5, 0)  # wipe
    ev = wow.events()
    assert [e["name"] for e in ev if e["k"] == "dungeon"] == ["Ragefire Chasm"]
    bosses = [e for e in ev if e["k"] == "boss"]
    assert len(bosses) == 1 and bosses[0]["dungeon"] == "Ragefire Chasm"


def test_elite_kill_fallback_is_inferred(wow):
    wow.g.WOW.units["target"] = wow.lua.table_from(
        {"name": "Kolkar Pack Runner", "guid": "Creature-77", "hostile": True,
         "level": 14, "classification": "elite"}
    )
    wow.g.WOW.inCombat = True
    wow.fire("PLAYER_TARGET_CHANGED")
    wow.fire("PLAYER_REGEN_DISABLED")
    wow.g.WOW.units["target"]["dead"] = True
    wow.fire("UNIT_HEALTH", "target")
    kills = [e for e in wow.events() if e["k"] == "kill"]
    assert len(kills) == 1 and kills[0]["inferred"] is True and kills[0]["class"] == "elite"


def test_money_and_group(wow):
    wow.g.WOW.money = 25000
    wow.fire("PLAYER_MONEY")
    wow.g.WOW.money = 24000
    wow.fire("PLAYER_MONEY")
    assert wow.S.session.gained == 25000 and wow.S.session.lost == 1000
    assert [e["delta"] for e in wow.events() if e["k"] == "money"] == [25000]

    wow.g.WOW.group = wow.lua.table_from(
        [wow.lua.table_from({"name": "Thrallina", "class": "SHAMAN", "level": 15})]
    )
    wow.fire("GROUP_ROSTER_UPDATE")
    wow.g.WOW.group = wow.lua.table_from([])
    wow.fire("GROUP_ROSTER_UPDATE")
    grp = [(e["event"], e["name"]) for e in wow.events() if e["k"] == "group"]
    assert grp == [("join", "Thrallina"), ("leave", "Thrallina")]
    assert wow.S.session.party["Thrallina"]["class"] == "SHAMAN"


def test_logout_then_reload_resumes_same_session(wow):
    wow.fire("PLAYER_LOGOUT")
    assert wow.S.session.stop is not None
    wow.tick(30)
    wow.fire("PLAYER_LOGIN")
    assert wow.S.session.id == 1 and wow.S.session.stop is None
    assert wow.S.session.resumed == 1
    wow.fire("PLAYER_LOGOUT")
    wow.tick(3600)
    wow.fire("PLAYER_LOGIN")
    assert wow.S.session.id == 2


def test_event_cap_keeps_priority_kinds(wow):
    for i in range(450):
        wow.g.WOW.sub = f"Nook {i}"
        wow.fire("ZONE_CHANGED")
    wow.fire("PLAYER_LEVEL_UP", 5)
    s = wow.S.session
    assert s.truncated is True
    kinds = wow.kinds()
    assert len(kinds) == wow.S.MAX_EVENTS + 1 and kinds[-1] == "level"


def test_handler_errors_are_contained(wow):
    wow.run("GetMoney = function() error('boom') end")
    wow.fire("PLAYER_MONEY")  # S.Try swallows it; nothing raised
    wow.run("GetRealZoneText = nil")
    wow.fire("ZONE_CHANGED_NEW_AREA")  # missing API: no error


def test_saved_variables_round_trip_through_python_parser(wow):
    wow.fire("PLAYER_LEVEL_UP", 2)
    wow.slash('He said "lok\'tar" and left.\nNew line.')
    wow.fire("PLAYER_LOGOUT")
    db = parse_saved_variables(wow.saved_variables())["SilvercordDB"]
    char = db["chars"]["Silverhand-Grukk"]
    assert char["class"] == "WARRIOR"
    sess = char["sessions"][0]
    assert sess["stop"] is not None and sess["endLevel"] == 2
    note = [e for e in sess["events"] if e["k"] == "note"][0]
    assert note["text"] == 'He said "lok\'tar" and left.\nNew line.'

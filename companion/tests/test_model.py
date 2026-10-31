from pathlib import Path

import pytest

from silvercord.model import build_facts, describe_event, fmt_money, load_sessions
from silvercord.pipeline import read_db

FIXTURE = Path(__file__).parent / "fixtures" / "Silvercord.lua"


@pytest.fixture(scope="module")
def sessions():
    return {s.key: s for s in load_sessions(read_db(FIXTURE))}


def test_fmt_money():
    assert fmt_money(0) == "0c"
    assert fmt_money(10203) == "1g 2s 3c"
    assert fmt_money(-4500) == "45s"


def test_sessions_loaded_and_normalized(sessions):
    assert list(sessions) == [
        "Ashvale-Grukk:1", "Ashvale-Grukk:2", "Ashvale-Grukk:3", "Ashvale-Grukk:4",
        "Ashvale-Zen'jah:1",
    ]
    g1 = sessions["Ashvale-Grukk:1"]
    assert (g1.start_level, g1.end_level) == (1, 6)
    assert g1.cls == "WARRIOR" and not g1.abrupt


def test_trivial_detection(sessions):
    assert sessions["Ashvale-Grukk:2"].is_trivial(10)
    assert not sessions["Ashvale-Grukk:2"].is_trivial(3)  # longer than 3 minutes
    assert not sessions["Ashvale-Grukk:1"].is_trivial(10)


def test_abrupt_session_closed_at_last_event(sessions):
    z = sessions["Ashvale-Zen'jah:1"]
    assert z.abrupt
    assert z.stop == max(e["t"] for e in z.events)


def test_truncated_flagged_in_facts(sessions):
    facts = build_facts(sessions["Ashvale-Grukk:4"])
    assert "size cap" in facts and "9 minor events" in facts


def test_facts_include_notes_party_and_hedging(sessions):
    facts = build_facts(sessions["Ashvale-Grukk:3"], sessions["Ashvale-Grukk:1"])
    assert '"Brekk pulled the whole room. Brekk is no longer allowed to touch things."' in facts
    assert "Thrallina (Shaman, level 13)" in facts
    assert "Ragefire Trogg (possibly; the killer is a guess" in facts
    assert "Defeated the boss Taragaman the Hungerer in Ragefire Chasm (confirmed)" in facts
    assert "went unrecorded" in facts  # level 6 -> 12 gap is called out, not filled in
    assert "combat log was unavailable" in facts


def test_combat_log_death_not_hedged(sessions):
    facts = build_facts(sessions["Ashvale-Zen'jah:1"])
    assert "Died by Shadow Bolt from Zalazane in Echo Isles." in facts
    assert "combat log was unavailable" not in facts
    assert "ended abruptly" in facts
    assert "Zen’jah’s first rule" in facts


def test_facts_contain_nothing_unlogged(sessions):
    """Every proper noun-ish token in the facts should come from the raw data."""
    s = sessions["Ashvale-Grukk:1"]
    raw = repr(s.raw) + s.name + s.realm
    facts = build_facts(s)
    for item in ["Rugged Leather Pants", "Tribal Warrior's Shield", "Yarrog Baneshadow", "Sen'jin Village"]:
        assert item in facts and item in raw


def test_describe_event_variants():
    assert describe_event({"k": "death"}) == "Died (cause not recorded)."
    assert "falling damage" in describe_event({"k": "death", "killer": "Falling", "env": True})
    assert describe_event({"k": "quest", "id": 5}) == 'Turned in the quest "quest #5".'
    assert describe_event({"k": "note", "text": "x"}) is None
    assert describe_event({"k": "kill", "name": "X", "class": "elite", "inferred": True}).endswith(
        "(possibly; inferred, not confirmed).")

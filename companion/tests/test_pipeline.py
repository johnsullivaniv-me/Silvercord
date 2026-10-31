import json
import shutil
from pathlib import Path

import pytest

from silvercord.pipeline import run
from silvercord.writer import Entry

FIXTURE = Path(__file__).parent / "fixtures" / "Silvercord.lua"


class FakeChronicler:
    def __init__(self):
        self.calls = []

    def write(self, facts):
        self.calls.append(facts)
        body = "In the chronicle it is written that the hero did things. " * 18
        return Entry(text=body.strip(), words=200, model="fake-model", attempts=1)


@pytest.fixture
def sv(tmp_path):
    p = tmp_path / "Silvercord.lua"
    shutil.copy(FIXTURE, p)
    return p


def test_first_run_writes_entries_index_and_state(sv, tmp_path):
    out = tmp_path / "chronicle"
    fake = FakeChronicler()
    rep = run(sv, out, chronicler=fake, log=lambda *_: None)
    assert len(rep.written) == 4 and rep.trivial == ["Ashvale-Grukk:2"] and not rep.failed
    assert len(fake.calls) == 4

    files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*.md"))
    assert "index.md" in files
    entry_files = [f for f in files if f != "index.md"]
    assert len(entry_files) == 4
    assert any(f.startswith("Grukk/") and f.endswith("-session-3.md") for f in entry_files)
    assert any(f.startswith("Zen'jah/") for f in entry_files)

    entry = next(out.glob("Grukk/*-session-3.md")).read_text(encoding="utf-8")
    assert entry.startswith("---\ncharacter: \"Grukk\"")
    assert "# Grukk," in entry and "the hero did things" in entry

    index = (out / "index.md").read_text(encoding="utf-8")
    assert "## Grukk of Ashvale (Orc Warrior)" in index
    assert "Session 2 (no entry)" in index
    assert "[Session 3](Grukk/" in index

    raw = list((out / "Grukk" / "raw").glob("*.json"))
    assert len(raw) == 4  # including the trivial one

    state = json.loads((out / ".silvercord-state.json").read_text())
    assert len(state["sessions"]) == 5


def test_rerun_is_idempotent(sv, tmp_path):
    out = tmp_path / "chronicle"
    run(sv, out, chronicler=FakeChronicler(), log=lambda *_: None)
    fake = FakeChronicler()
    rep = run(sv, out, chronicler=fake, log=lambda *_: None)
    assert fake.calls == [] and rep.unchanged == 5 and not rep.written


def test_changed_session_is_revised(sv, tmp_path):
    out = tmp_path / "chronicle"
    run(sv, out, chronicler=FakeChronicler(), log=lambda *_: None)
    # Simulate the addon appending to session 4 after a /reload mid-play.
    text = sv.read_text(encoding="utf-8").replace(
        "fell to a level 15 orc", "fell to a level 15 orc, twice", 1)
    sv.write_text(text, encoding="utf-8")
    fake = FakeChronicler()
    rep = run(sv, out, chronicler=fake, log=lambda *_: None)
    assert rep.revised == ["Ashvale-Grukk:4"] and len(fake.calls) == 1


def test_latest_session_skipped_while_game_running(sv, tmp_path):
    rep = run(sv, tmp_path / "c", chronicler=FakeChronicler(), game_running=True, log=lambda *_: None)
    assert sorted(rep.skipped_active) == ["Ashvale-Grukk:4", "Ashvale-Zen'jah:1"]


def test_failures_dont_stop_the_run(sv, tmp_path):
    class Flaky(FakeChronicler):
        def write(self, facts):
            if "Session #3" in facts:
                raise RuntimeError("overloaded")
            return super().write(facts)

    out = tmp_path / "c"
    rep = run(sv, out, chronicler=Flaky(), log=lambda *_: None)
    assert rep.failed and rep.failed[0][0] == "Ashvale-Grukk:3"
    assert len(rep.written) == 3
    # the failed one is retried next time
    fake = FakeChronicler()
    rep2 = run(sv, out, chronicler=fake, log=lambda *_: None)
    assert rep2.written == ["Ashvale-Grukk:3"]


def test_dry_run_writes_nothing(sv, tmp_path):
    out = tmp_path / "c"
    logs = []
    run(sv, out, dry_run=True, log=logs.append)
    assert not out.exists()
    assert any("Timeline" in line for line in logs)


def test_force_rewrites_everything(sv, tmp_path):
    out = tmp_path / "c"
    run(sv, out, chronicler=FakeChronicler(), log=lambda *_: None)
    fake = FakeChronicler()
    run(sv, out, chronicler=fake, force=True, log=lambda *_: None)
    assert len(fake.calls) == 5  # force also writes the trivial session


def test_fatal_error_stops_run(sv, tmp_path):
    from silvercord.writer import WriterError

    class NoKey(FakeChronicler):
        def write(self, facts):
            self.calls.append(facts)
            raise WriterError("no key", fatal=True)

    fake = NoKey()
    rep = run(sv, tmp_path / "c", chronicler=fake, log=lambda *_: None)
    assert len(fake.calls) == 1 and len(rep.failed) == 1

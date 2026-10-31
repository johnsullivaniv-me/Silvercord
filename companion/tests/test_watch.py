import os
import time

from silvercord import watch as watch_mod


def test_watch_runs_after_file_settles_and_game_closes(tmp_path, monkeypatch):
    sv = tmp_path / "Silvercord.lua"
    sv.write_text("x")
    old = time.time() - 100
    os.utime(sv, (old, old))

    states = iter([True, True, False])  # startup check, then: running, closed
    monkeypatch.setattr(watch_mod, "wow_running", lambda: next(states, False))
    runs = []
    ticks = {"n": 0}

    def fake_sleep(_):
        ticks["n"] += 1
        if ticks["n"] == 1:  # the client writes SavedVariables on logout
            t = time.time() - 30
            os.utime(sv, (t, t))

    watch_mod.watch(sv, lambda: runs.append(1), interval=0, settle=5,
                    log=lambda *_: None, max_cycles=4, sleep=fake_sleep)
    assert runs == [1]


def test_watch_ignores_unchanged_file(tmp_path, monkeypatch):
    sv = tmp_path / "Silvercord.lua"
    sv.write_text("x")
    monkeypatch.setattr(watch_mod, "wow_running", lambda: False)
    runs = []
    watch_mod.watch(sv, lambda: runs.append(1), interval=0, log=lambda *_: None,
                    max_cycles=3, sleep=lambda _: None)
    assert runs == []

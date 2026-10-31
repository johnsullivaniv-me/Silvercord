"""The run: read SavedVariables -> pick sessions -> write entries -> index."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .chronicle import Chronicle
from .luaparse import parse_saved_variables
from .model import Session, build_facts, load_sessions

_WOW_EXE = re.compile(r"^wow.*\.exe$", re.IGNORECASE)


def wow_running() -> bool | None:
    """True/False if we can tell, None if psutil isn't installed."""
    try:
        import psutil
    except ImportError:
        return None
    for proc in psutil.process_iter(["name"]):
        name = proc.info.get("name") or ""
        if _WOW_EXE.match(name):
            return True
    return False


def read_db(sv_path: Path) -> dict:
    text = sv_path.read_text(encoding="utf-8", errors="replace")
    data = parse_saved_variables(text)
    db = data.get("SilvercordDB")
    if not isinstance(db, dict):
        raise ValueError(f"{sv_path} has no SilvercordDB table. Is this the right file?")
    return db


@dataclass
class RunReport:
    written: list[str] = field(default_factory=list)
    revised: list[str] = field(default_factory=list)
    trivial: list[str] = field(default_factory=list)
    skipped_active: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)
    unchanged: int = 0


def run(
    sv_path: Path,
    out_dir: Path,
    *,
    chronicler=None,
    min_minutes: float = 10.0,
    force: bool = False,
    dry_run: bool = False,
    game_running: bool | None = None,
    log: Callable[[str], None] = print,
) -> RunReport:
    """Process every unwritten (or changed) session in the file.

    chronicler: object with .write(facts) -> Entry; required unless dry_run.
    game_running: if True, each character's latest session is skipped because
    it may still be in progress (SavedVariables are also written on /reload).
    """
    db = read_db(sv_path)
    sessions = load_sessions(db)
    chron = Chronicle(out_dir)
    report = RunReport()

    latest: dict[str, int] = {}
    for s in sessions:
        latest[s.char_key] = max(latest.get(s.char_key, 0), s.id)
    previous: dict[str, Session] = {}

    for s in sessions:
        prev = previous.get(s.char_key)
        if not s.is_trivial(min_minutes):
            previous[s.char_key] = s  # context for the next entry skips trivial stops
        status = chron.status(s)
        if status == "done" and not force:
            report.unchanged += 1
            continue
        if game_running and s.id == latest[s.char_key]:
            report.skipped_active.append(s.key)
            log(f"  {s.name} session {s.id}: WoW is running, so it may be unfinished. Skipping for now.")
            continue

        folder = chron.folder_for(s, sessions)
        label = f"{s.name} session {s.id} ({s.start_dt:%Y-%m-%d})"

        if s.is_trivial(min_minutes) and not force:
            if not dry_run:
                chron.archive_raw(s, folder)
                chron.record(s, folder, "trivial")
            report.trivial.append(s.key)
            log(f"  {label}: trivial (under {min_minutes:g} min, nothing notable). Index line only.")
            continue

        facts = build_facts(s, prev)
        if dry_run:
            log(f"\n===== {label}: {status} =====\n{facts}\n")
            report.written.append(s.key)
            continue

        try:
            entry = chronicler.write(facts)
        except Exception as exc:  # keep going; one bad call shouldn't sink the run
            report.failed.append((s.key, str(exc)))
            log(f"  {label}: FAILED: {exc}")
            if getattr(exc, "fatal", False):
                log("  Stopping: this error would hit every remaining session too.")
                break
            continue

        chron.archive_raw(s, folder)
        path = chron.write_entry(s, folder, entry.text, entry.model, entry.words)
        chron.save_state()  # save as we go so a crash mid-run loses nothing
        (report.revised if status == "changed" else report.written).append(s.key)
        verb = "revised" if status == "changed" else "wrote"
        log(f"  {label}: {verb} {path} ({entry.words} words)")

    if not dry_run:
        chron.save_state()
        chron.write_index()
    return report

"""Markdown output, the index, raw archives, and processed-session state."""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

from .model import Session, fmt_duration, fmt_money, title_case

STATE_FILE = ".silvercord-state.json"
STATE_VERSION = 1


def _safe(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .") or "Unknown"


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


class Chronicle:
    def __init__(self, out_dir: Path):
        self.out = Path(out_dir)
        self.state_path = self.out / STATE_FILE
        self.state = self._load_state()

    # -- state -----------------------------------------------------------

    def _load_state(self) -> dict:
        if self.state_path.is_file():
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            data.setdefault("sessions", {})
            data.setdefault("chars", {})
            return data
        return {"version": STATE_VERSION, "sessions": {}, "chars": {}}

    def save_state(self) -> None:
        _atomic_write(self.state_path, json.dumps(self.state, indent=2, sort_keys=True))

    def status(self, s: Session) -> str:
        """'new', 'done', or 'changed' (the addon added events since we wrote it)."""
        rec = self.state["sessions"].get(s.key)
        if not rec:
            return "new"
        return "done" if rec.get("hash") == s.content_hash else "changed"

    def folder_for(self, s: Session, all_sessions: list[Session]) -> str:
        chars = self.state["chars"]
        if s.char_key in chars:
            return chars[s.char_key]["folder"]
        taken = {c["folder"].lower() for c in chars.values()}
        same_name = {x.char_key for x in all_sessions if x.name == s.name}
        folder = _safe(s.name)
        if len(same_name) > 1 or folder.lower() in taken:
            folder = _safe(f"{s.name}-{s.realm}")
        chars[s.char_key] = {
            "folder": folder, "name": s.name, "realm": s.realm,
            "class": s.cls, "race": s.race,
        }
        return folder

    # -- files -----------------------------------------------------------

    def entry_path(self, s: Session, folder: str) -> Path:
        return self.out / folder / f"{s.start_dt:%Y-%m-%d}-session-{s.id}.md"

    def archive_raw(self, s: Session, folder: str) -> Path:
        p = self.out / folder / "raw" / f"session-{s.id}.json"
        payload = {"char": s.char_key, "session": s.raw}
        _atomic_write(p, json.dumps(payload, indent=2, sort_keys=True, default=str))
        return p

    def render_entry(self, s: Session, body: str, model: str) -> str:
        lv = s.start_level, s.end_level
        levels = f"{lv[0]} -> {lv[1]}" if lv[0] and lv[1] and lv[0] != lv[1] else str(lv[1] or lv[0] or "?")
        net = ("+" if s.net_money >= 0 else "-") + fmt_money(s.net_money)
        who = " ".join(x for x in (title_case(s.race), title_case(s.cls)) if x)
        front = [
            "---",
            f"character: {json.dumps(s.name)}",
            f"realm: {json.dumps(s.realm)}",
            f"session: {s.id}",
            f"start: {s.start_dt.isoformat(timespec='minutes')}",
            f"end: {s.stop_dt.isoformat(timespec='minutes')}",
            f"duration: {json.dumps(fmt_duration(s.duration))}",
            f"levels: {json.dumps(levels)}",
            f"gold_net: {json.dumps(net)}",
            f"model: {json.dumps(model)}",
        ]
        if s.abrupt:
            front.append("ended_abruptly: true")
        front.append("---")
        title = f"# {s.name}, {s.start_dt:%d %B %Y}: Session {s.id}"
        sub = f"*{who} of {s.realm}. {fmt_duration(s.duration)}, level {levels}, gold {net}.*"
        return "\n".join(front) + f"\n\n{title}\n\n{sub}\n\n{body.strip()}\n"

    def record(self, s: Session, folder: str, status: str, **extra) -> None:
        rec = {
            "hash": s.content_hash,
            "status": status,  # "written" | "trivial"
            "char": s.char_key,
            "id": s.id,
            "start": s.start,
            "stop": s.stop,
            "folder": folder,
            "headline": s.headline(),
            "levels": [s.start_level, s.end_level],
            "recorded_at": datetime.now().isoformat(timespec="seconds"),
        }
        rec.update(extra)
        self.state["sessions"][s.key] = rec

    def write_entry(self, s: Session, folder: str, body: str, model: str, words: int) -> Path:
        path = self.entry_path(s, folder)
        _atomic_write(path, self.render_entry(s, body, model))
        self.record(s, folder, "written", file=path.relative_to(self.out).as_posix(),
                    words=words, model=model)
        return path

    # -- index -----------------------------------------------------------

    def write_index(self) -> Path:
        by_char: dict[str, list[dict]] = {}
        for rec in self.state["sessions"].values():
            by_char.setdefault(rec["char"], []).append(rec)
        lines = ["# The Silvercord Chronicle", ""]
        if not by_char:
            lines.append("_No sessions chronicled yet._")
        chars = self.state["chars"]
        for char_key in sorted(by_char, key=lambda k: chars.get(k, {}).get("name", k)):
            info = chars.get(char_key, {})
            who = " ".join(x for x in (title_case(info.get("race")), title_case(info.get("class"))) if x)
            lines.append(f"## {info.get('name', char_key)} of {info.get('realm', '?')}"
                         + (f" ({who})" if who else ""))
            lines.append("")
            for rec in sorted(by_char[char_key], key=lambda r: (r["start"], r["id"]), reverse=True):
                date = datetime.fromtimestamp(rec["start"]).strftime("%Y-%m-%d")
                dur = fmt_duration(rec["stop"] - rec["start"])
                lv = rec.get("levels") or [None, None]
                lvl = f"lvl {lv[0]}->{lv[1]}" if lv[0] and lv[1] and lv[0] != lv[1] else f"lvl {lv[1] or lv[0] or '?'}"
                if rec["status"] == "written" and rec.get("file"):
                    label = f"[Session {rec['id']}]({rec['file']})"
                else:
                    label = f"Session {rec['id']} (no entry)"
                lines.append(f"- {date}: {label}, {dur}, {lvl}. {rec.get('headline', '')}")
            lines.append("")
        path = self.out / "index.md"
        _atomic_write(path, "\n".join(lines).rstrip() + "\n")
        return path

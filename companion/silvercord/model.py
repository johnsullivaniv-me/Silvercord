"""Session model: normalize raw SavedVariables data and build prompt facts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

QUALITY = {2: "uncommon", 3: "rare", 4: "epic", 5: "legendary", 6: "artifact", 7: "heirloom"}

# Event kinds that make a session worth a full entry even if it was short.
NOTABLE_KINDS = {"level", "death", "boss", "kill", "quest", "loot", "note"}


def as_list(v: Any) -> list:
    """SavedVariables lists come back as list, or {} when empty."""
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        return [v[k] for k in sorted(k for k in v if isinstance(k, int))]
    return []


def as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def fmt_money(copper: int | float | None) -> str:
    c = int(abs(copper or 0))
    g, s, cc = c // 10000, (c // 100) % 100, c % 100
    parts = []
    if g:
        parts.append(f"{g}g")
    if s:
        parts.append(f"{s}s")
    if cc or not parts:
        parts.append(f"{cc}c")
    return " ".join(parts)


def fmt_duration(seconds: float) -> str:
    m = int(round(seconds / 60))
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def title_case(token: str | None) -> str | None:
    return token.replace("_", " ").title() if token else None


@dataclass
class Session:
    char_key: str
    name: str
    realm: str
    cls: str | None
    race: str | None
    faction: str | None
    id: int
    start: int
    stop: int
    abrupt: bool
    events: list[dict]
    gained: int = 0
    lost: int = 0
    start_money: int | None = None
    end_money: int | None = None
    start_level: int | None = None
    end_level: int | None = None
    party: dict = field(default_factory=dict)
    caps: dict = field(default_factory=dict)
    truncated: bool = False
    dropped: int = 0
    raw: dict = field(default_factory=dict, repr=False)

    # -- identity --------------------------------------------------------

    @property
    def key(self) -> str:
        return f"{self.char_key}:{self.id}"

    @property
    def content_hash(self) -> str:
        blob = json.dumps(self.raw, sort_keys=True, default=str).encode()
        return hashlib.sha256(blob).hexdigest()[:16]

    @property
    def start_dt(self) -> datetime:
        return datetime.fromtimestamp(self.start)

    @property
    def stop_dt(self) -> datetime:
        return datetime.fromtimestamp(self.stop)

    @property
    def duration(self) -> int:
        return max(0, self.stop - self.start)

    @property
    def net_money(self) -> int:
        return (self.gained or 0) - (self.lost or 0)

    def is_trivial(self, min_minutes: float) -> bool:
        if self.duration >= min_minutes * 60:
            return False
        for e in self.events:
            k = e.get("k")
            if k in NOTABLE_KINDS:
                return False
            if k == "zone" and e.get("first"):
                return False
            if k == "dungeon" and e.get("event") == "enter":
                return False
            if k == "group" and e.get("event") == "join" and not e.get("already"):
                return False
        return True

    def headline(self) -> str:
        """One-line summary for the index, built only from logged facts."""
        bits = []
        lv = [e["level"] for e in self.events if e.get("k") == "level" and "level" in e]
        if lv:
            bits.append(f"reached level {max(lv)}")
        bosses = [e.get("name") for e in self.events if e.get("k") == "boss"]
        if bosses:
            bits.append(f"felled {', '.join(b for b in bosses if b)}")
        deaths = sum(1 for e in self.events if e.get("k") == "death")
        if deaths:
            bits.append(f"died {deaths}x")
        zones = [e["zone"] for e in self.events if e.get("k") == "zone" and e.get("first")]
        if zones:
            bits.append(f"discovered {', '.join(zones)}")
        quests = sum(1 for e in self.events if e.get("k") == "quest")
        if quests:
            bits.append(f"{quests} quest{'s' if quests != 1 else ''}")
        return "; ".join(bits) if bits else "a quiet session"


def load_sessions(db: dict) -> list[Session]:
    """Flatten SilvercordDB into Session objects, oldest first per character."""
    out: list[Session] = []
    for char_key, c in as_dict(db.get("chars")).items():
        c = as_dict(c)
        name = c.get("name") or char_key.split("-", 1)[-1]
        realm = c.get("realm") or char_key.split("-", 1)[0]
        for s in as_list(c.get("sessions")):
            s = as_dict(s)
            if "id" not in s or "start" not in s:
                continue
            events = [as_dict(e) for e in as_list(s.get("events"))]
            stop = s.get("stop")
            abrupt = stop is None
            if abrupt:
                times = [e.get("t") for e in events if isinstance(e.get("t"), (int, float))]
                stop = int(max(times)) if times else int(s["start"])
            out.append(Session(
                char_key=char_key, name=name, realm=realm,
                cls=c.get("class"), race=c.get("race"), faction=c.get("faction"),
                id=int(s["id"]), start=int(s["start"]), stop=int(stop), abrupt=abrupt,
                events=events,
                gained=int(s.get("gained") or 0), lost=int(s.get("lost") or 0),
                start_money=s.get("startMoney"), end_money=s.get("endMoney"),
                start_level=s.get("startLevel"), end_level=s.get("endLevel"),
                party=as_dict(s.get("party")), caps=as_dict(s.get("caps")),
                truncated=bool(s.get("truncated")), dropped=int(s.get("dropped") or 0),
                raw=s,
            ))
    out.sort(key=lambda x: (x.char_key, x.id))
    return out


# ---------------------------------------------------------------------------
# Facts for the prompt
# ---------------------------------------------------------------------------

def _where(e: dict) -> str:
    place = e.get("sub") or e.get("dungeon") or e.get("zone")
    return f" in {place}" if place else ""


def describe_event(e: dict) -> str | None:
    """Render one logged event as a plain factual line, or None to skip it."""
    k = e.get("k")
    if k == "session":
        return "Logged in." if e.get("event") == "start" else "Logged out."
    if k == "zone":
        return f"Entered {e.get('zone')}" + (" (first visit ever)" if e.get("first") else "") + "."
    if k == "subzone":
        return f"Discovered {e.get('sub')} ({e.get('zone')})."
    if k == "dungeon":
        if e.get("event") == "enter":
            return f"Entered the dungeon {e.get('name')}."
        return f"Left the dungeon {e.get('name')}."
    if k == "level":
        return f"Reached level {e.get('level')}" + (f" in {e['zone']}" if e.get("zone") else "") + "."
    if k == "quest":
        title = e.get("title") or f"quest #{e.get('id')}"
        return f"Turned in the quest \"{title}\"."
    if k == "loot":
        q = QUALITY.get(e.get("q"), "uncommon")
        n = e.get("n") or 1
        how = {"created": "Crafted", "received": "Received"}.get(e.get("how"), "Looted")
        count = f"{n}x " if n and n > 1 else ""
        return f"{how} {count}[{e.get('item')}] ({q} quality)."
    if k == "money":
        d = e.get("delta") or 0
        verb = "Gained" if d > 0 else "Spent or lost"
        return f"{verb} {fmt_money(d)} in one go."
    if k == "group":
        cls = title_case(e.get("class"))
        who = e.get("name")
        detail = ", ".join(str(x) for x in (cls, f"level {e['level']}" if e.get("level") else None) if x)
        detail = f" ({detail})" if detail else ""
        if e.get("event") == "join":
            if e.get("already"):
                return f"Already grouped with {who}{detail}."
            return f"{who}{detail} joined the group."
        return f"{who} left the group."
    if k == "boss":
        where = f" in {e['dungeon']}" if e.get("dungeon") else ""
        return f"Defeated the boss {e.get('name')}{where} (confirmed)."
    if k == "kill":
        label = {"rare": "rare", "rareelite": "rare elite", "worldboss": "world boss",
                 "boss": "boss"}.get(e.get("class"), "elite")
        lvl = f", level {e['level']}" if e.get("level") and e["level"] > 0 else ""
        certainty = " (possibly; inferred, not confirmed)" if e.get("inferred") else ""
        return f"Killed {e.get('name')} ({label}{lvl}){_where(e)}{certainty}."
    if k == "death":
        where = _where(e)
        if e.get("killer"):
            how = f" by {e.get('spell')} from {e['killer']}" if e.get("spell") else f" at the hands of {e['killer']}"
            if e.get("env"):
                how = f" from {e['killer'].lower()} damage"
            if e.get("inferred"):
                how += " (possibly; the killer is a guess, not confirmed)"
            return f"Died{how}{where}."
        return f"Died{where} (cause not recorded)."
    if k == "note":
        return None  # notes are listed separately
    if k == "error":
        return None
    return None


def build_facts(s: Session, previous: Session | None = None) -> str:
    """Everything the chronicler is allowed to know about one session."""
    lines: list[str] = []
    race = title_case(s.race)
    cls = title_case(s.cls)
    who = " ".join(x for x in (race, cls) if x) or "adventurer"
    faction = f" of the {s.faction}" if s.faction else ""
    lines.append(f"Character: {s.name}, {who}{faction}, realm {s.realm}.")
    lines.append(
        f"Session #{s.id}: {s.start_dt:%A %d %B %Y, %H:%M} to {s.stop_dt:%H:%M} "
        f"({fmt_duration(s.duration)})."
    )
    if s.start_level and s.end_level and s.end_level != s.start_level:
        lines.append(f"Level: {s.start_level} -> {s.end_level}.")
    elif s.start_level or s.end_level:
        lines.append(f"Level: {s.end_level or s.start_level} (no level gained).")
    if s.gained or s.lost:
        lines.append(
            f"Gold: gained {fmt_money(s.gained)}, spent or lost {fmt_money(s.lost)}, "
            f"net {'+' if s.net_money >= 0 else '-'}{fmt_money(s.net_money)}."
        )
    else:
        lines.append("Gold: no money changed hands.")
    party = []
    for n, p in sorted(s.party.items()):
        p = as_dict(p)
        bits = [title_case(p.get("class"))]
        if p.get("level"):
            bits.append(f"level {p['level']}")
        detail = ", ".join(b for b in bits if b)
        party.append(f"{n} ({detail})" if detail else n)
    lines.append("Grouped with: " + (", ".join(party) if party else "nobody (solo)") + ".")
    if previous:
        lines.append(
            f"Previous recorded session for this character: #{previous.id} on "
            f"{previous.start_dt:%d %B %Y} ({previous.headline()})."
        )
        prev_level = previous.end_level or previous.start_level
        if prev_level and s.start_level and s.start_level > prev_level:
            lines.append(
                f"Note: the hero was level {prev_level} at the end of that session and "
                f"level {s.start_level} at the start of this one; whatever happened in "
                "between went unrecorded. Do not invent it."
            )
    else:
        lines.append("This is the first recorded session for this character.")

    caveats = []
    if s.caps.get("combatlog") is False:
        caveats.append(
            "The combat log was unavailable, so any killer or elite kill marked "
            "'possibly' is a guess and must be presented as uncertain."
        )
    if s.abrupt:
        caveats.append("The session ended abruptly (likely a disconnect or crash); the true end time is unknown.")
    if s.truncated:
        caveats.append(f"The log hit its size cap; {s.dropped or 'some'} minor events were not recorded.")
    if caveats:
        lines.append("Caveats: " + " ".join(caveats))

    lines.append("")
    lines.append("Timeline (local time):")
    dungeons = {e.get("name") for e in s.events if e.get("k") == "dungeon"}
    for e in s.events:
        if e.get("k") == "zone" and e.get("zone") in dungeons:
            continue  # the dungeon line already says it
        text = describe_event(e)
        if text and isinstance(e.get("t"), (int, float)):
            lines.append(f"- {datetime.fromtimestamp(e['t']):%H:%M} {text}")

    notes = [e for e in s.events if e.get("k") == "note" and e.get("text")]
    lines.append("")
    if notes:
        lines.append("The adventurer's own notes (/chron), quoted exactly. Every one must appear in the entry:")
        for e in notes:
            t = f"{datetime.fromtimestamp(e['t']):%H:%M} " if isinstance(e.get("t"), (int, float)) else ""
            place = f" [{e.get('sub') or e.get('zone')}]" if (e.get("sub") or e.get("zone")) else ""
            lines.append(f"- {t}{place.strip()} \"{e['text']}\"".replace("  ", " "))
    else:
        lines.append("The adventurer wrote no notes this session.")
    return "\n".join(lines)

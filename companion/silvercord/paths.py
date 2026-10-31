"""Config loading and SavedVariables path discovery.

Resolution order for every setting: CLI flag > environment variable >
config file > built-in default. The SavedVariables path is auto-detected
on Windows when nothing is configured.
"""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

SV_FILENAME = "Silvercord.lua"
DEFAULT_MODEL = "claude-sonnet-5-5"

# Where Battle.net usually puts WoW. The registry lookup runs first.
COMMON_WOW_ROOTS = [
    r"C:\Program Files (x86)\World of Warcraft",
    r"C:\Program Files\World of Warcraft",
    r"D:\World of Warcraft",
    r"D:\Games\World of Warcraft",
    r"E:\World of Warcraft",
    r"C:\Games\World of Warcraft",
]

ENV = {
    "sv_path": "SILVERCORD_SV_PATH",
    "wow_path": "SILVERCORD_WOW_PATH",
    "account": "SILVERCORD_ACCOUNT",
    "out_dir": "SILVERCORD_OUT",
    "model": "SILVERCORD_MODEL",
    "min_minutes": "SILVERCORD_MIN_MINUTES",
}


class ConfigError(RuntimeError):
    pass


@dataclass
class Config:
    sv_path: Path | None = None
    wow_path: Path | None = None
    account: str | None = None
    out_dir: Path = field(default_factory=lambda: Path("chronicle"))
    model: str = DEFAULT_MODEL
    min_minutes: float = 10.0
    config_file: Path | None = None


def default_config_locations() -> list[Path]:
    locs = [Path.cwd() / "silvercord.toml"]
    appdata = os.environ.get("APPDATA")
    if appdata:
        locs.append(Path(appdata) / "Silvercord" / "config.toml")
    locs.append(Path.home() / ".config" / "silvercord" / "config.toml")
    return locs


def load_config(cli: dict | None = None, config_path: Path | None = None) -> Config:
    """Merge CLI overrides, env vars, and the first config file found."""
    cli = {k: v for k, v in (cli or {}).items() if v is not None}
    file_data: dict = {}
    chosen = None
    candidates = [config_path] if config_path else default_config_locations()
    for p in candidates:
        if p and p.is_file():
            with p.open("rb") as fh:
                file_data = tomllib.load(fh)
            chosen = p
            break
    if config_path and chosen is None:
        raise ConfigError(f"Config file not found: {config_path}")

    def pick(key):
        if key in cli:
            return cli[key]
        env = os.environ.get(ENV[key])
        if env:
            return env
        return file_data.get(key)

    cfg = Config(config_file=chosen)
    if v := pick("sv_path"):
        cfg.sv_path = Path(v).expanduser()
    if v := pick("wow_path"):
        cfg.wow_path = Path(v).expanduser()
    if v := pick("account"):
        cfg.account = str(v)
    if v := pick("out_dir"):
        cfg.out_dir = Path(v).expanduser()
    if v := pick("model"):
        cfg.model = str(v)
    v = pick("min_minutes")
    if v is not None:
        try:
            cfg.min_minutes = float(v)
        except ValueError as exc:
            raise ConfigError(f"min_minutes must be a number, got {v!r}") from exc
    return cfg


# ---------------------------------------------------------------------------
# WoW install discovery
# ---------------------------------------------------------------------------

def _registry_wow_roots() -> list[Path]:
    if sys.platform != "win32":
        return []
    try:
        import winreg
    except ImportError:
        return []
    found = []
    keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Blizzard Entertainment\World of Warcraft"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Blizzard Entertainment\World of Warcraft"),
    ]
    for hive, sub in keys:
        try:
            with winreg.OpenKey(hive, sub) as k:
                val, _ = winreg.QueryValueEx(k, "InstallPath")
        except OSError:
            continue
        p = Path(val)
        # InstallPath often points at a flavor folder like ...\_retail_\
        if p.name.startswith("_") and p.name.endswith("_"):
            p = p.parent
        found.append(p)
    return found


def candidate_wow_roots(cfg: Config) -> list[Path]:
    if cfg.wow_path:
        return [cfg.wow_path]
    roots = _registry_wow_roots() + [Path(r) for r in COMMON_WOW_ROOTS]
    seen, out = set(), []
    for r in roots:
        key = str(r).lower()
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def find_saved_variables(roots: list[Path], account: str | None = None) -> list[Path]:
    """All Silvercord.lua SavedVariables under any flavor folder of any root.

    The live WoW: Forever flavor folder name isn't known yet (the beta used
    _classic_beta_), so every _*_ folder is searched.
    """
    hits: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for flavor in sorted(root.glob("_*_")):
            acct_dir = flavor / "WTF" / "Account"
            if not acct_dir.is_dir():
                continue
            for acct in acct_dir.iterdir():
                if account and acct.name.lower() != account.lower():
                    continue
                sv = acct / "SavedVariables" / SV_FILENAME
                if sv.is_file():
                    hits.append(sv)
    return sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)


def resolve_sv_path(cfg: Config) -> Path:
    if cfg.sv_path:
        if not cfg.sv_path.is_file():
            raise ConfigError(f"SavedVariables file not found: {cfg.sv_path}")
        return cfg.sv_path
    roots = candidate_wow_roots(cfg)
    hits = find_saved_variables(roots, cfg.account)
    if not hits:
        searched = "\n  ".join(str(r) for r in roots) or "(none)"
        raise ConfigError(
            "Couldn't find Silvercord's SavedVariables. Log in and out once with the "
            "addon enabled, or pass --sv-path / set SILVERCORD_SV_PATH.\n"
            f"Searched WoW roots:\n  {searched}"
        )
    accounts = {p.parent.parent.name for p in hits}
    if len(accounts) > 1 and not cfg.account:
        listing = "\n  ".join(f"{p.parent.parent.name}: {p}" for p in hits)
        raise ConfigError(
            "Found SavedVariables for several accounts; choose one with --account "
            f"or SILVERCORD_ACCOUNT:\n  {listing}"
        )
    return hits[0]

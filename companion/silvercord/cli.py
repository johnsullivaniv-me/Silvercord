"""Command line: silvercord [run|dry-run|list|watch|where]."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from . import __version__
from .chronicle import Chronicle
from .model import fmt_duration, load_sessions
from .paths import ConfigError, load_config, resolve_sv_path
from .pipeline import read_db, run, wow_running


def _parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--sv-path", type=Path, help="Path to SavedVariables/Silvercord.lua")
    common.add_argument("--wow-path", type=Path, help="WoW install root (to auto-detect from)")
    common.add_argument("--account", help="WTF/Account folder name, if you have several")
    common.add_argument("--out", type=Path, dest="out_dir", help="Chronicle output dir (default ./chronicle)")
    common.add_argument("--model", help="Claude model (default claude-sonnet-5-5)")
    common.add_argument("--min-minutes", type=float, help="Trivial-session threshold (default 10)")
    common.add_argument("--config", type=Path, help="Path to a silvercord.toml config file")

    p = argparse.ArgumentParser(prog="silvercord", description="Turn Silvercord logs into a chronicle.")
    p.add_argument("--version", action="version", version=f"silvercord {__version__}")
    sub = p.add_subparsers(dest="cmd")

    r = sub.add_parser("run", parents=[common], help="Write entries for new sessions (default)")
    r.add_argument("--force", action="store_true", help="Rewrite sessions already written")
    r.add_argument("--include-latest", action="store_true",
                   help="Process the latest session even if WoW is still running")
    sub.add_parser("dry-run", parents=[common], help="Show the facts that would be sent; no API calls")
    sub.add_parser("list", parents=[common], help="List sessions and their status")
    w = sub.add_parser("watch", parents=[common], help="Write entries automatically after WoW closes")
    w.add_argument("--interval", type=float, default=15.0, help="Poll interval in seconds")
    sub.add_parser("where", parents=[common], help="Show which SavedVariables file would be used")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0].startswith("-") and argv[0] not in ("-h", "--help", "--version"):
        argv.insert(0, "run")
    args = _parser().parse_args(argv)
    cmd = args.cmd or "run"

    try:
        cfg = load_config(
            {k: getattr(args, k, None) for k in
             ("sv_path", "wow_path", "account", "out_dir", "model", "min_minutes")},
            getattr(args, "config", None),
        )
        sv_path = resolve_sv_path(cfg)
    except ConfigError as exc:
        print(f"silvercord: {exc}", file=sys.stderr)
        return 2

    if cmd == "where":
        print(sv_path)
        return 0

    if cmd == "list":
        sessions = load_sessions(read_db(sv_path))
        chron = Chronicle(cfg.out_dir)
        for s in sessions:
            st = chron.status(s)
            if st == "new" and s.is_trivial(cfg.min_minutes):
                st = "new (trivial)"
            print(f"{s.name:<14} #{s.id:<4} {datetime.fromtimestamp(s.start):%Y-%m-%d %H:%M}  "
                  f"{fmt_duration(s.duration):>8}  {st:<14} {s.headline()}")
        return 0

    if cmd == "dry-run":
        run(sv_path, cfg.out_dir, min_minutes=cfg.min_minutes, dry_run=True)
        return 0

    def make_chronicler():
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
            print("silvercord: note: ANTHROPIC_API_KEY is not set; relying on other SDK credentials.",
                  file=sys.stderr)
        from .writer import Chronicler
        return Chronicler(cfg.model)

    def do_run(force=False, include_latest=False):
        game = None if include_latest else wow_running()
        print(f"Reading {sv_path}")
        report = run(sv_path, cfg.out_dir, chronicler=make_chronicler(), min_minutes=cfg.min_minutes,
                     force=force, game_running=game)
        n = len(report.written) + len(report.revised)
        print(f"Done: {n} entr{'y' if n == 1 else 'ies'} written, {len(report.trivial)} trivial, "
              f"{report.unchanged} already done, {len(report.failed)} failed. "
              f"Index: {cfg.out_dir / 'index.md'}")
        return report

    if cmd == "watch":
        from .watch import watch
        try:
            watch(sv_path, do_run, interval=args.interval)
        except KeyboardInterrupt:
            print("\nStopped watching.")
        return 0

    report = do_run(force=args.force, include_latest=args.include_latest)
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

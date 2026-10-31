"""Watch mode: write entries automatically after you log off."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from .pipeline import wow_running


def watch(
    sv_path: Path,
    run_once: Callable[[], object],
    *,
    interval: float = 15.0,
    settle: float = 5.0,
    log: Callable[[str], None] = print,
    max_cycles: int | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """Poll the SavedVariables file and run the pipeline when it settles.

    The client rewrites SavedVariables on logout, on /reload and on exit. We
    wait until the file has stopped changing and, if psutil is available,
    until WoW has closed. Without psutil we run once the file settles; the
    latest session may then be revised later if you were only reloading.
    """
    running = wow_running()
    if running is None:
        log("psutil not installed: can't see whether WoW is open, so each save is processed "
            "once it settles. pip install psutil to wait for WoW to close.")
    log(f"Watching {sv_path} (Ctrl+C to stop).")

    last_done = sv_path.stat().st_mtime if sv_path.exists() else None
    cycles = 0
    pending_announced = False
    while max_cycles is None or cycles < max_cycles:
        cycles += 1
        try:
            mtime = sv_path.stat().st_mtime if sv_path.exists() else None
            if mtime is not None and mtime != last_done:
                settled = (time.time() - mtime) >= settle
                if settled and wow_running() is not True:
                    log(f"[{time.strftime('%H:%M:%S')}] SavedVariables updated, writing the chronicle...")
                    run_once()
                    last_done = sv_path.stat().st_mtime
                    pending_announced = False
                elif settled and not pending_announced:
                    log("SavedVariables updated, but WoW is still open. Waiting for it to close.")
                    pending_announced = True
        except Exception as exc:  # keep watching through transient errors
            log(f"Watch error: {exc}")
        sleep(interval)

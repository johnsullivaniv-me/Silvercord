# Silvercord

A personal adventure chronicle for **World of Warcraft: Forever**.

- **The addon** (`addon/Silvercord`) quietly logs the notable moments of each play session to SavedVariables. It's observe-only: no automation, no protected functions, and it never posts to chat except to confirm your own `/chron` notes.
- **The companion** (`companion/`) reads that file after you log off. It asks Claude to write a 150–250 word journal entry per session in an epic-but-wry chronicler's voice, using only what was actually logged, and saves the entries as Markdown.

```
chronicle/
  index.md
  Grukk/
    2026-11-04-session-1.md
    2026-11-06-session-3.md
    raw/session-1.json ...       # archived raw logs (survive the addon's log cap)
  .silvercord-state.json         # which sessions are done
```

---

## Read this first: what WoW: Forever's API probably is

Forever is a Classic-style game, but community reports say it runs on the **modern (Mainline) client**, not the Classic Era client. They list it as game type `camelot`, beta build 1.60.1.x, TOC interface **16001**. None of this is confirmed by Blizzard. If it's right, Forever likely inherits modern addon restrictions:

- The **combat log may not be available to addons**. That's normally how you learn *what* killed you and *which* elite died.
- Some combat APIs may return **"secret" values** that addons can't read.

So the addon **probes at runtime** and degrades gracefully:

| Moment | How it's detected | Reliability |
|---|---|---|
| Login / logout, level-ups, zones, subzones, dungeons, quests, gold, group | Standard events | Reliable |
| Loot (green+) | Loot chat messages, parsed with the client's own localized strings | Reliable |
| Dungeon bosses | `ENCOUNTER_END` (success) and `BOSS_KILL` | Reliable |
| Your deaths | `PLAYER_DEAD` | Reliable |
| What killed you | Combat log if available. Otherwise your hostile target at the time of death, marked **inferred** | Guess without the combat log |
| Elite / rare kills | Combat log if available. Otherwise "an elite you were fighting as your target died", marked **inferred** | Guess without the combat log |

Inferred facts reach the chronicler labelled "possibly", and the prompt requires hedging ("by most accounts..."). The chronicle never states a guess as fact. Each session also records which events and APIs actually worked (`caps`), so "no deaths logged" can be told apart from "deaths weren't observable".

### Check the interface number on launch day

`addon/Silvercord/Silvercord.toc` says `## Interface: 16001`, the beta value. In-game, run:

```
/dump select(4, GetBuildInfo())
```

If it prints a different number, edit the TOC. Until you do, you can tick **"Load out of date AddOns"** on the character-select AddOns screen.

---

## Install

### Addon (dev install: link the repo into WoW)

In PowerShell, from the repo root:

```powershell
.\scripts\install-dev.ps1                         # auto-detects WoW, asks which game folder
.\scripts\install-dev.ps1 -WowPath "D:\Games\World of Warcraft" -Flavor _forever_
.\scripts\install-dev.ps1 -Uninstall              # removes only the link
```

This creates a **directory junction** from `...\<flavor>\Interface\AddOns\Silvercord` to `addon\Silvercord`, so repo edits go live after a `/reload`. No admin rights needed. The Forever game folder name isn't known yet (the beta used `_classic_beta_`), so the script lists what it finds.

- If PowerShell blocks the script: `powershell -ExecutionPolicy Bypass -File .\scripts\install-dev.ps1`.
- Junctions need a local NTFS path. If your repo lives in WSL or on a network drive, copy `addon\Silvercord` into `AddOns` instead.
- No dev setup? Just copy the `addon\Silvercord` folder into `Interface\AddOns`.

### Companion (Python 3.11+)

```powershell
cd companion
pip install -e ".[watch]"      # [watch] adds psutil so watch mode can tell when WoW closes
setx ANTHROPIC_API_KEY "sk-ant-..."   # then open a new terminal
```

---

## Use

### In game

| Command | What it does |
|---|---|
| `/chron <text>` | Adds your own note to this session ("Named the boar Kevin."). Notes are always included in the entry, quoted. |
| `/chron` | Shows the current session number and how many entries it has. |

That's the only interaction. Everything else is logged silently.

### After you log off

```powershell
silvercord              # same as: silvercord run
silvercord list         # every session and whether it's written
silvercord dry-run      # print exactly what would be sent to Claude; no API calls, no files
silvercord watch        # leave running: writes entries automatically when WoW closes
silvercord where        # which SavedVariables file it's using
silvercord run --force  # rewrite everything (costs API calls)
```

- **Re-runs are safe.** Each session is tracked by a content hash, so unchanged sessions are skipped.
- **Changes get revised.** If the addon later adds events to a session you already chronicled (you `/reload`ed mid-play and ran the script), that entry is rewritten.
- **WoW still open:** each character's latest session is skipped because it may be unfinished. Pass `--include-latest` to override.
- **Short sessions:** under `--min-minutes` (default 10) with nothing notable, a session gets an index line and no API call.

### Try it now, before launch

A realistic sample file lives at `companion/tests/fixtures/Silvercord.lua`. It covers two characters and five sessions: deaths, Ragefire Chasm with a group, a rare kill, notes, a trivial session, an abrupt one, and one that hit the log cap.

```powershell
cd companion
silvercord dry-run --sv-path tests\fixtures\Silvercord.lua
silvercord run     --sv-path tests\fixtures\Silvercord.lua --out .\sample-chronicle
```

The fixture is **generated by running the real addon code** against a stubbed WoW API: `python tests/make_fixture.py`.

---

## Configuration

Precedence: CLI flag > environment variable > config file > default.

| Setting | Flag | Env var | Default |
|---|---|---|---|
| SavedVariables file | `--sv-path` | `SILVERCORD_SV_PATH` | auto-detected |
| WoW root to search | `--wow-path` | `SILVERCORD_WOW_PATH` | registry, then common paths |
| Account folder | `--account` | `SILVERCORD_ACCOUNT` | only needed if you have several |
| Output folder | `--out` | `SILVERCORD_OUT` | `./chronicle` |
| Claude model | `--model` | `SILVERCORD_MODEL` | `claude-sonnet-5-5` |
| Trivial threshold (min) | `--min-minutes` | `SILVERCORD_MIN_MINUTES` | `10` |
| API key | | `ANTHROPIC_API_KEY` | |

The config file is the first one found of `./silvercord.toml`, `%APPDATA%\Silvercord\config.toml`, and `~/.config/silvercord/config.toml`, or pass `--config`. See `silvercord.example.toml`.

**Auto-detection** reads `InstallPath` from `HKLM\SOFTWARE\WOW6432Node\Blizzard Entertainment\World of Warcraft`, then tries common install folders. It searches every `_*_` game folder for `WTF\Account\*\SavedVariables\Silvercord.lua` and picks the newest.

**Model notes:**
- Requests use adaptive thinking at `medium` effort.
- On models that support it, server-side refusal fallbacks are enabled (`fallbacks: "default"`), so a rare false-positive refusal gets rerouted instead of failing. If your account rejects that beta, the script turns it off and carries on.
- A 200-word entry costs a fraction of a cent on Sonnet.

---

## What gets logged (the SavedVariables shape)

`SilvercordDB.chars["Realm-Name"]` stores the character's class, race, faction, and level, plus `seenZones` and up to 60 `sessions`. Each session holds:

- `id`, `start`, `stop`, `startLevel`, `endLevel`, `startMoney`, `endMoney`, `gained`, `lost`
- `party`: everyone you grouped with
- `caps`: which events and APIs worked
- `truncated` / `dropped`
- `events[]`: `{ t = <epoch>, k = <kind>, ... }`

Event kinds: `session`, `zone`, `subzone` (first visit only), `dungeon`, `level`, `quest`, `loot`, `money` (single swings of 1g+), `group`, `boss`, `kill`, `death`, `note`, `error`.

**Caps:**
- 400 events per session. After that only high-value kinds are kept (levels, deaths, bosses, kills, notes, dungeons), up to 500.
- 60 sessions per character, oldest pruned. The companion archives every session it processes to `raw/`, so pruning never loses chronicle history.
- `/reload` or a relog within 2 minutes continues the same session rather than starting a new chapter.

## Privacy

The names of characters you grouped with, and your notes, are sent to the Claude API as part of the prompt. Nothing else leaves your machine, and nothing is uploaded anywhere else.

## Development

```bash
cd companion
pip install -e ".[watch,dev]"   # dev = pytest + lupa (embedded Lua 5.1)
pytest
```

The addon tests (`tests/test_addon.py`) load the real `.lua` files into Lua 5.1 against a stubbed WoW API (`tests/wowstub.lua`) and fire fake events. The stub simulates a Mainline-style client: no combat log, and some unknown events. They catch logic bugs and Lua errors, but they can't prove client compatibility.

### Launch-day checklist

1. `/dump select(4, GetBuildInfo())` → fix `## Interface:` if needed.
2. Log in, `/chron testing`, `/reload`, `/chron after reload`, log out.
3. `silvercord list` should show one session (the reload continued it) with both notes.
4. Open `SavedVariables\Silvercord.lua` and look at `caps`:
   - `combatlog = false` means killers and elite kills will be inferred.
   - Any event `= false` means that event doesn't exist in this client.
5. Kill something, die to something, loot a green, turn in a quest, then check `silvercord dry-run`.
6. Seeing an `error` event in the log? That's a handler that failed safely. Please file it.

## Layout

```
addon/Silvercord/        Silvercord.toc, Compat.lua (API probes), Core.lua (DB/sessions/caps/slash), Events.lua (handlers)
companion/silvercord/    luaparse, paths, model (facts), writer (Claude), chronicle (Markdown/index/state), pipeline, watch, cli
companion/tests/         pytest suite, WoW stub + Lua harness, fixture generator, fixtures/Silvercord.lua
scripts/install-dev.ps1  dev install via directory junction
```

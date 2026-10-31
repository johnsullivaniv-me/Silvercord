import os
import time
from pathlib import Path

import pytest

from silvercord.paths import ConfigError, Config, find_saved_variables, load_config, resolve_sv_path


def make_sv(root: Path, flavor: str, account: str) -> Path:
    p = root / flavor / "WTF" / "Account" / account / "SavedVariables" / "Silvercord.lua"
    p.parent.mkdir(parents=True)
    p.write_text("SilvercordDB = {}\n")
    return p


def test_finds_newest_across_flavors(tmp_path):
    old = make_sv(tmp_path, "_classic_beta_", "ACCT1")
    os.utime(old, (time.time() - 1000, time.time() - 1000))
    new = make_sv(tmp_path, "_forever_", "ACCT1")
    assert find_saved_variables([tmp_path]) == [new, old]


def test_multiple_accounts_requires_choice(tmp_path):
    make_sv(tmp_path, "_forever_", "ALPHA")
    b = make_sv(tmp_path, "_forever_", "BRAVO")
    with pytest.raises(ConfigError, match="several accounts"):
        resolve_sv_path(Config(wow_path=tmp_path))
    assert resolve_sv_path(Config(wow_path=tmp_path, account="bravo")) == b


def test_missing_gives_helpful_error(tmp_path):
    with pytest.raises(ConfigError, match="--sv-path"):
        resolve_sv_path(Config(wow_path=tmp_path))


def test_precedence_cli_env_file(tmp_path, monkeypatch):
    cfg_file = tmp_path / "silvercord.toml"
    cfg_file.write_text('model = "from-file"\nmin_minutes = 3\nout_dir = "x"\n')
    monkeypatch.setenv("SILVERCORD_MODEL", "from-env")
    cfg = load_config({"model": None}, cfg_file)
    assert cfg.model == "from-env" and cfg.min_minutes == 3.0 and cfg.out_dir == Path("x")
    cfg = load_config({"model": "from-cli"}, cfg_file)
    assert cfg.model == "from-cli"
    monkeypatch.delenv("SILVERCORD_MODEL")
    assert load_config({}, cfg_file).model == "from-file"


def test_default_model(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SILVERCORD_MODEL", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("APPDATA", raising=False)
    assert load_config({}).model == "claude-sonnet-5-5"

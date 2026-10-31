from pathlib import Path

import pytest

from silvercord.luaparse import LuaParseError, parse_saved_variables

FIXTURE = Path(__file__).parent / "fixtures" / "Silvercord.lua"


def test_basic_types_and_lists():
    text = '''
Foo = {
	["a"] = 1,
	["b"] = -2.5,
	["c"] = true,
	["d"] = "x\\"y\\\\z\\nnew",
	["e"] = {
		"one", -- [1]
		"two", -- [2]
	},
	["f"] = {
	},
	[3] = false,
	g = nil,
}
Bar = 42
'''
    out = parse_saved_variables(text)
    assert out["Bar"] == 42
    foo = out["Foo"]
    assert foo["a"] == 1 and foo["b"] == -2.5 and foo["c"] is True
    assert foo["d"] == 'x"y\\z\nnew'
    assert foo["e"] == ["one", "two"]
    assert foo["f"] == {}
    assert foo[3] is False
    assert "g" not in foo


def test_backslash_newline_escape_and_decimal_utf8():
    # Lua's %q writes newlines as backslash + newline; bytes may be \ddd.
    out = parse_saved_variables('X = "a\\\nb"\nY = "caf\\195\\169"\n')
    assert out["X"] == "a\nb"
    assert out["Y"] == "café"


def test_raw_utf8_passes_through():
    assert parse_saved_variables('X = "Zen’jah ünïcode"')["X"] == "Zen’jah ünïcode"


def test_sparse_int_keys_stay_dict():
    assert parse_saved_variables("X = { [1] = 'a', [3] = 'c' }")["X"] == {1: "a", 3: "c"}


def test_errors_have_line_numbers():
    with pytest.raises(LuaParseError, match="line 2"):
        parse_saved_variables("X = {\n  [\"a\"] = ,\n}")


def test_fixture_parses():
    db = parse_saved_variables(FIXTURE.read_text(encoding="utf-8"))["SilvercordDB"]
    assert set(db["chars"]) == {"Ashvale-Grukk", "Ashvale-Zen'jah"}
    assert len(db["chars"]["Ashvale-Grukk"]["sessions"]) == 4
    assert db["client"]["interface"] == 16001

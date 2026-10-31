"""Parser for WoW SavedVariables files.

The client writes a restricted Lua subset: top-level assignments of
tables, strings, numbers, booleans, and nil. This recursive-descent parser
handles exactly that (plus comments), without executing anything.

Tables become dicts. A table whose keys are exactly 1..n becomes a list.
"""

from __future__ import annotations

from typing import Any

_ESCAPES = {
    "n": "\n", "t": "\t", "r": "\r", "a": "\a", "b": "\b", "f": "\f",
    "v": "\v", "\\": "\\", '"': '"', "'": "'", "\n": "\n",
}


class LuaParseError(ValueError):
    pass


class _Parser:
    def __init__(self, text: str):
        self.s = text
        self.i = 0
        self.n = len(text)

    # -- low level -----------------------------------------------------------

    def error(self, msg: str) -> LuaParseError:
        line = self.s.count("\n", 0, self.i) + 1
        return LuaParseError(f"{msg} at line {line}")

    def skip(self) -> None:
        s, n = self.s, self.n
        while self.i < n:
            c = s[self.i]
            if c in " \t\r\n;":
                self.i += 1
            elif s.startswith("--", self.i):
                if s.startswith("--[[", self.i):
                    end = s.find("]]", self.i + 4)
                    self.i = n if end < 0 else end + 2
                else:
                    end = s.find("\n", self.i)
                    self.i = n if end < 0 else end + 1
            else:
                break

    def peek(self) -> str:
        self.skip()
        return self.s[self.i] if self.i < self.n else ""

    def expect(self, ch: str) -> None:
        if self.peek() != ch:
            raise self.error(f"expected {ch!r}, got {self.peek()!r}")
        self.i += 1

    def name(self) -> str:
        self.skip()
        start = self.i
        while self.i < self.n and (self.s[self.i].isalnum() or self.s[self.i] == "_"):
            self.i += 1
        if start == self.i:
            raise self.error("expected identifier")
        return self.s[start:self.i]

    # -- values --------------------------------------------------------------

    def value(self) -> Any:
        c = self.peek()
        if c == "{":
            return self.table()
        if c in "\"'":
            return self.string()
        if c == "[" and self.s.startswith("[[", self.i):
            return self.long_string()
        if c == "-" or c == "." or c.isdigit():
            return self.number()
        word = self.name()
        if word == "true":
            return True
        if word == "false":
            return False
        if word == "nil":
            return None
        raise self.error(f"unexpected word {word!r}")

    def number(self) -> int | float:
        start = self.i
        if self.s[self.i] == "-":
            self.i += 1
        if self.s.startswith(("0x", "0X"), self.i):
            self.i += 2
            while self.i < self.n and self.s[self.i] in "0123456789abcdefABCDEF":
                self.i += 1
            txt = self.s[start:self.i]
            return int(txt, 16)
        while self.i < self.n and self.s[self.i] in "0123456789.eE+-":
            # stop a trailing '-' from eating the next token
            if self.s[self.i] in "+-" and self.s[self.i - 1] not in "eE":
                break
            self.i += 1
        txt = self.s[start:self.i]
        try:
            if txt in ("inf", "-inf"):
                return float(txt)
            f = float(txt)
        except ValueError as exc:
            raise self.error(f"bad number {txt!r}") from exc
        if f.is_integer() and not any(ch in txt for ch in ".eE"):
            return int(txt)
        return f

    def string(self) -> str:
        q = self.s[self.i]
        self.i += 1
        out: list[str] = []
        s = self.s
        byte_escapes = False
        while True:
            if self.i >= self.n:
                raise self.error("unterminated string")
            c = s[self.i]
            if c == q:
                self.i += 1
                break
            if c == "\\":
                self.i += 1
                e = s[self.i]
                if e in _ESCAPES:
                    out.append(_ESCAPES[e])
                    self.i += 1
                elif e.isdigit():
                    j = self.i
                    while j < self.n and j - self.i < 3 and s[j].isdigit():
                        j += 1
                    out.append(chr(int(s[self.i:j])))
                    byte_escapes = True
                    self.i = j
                else:
                    raise self.error(f"bad escape \\{e}")
            else:
                out.append(c)
                self.i += 1
        raw = "".join(out)
        if not byte_escapes:
            return raw
        # Decimal escapes (\195\169) are raw bytes of a UTF-8 sequence.
        try:
            return raw.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return raw

    def long_string(self) -> str:
        end = self.s.find("]]", self.i + 2)
        if end < 0:
            raise self.error("unterminated long string")
        txt = self.s[self.i + 2:end]
        self.i = end + 2
        return txt[1:] if txt.startswith("\n") else txt

    def table(self) -> dict | list:
        self.expect("{")
        result: dict[Any, Any] = {}
        auto = 1
        while True:
            c = self.peek()
            if c == "}":
                self.i += 1
                break
            if c == "[" and not self.s.startswith("[[", self.i):
                self.i += 1
                key = self.value()
                self.expect("]")
                self.expect("=")
                result[key] = self.value()
            else:
                save = self.i
                ident = None
                if c.isalpha() or c == "_":
                    ident = self.name()
                    if self.peek() == "=" and not self.s.startswith("==", self.i):
                        self.i += 1
                        result[ident] = self.value()
                    else:
                        ident = None
                        self.i = save
                if ident is None:
                    result[auto] = self.value()
                    auto += 1
            c = self.peek()
            if c in ",;":
                self.i += 1
            elif c != "}":
                raise self.error(f"expected ',' or '}}', got {c!r}")
        # drop nil values the same way Lua would
        result = {k: v for k, v in result.items() if v is not None}
        if result and all(isinstance(k, int) for k in result):
            keys = sorted(result)
            if keys == list(range(1, len(keys) + 1)):
                return [result[k] for k in keys]
        if not result:
            return {}
        return result

    # -- top level -----------------------------------------------------------

    def chunk(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        while self.peek():
            name = self.name()
            self.expect("=")
            out[name] = self.value()
        return out


def parse_saved_variables(text: str) -> dict[str, Any]:
    """Parse a SavedVariables file body into {global_name: value}."""
    if text.startswith("﻿"):
        text = text[1:]
    return _Parser(text).chunk()

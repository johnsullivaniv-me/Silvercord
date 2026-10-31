"""Shared Lua harness: loads the real addon into Lua 5.1 with a WoW stub."""

from pathlib import Path

from lupa import lua51

ROOT = Path(__file__).resolve().parents[2]
ADDON_DIR = ROOT / "addon" / "Silvercord"
STUB = Path(__file__).with_name("wowstub.lua")


class Client:
    def __init__(self, combatlog: bool = False, saved_variables: str | None = None):
        self.lua = lua51.LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(STUB.read_text())
        self.g = self.lua.globals()
        if saved_variables:
            # The client loads SavedVariables by executing the file as Lua.
            self.lua.execute(saved_variables)
        if combatlog:
            self.lua.execute("WOW.cleu = {}; CombatLogGetCurrentEventInfo = CombatLogGetCurrentEventInfo_impl")
        self.S = self.g.LoadAddon(str(ADDON_DIR))

    def run(self, code: str):
        return self.lua.execute(code)

    def fire(self, event, *args):
        self.g.Fire(event, *args)

    def login(self):
        self.fire("PLAYER_LOGIN")

    def tick(self, seconds=1):
        self.g.WOW.now = self.g.WOW.now + seconds

    def events(self):
        s = self.S.session
        return [dict(e.items()) for e in s.events.values()]

    def kinds(self):
        return [e["k"] for e in self.events()]

    def printed(self):
        return list(self.g.WOW.printed.values())

    def slash(self, text):
        self.g.SlashCmdList["SILVERCORD"](text)

    def saved_variables(self):
        return self.g.SerializeSV("SilvercordDB", self.g.SilvercordDB)

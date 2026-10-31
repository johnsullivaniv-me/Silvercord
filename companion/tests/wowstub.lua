-- Minimal WoW client stub for offline addon tests (Lua 5.1, via lupa).
-- Simulates a Mainline-family client by default: no combat log, a few
-- events "unknown". Tests flip WOW.* fields to simulate other clients.

WOW = {
  now = 1730750000,
  money = 0,
  level = 1,
  zone = "Durotar",
  sub = "Valley of Trials",
  instance = { nil, "none" },
  units = {},          -- unit token -> { name, guid, hostile, player, level, class, dead, classification, tapDenied }
  group = {},          -- list of { name, class, level }
  raid = false,
  inCombat = false,
  invalid = { BOSS_KILL = true },  -- events this fake client rejects
  frames = {},
  printed = {},
  cleu = nil,          -- set to a table to enable CombatLogGetCurrentEventInfo
  questTitle = nil,
  player = { name = "Grukk", class = "Warrior", classToken = "WARRIOR",
             race = "Orc", raceToken = "Orc", faction = "Horde", realm = "Silverhand" },
}

function time() return WOW.now end

function CreateFrame()
  local f = { events = {} }
  function f:RegisterEvent(e)
    if WOW.invalid[e] then error("Attempt to register unknown event \"" .. e .. "\"") end
    self.events[e] = true
  end
  function f:RegisterUnitEvent(e) return self:RegisterEvent(e) end
  function f:UnregisterEvent(e) self.events[e] = nil end
  function f:SetScript(_, fn) self.onevent = fn end
  WOW.frames[#WOW.frames + 1] = f
  return f
end

function Fire(ev, ...)
  for _, f in ipairs(WOW.frames) do
    if f.events[ev] and f.onevent then f.onevent(f, ev, ...) end
  end
end

local function U(u) return WOW.units[u] end

function GetRealmName() return WOW.player.realm end
function UnitName(u)
  if u == "player" then return WOW.player.name, nil end
  local t = U(u); return t and t.name, nil
end
function UnitGUID(u)
  if u == "player" then return "Player-1-" .. WOW.player.name end
  local t = U(u); return t and t.guid
end
function UnitExists(u) return u == "player" or U(u) ~= nil end
function UnitClass(u)
  if u == "player" then return WOW.player.class, WOW.player.classToken end
  local t = U(u); if t then return t.class, t.class end
end
function UnitRace() return WOW.player.race, WOW.player.raceToken end
function UnitFactionGroup() return WOW.player.faction, WOW.player.faction end
function UnitLevel(u)
  if u == "player" then return WOW.level end
  local t = U(u); return t and t.level
end
function UnitIsDead(u) local t = U(u); return t and t.dead or false end
function UnitCanAttack(_, u) local t = U(u); return t and t.hostile or false end
function UnitIsPlayer(u) if u == "player" then return true end local t = U(u); return t and t.player or false end
function UnitClassification(u) local t = U(u); return t and t.classification or "normal" end
function UnitAffectingCombat() return WOW.inCombat end
function UnitIsTapDenied(u) local t = U(u); return t and t.tapDenied or false end

function GetMoney() return WOW.money end
function GetRealZoneText() return WOW.zone end
function GetSubZoneText() return WOW.sub or "" end
function GetInstanceInfo() return WOW.instance[1], WOW.instance[2], 1, "Normal", 5 end
function GetNumGroupMembers() if #WOW.group == 0 then return 0 end return #WOW.group + 1 end
function IsInRaid() return WOW.raid end
function GetBuildInfo() return "1.60.1", "70374", "Oct 1 2026", 16001 end
function GetTitleText() return WOW.questTitle end

function CombatLogGetCurrentEventInfo_impl() return unpack(WOW.cleu) end

LOOT_ITEM_SELF = "You receive loot: %s."
LOOT_ITEM_SELF_MULTIPLE = "You receive loot: %sx%d."
LOOT_ITEM_PUSHED_SELF = "You receive item: %s."
LOOT_ITEM_PUSHED_SELF_MULTIPLE = "You receive item: %sx%d."
UNKNOWNOBJECT = "Unknown"

C_Timer = { After = function(_, fn) fn() end }
DEFAULT_CHAT_FRAME = { AddMessage = function(_, msg) WOW.printed[#WOW.printed + 1] = msg end }
SlashCmdList = {}

-- Party units are derived from WOW.group.
setmetatable(WOW.units, { __index = function(_, k)
  local i = type(k) == "string" and tonumber(string.match(k, "^party(%d)$"))
  local g = i and WOW.group[i]
  if g then return { name = g.name, class = g.class, level = g.level, guid = "Player-" .. g.name } end
end })

function Link(name, quality, id)
  local colors = { [0] = "9d9d9d", [1] = "ffffff", [2] = "1eff00", [3] = "0070dd", [4] = "a335ee" }
  return "|cff" .. colors[quality] .. "|Hitem:" .. (id or 1) .. "::::::::1:::::::|h[" .. name .. "]|h|r"
end

function LoadAddon(dir)
  local S = {}
  for _, file in ipairs({ "Compat.lua", "Core.lua", "Events.lua" }) do
    local chunk = assert(loadfile(dir .. "/" .. file))
    chunk("Silvercord", S)
  end
  return S
end

-- Serialize a table the way the WoW client writes SavedVariables.
local function key(k)
  if type(k) == "string" then return string.format("[%q]", k) end
  return "[" .. tostring(k) .. "]"
end
local function val(v, indent)
  local tv = type(v)
  if tv == "string" then return string.format("%q", v) end
  if tv == "number" or tv == "boolean" then return tostring(v) end
  if tv == "table" then
    local out, pad = { "{\n" }, string.rep("\t", indent + 1)
    local n = #v
    for i = 1, n do
      out[#out + 1] = pad .. val(v[i], indent + 1) .. ", -- [" .. i .. "]\n"
    end
    local keys = {}
    for k in pairs(v) do
      if not (type(k) == "number" and k >= 1 and k <= n and math.floor(k) == k) then keys[#keys + 1] = k end
    end
    table.sort(keys, function(a, b) return tostring(a) < tostring(b) end)
    for _, k in ipairs(keys) do
      out[#out + 1] = pad .. key(k) .. " = " .. val(v[k], indent + 1) .. ",\n"
    end
    out[#out + 1] = string.rep("\t", indent) .. "}"
    return table.concat(out)
  end
  return "nil"
end
function SerializeSV(name, v)
  return "\n" .. name .. " = " .. val(v, 0) .. "\n"
end

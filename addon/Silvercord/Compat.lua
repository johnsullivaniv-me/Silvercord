-- Silvercord: Compat.lua
-- Capability probes and safe wrappers. Every version-specific API goes
-- through here so the rest of the addon never touches a global that might
-- not exist in this client (Classic Era vs Mainline-family clients such as
-- WoW: Forever), and never errors on a "secret" value.

local ADDON, S = ...
S = S or {}

S.caps = {}  -- filled at runtime; persisted per session for the companion

-- ---------------------------------------------------------------------------
-- Generic safety helpers
-- ---------------------------------------------------------------------------

-- Midnight-era clients can hand back "secret" values that addon code may not
-- compare, concatenate, or do arithmetic on. issecretvalue() exists only in
-- those clients; elsewhere nothing is secret.
local issecret = _G.issecretvalue
function S.IsSecret(v)
  if issecret then
    local ok, res = pcall(issecret, v)
    return (not ok) or res and true or false
  end
  return false
end

-- Return v only if it is a usable plain value of the expected Lua type.
function S.Plain(v, expectedType)
  if v == nil or S.IsSecret(v) then return nil end
  if expectedType and type(v) ~= expectedType then return nil end
  return v
end

-- pcall wrapper that returns the function's first result or nil.
function S.Try(fn, ...)
  if type(fn) ~= "function" then return nil end
  local ok, a, b, c, d, e = pcall(fn, ...)
  if ok then return a, b, c, d, e end
  return nil
end

-- Resolve a dotted path like "C_Item.GetItemQualityByID" without erroring.
function S.Api(path)
  local node = _G
  for part in string.gmatch(path, "[^%.]+") do
    if type(node) ~= "table" then return nil end
    node = node[part]
  end
  if type(node) == "function" then return node end
  return nil
end

-- ---------------------------------------------------------------------------
-- Event registration that cannot blow up
-- ---------------------------------------------------------------------------

local isEventValid = S.Api("C_EventUtils.IsEventValid")

-- Register an event if this client knows it. Records the outcome in S.caps
-- so the companion can tell "nothing happened" from "couldn't observe".
function S.SafeRegister(frame, event, unit)
  if isEventValid then
    local ok, valid = pcall(isEventValid, event)
    if ok and valid == false then
      S.caps[event] = false
      return false
    end
  end
  local ok
  if unit and frame.RegisterUnitEvent then
    ok = pcall(frame.RegisterUnitEvent, frame, event, unit)
  end
  if not ok then
    ok = pcall(frame.RegisterEvent, frame, event)
  end
  S.caps[event] = ok and true or false
  return ok
end

-- ---------------------------------------------------------------------------
-- Client info
-- ---------------------------------------------------------------------------

function S.ClientInfo()
  local version, build, date, interface = S.Try(GetBuildInfo)
  return {
    version = version,
    build = build,
    interface = interface,
    project = _G.WOW_PROJECT_ID,
  }
end

-- ---------------------------------------------------------------------------
-- Items
-- ---------------------------------------------------------------------------

-- Hex colours used by item links in older link formats.
local QUALITY_BY_COLOR = {
  ["9d9d9d"] = 0, ["ffffff"] = 1, ["1eff00"] = 2, ["0070dd"] = 3,
  ["a335ee"] = 4, ["ff8000"] = 5, ["e6cc80"] = 6, ["00ccff"] = 7,
}

function S.ItemIdFromLink(link)
  if type(link) ~= "string" then return nil end
  return tonumber(string.match(link, "item:(%d+)"))
end

function S.ItemNameFromLink(link)
  if type(link) ~= "string" then return nil end
  return string.match(link, "%[(.-)%]")
end

local getQualityByID = S.Api("C_Item.GetItemQualityByID")
local cGetItemInfo = S.Api("C_Item.GetItemInfo")

-- Best-effort item quality: API first, then the link's own colour code
-- (works even when the item isn't in the client cache yet).
function S.ItemQuality(link)
  if type(link) ~= "string" then return nil end
  local q
  if getQualityByID then q = S.Plain(S.Try(getQualityByID, link), "number") end
  if q then return q end
  local infoFn = cGetItemInfo or _G.GetItemInfo
  if infoFn then
    local _, _, iq = S.Try(infoFn, link)
    q = S.Plain(iq, "number")
    if q then return q end
  end
  -- Newer link format: |cnIQ2:|Hitem:...
  q = tonumber(string.match(link, "|cnIQ(%d+):"))
  if q then return q end
  -- Older link format: |cff1eff00|Hitem:...
  local hex = string.match(link, "|c%x%x(%x%x%x%x%x%x)")
  if hex then return QUALITY_BY_COLOR[string.lower(hex)] end
  return nil
end

-- Build Lua patterns from the client's own localized loot strings, so
-- CHAT_MSG_LOOT parsing works in any locale. Multi-item patterns first.
local function FormatToPattern(fmt)
  if type(fmt) ~= "string" then return nil end
  -- Normalize positional args ("%1$s") to plain ones ("%s").
  local p = string.gsub(fmt, "%%%d%$([sd])", "%%%1")
  -- Escape Lua pattern magic characters (but not '%', handled below).
  p = string.gsub(p, "([%(%)%.%+%-%*%?%[%]%^%$])", "%%%1")
  p = string.gsub(p, "%%s", "(.+)")
  p = string.gsub(p, "%%d", "(%%d+)")
  return "^" .. p .. "$"
end

function S.BuildLootPatterns()
  local list = {}
  local names = {
    "LOOT_ITEM_SELF_MULTIPLE", "LOOT_ITEM_PUSHED_SELF_MULTIPLE",
    "LOOT_ITEM_CREATED_SELF_MULTIPLE",
    "LOOT_ITEM_SELF", "LOOT_ITEM_PUSHED_SELF", "LOOT_ITEM_CREATED_SELF",
  }
  for _, name in ipairs(names) do
    local pat = FormatToPattern(_G[name])
    if pat then
      list[#list + 1] = { pattern = pat, source = name }
    end
  end
  return list
end

-- ---------------------------------------------------------------------------
-- Quests
-- ---------------------------------------------------------------------------

local getTitleForQuestID = S.Api("C_QuestLog.GetTitleForQuestID")
local getQuestInfo = S.Api("C_QuestLog.GetQuestInfo")

function S.QuestTitle(questID)
  if not questID then return nil end
  local t
  if getTitleForQuestID then t = S.Plain(S.Try(getTitleForQuestID, questID), "string") end
  if not t and getQuestInfo then t = S.Plain(S.Try(getQuestInfo, questID), "string") end
  if t == "" then t = nil end
  return t
end

-- ---------------------------------------------------------------------------
-- Units
-- ---------------------------------------------------------------------------

function S.UnitExists(unit)
  return S.Plain(S.Try(UnitExists, unit)) == true
end

function S.UnitName(unit)
  return S.Plain(S.Try(UnitName, unit), "string")
end

function S.UnitGUID(unit)
  return S.Plain(S.Try(UnitGUID, unit), "string")
end

function S.UnitIsDead(unit)
  return S.Plain(S.Try(UnitIsDead, unit)) == true
end

function S.UnitIsHostile(unit)
  if not S.UnitExists(unit) then return false end
  return S.Plain(S.Try(UnitCanAttack, "player", unit)) == true
    and S.Plain(S.Try(UnitIsPlayer, unit)) ~= true
end

function S.UnitIsTapDenied(unit)
  if not _G.UnitIsTapDenied then return false end
  return S.Plain(S.Try(UnitIsTapDenied, unit)) == true
end

-- "elite", "rare", "rareelite", "worldboss", "boss" or nil if not notable.
function S.NotableClass(unit)
  local c = S.Plain(S.Try(UnitClassification, unit), "string")
  local lvl = S.Plain(S.Try(UnitLevel, unit), "number")
  if lvl == -1 then return "boss" end
  if c == "elite" or c == "rare" or c == "rareelite" or c == "worldboss" then
    return c
  end
  return nil
end

-- ---------------------------------------------------------------------------
-- Combat log (may be absent or forbidden in Mainline-family clients)
-- ---------------------------------------------------------------------------

function S.CombatLogAvailable()
  return type(_G.CombatLogGetCurrentEventInfo) == "function"
end

-- Returns the CLEU payload or nil if the call errors / yields secrets.
function S.CombatLogInfo()
  local fn = _G.CombatLogGetCurrentEventInfo
  if not fn then return nil end
  local res = { pcall(fn) }
  if not res[1] then return nil end
  table.remove(res, 1)
  return res
end

-- ---------------------------------------------------------------------------
-- Misc
-- ---------------------------------------------------------------------------

function S.After(seconds, fn)
  local after = S.Api("C_Timer.After")
  if after then
    after(seconds, fn)
  else
    fn()
  end
end

function S.Print(msg)
  local frame = _G.DEFAULT_CHAT_FRAME
  if frame and frame.AddMessage then
    frame:AddMessage("|cffb0c4deSilvercord:|r " .. tostring(msg))
  end
end

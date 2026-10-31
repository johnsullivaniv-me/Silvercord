-- Silvercord: Events.lua
-- Event handlers. Each one observes and calls S.Log(); none of them act.
-- Combat-derived facts that can't be verified are logged with inferred=true.

local ADDON, S = ...

local frame = CreateFrame("Frame")
S.frame = frame
local H = {}  -- handlers by event name

local BIG_MONEY = 10000          -- 1 gold, in copper: log single swings this big
local DEATH_LOOKBACK = 10        -- seconds: a hit this recent counts as the killer
local BOSS_DEDUPE = 15           -- seconds: ENCOUNTER_END + BOSS_KILL for one fight

-- Runtime state (not saved)
S.currentZone, S.currentSub, S.currentInstance = nil, nil, nil
local lastHit            -- { name, spell, t } from the combat log
local lastHostileTarget  -- { name, t } fallback when there's no combat log
local notable = {}       -- guid -> { name, class, level, engaged }
local recentBoss = {}    -- encounter name -> time
local roster = {}        -- name -> { class, level }
local lootPatterns = {}
local pendingQuestTitle

local function Now() return time() end

local function ZoneData()
  return { zone = S.currentZone, sub = S.currentSub }
end

-- ---------------------------------------------------------------------------
-- Lifecycle
-- ---------------------------------------------------------------------------

function H.PLAYER_LOGIN()
  S.InitDB()
  lootPatterns = S.BuildLootPatterns()
  S.caps.combatlog = S.CombatLogAvailable()
  S.caps.lootPatterns = #lootPatterns

  local s, resumed = S.StartSession()
  if not resumed then
    S.Log("session", {
      event = "start", level = S.char.level, class = S.char.class,
      race = S.char.race, money = s.startMoney,
    })
  end
  S.RegisterGameplayEvents()
  -- Snapshot capabilities now too, in case the session never ends cleanly.
  for k, v in pairs(S.caps) do s.caps[k] = v end
  H.ZONE_CHANGED_NEW_AREA()
  H.GROUP_ROSTER_UPDATE(true)
end

function H.PLAYER_LOGOUT()
  S.Log("session", { event = "end", money = S.Plain(S.Try(GetMoney), "number") })
  S.EndSession()
end

-- ---------------------------------------------------------------------------
-- Progress
-- ---------------------------------------------------------------------------

function H.PLAYER_LEVEL_UP(level)
  level = S.Plain(level, "number")
  if not level then return end
  S.char.level = level
  if S.session then S.session.endLevel = level end
  S.Log("level", { level = level, zone = S.currentZone })
end

function H.QUEST_COMPLETE()
  -- The reward frame is open; its title is the most reliable name source.
  pendingQuestTitle = S.Plain(S.Try(GetTitleText), "string")
end

function H.QUEST_TURNED_IN(questID, xp, money)
  questID = S.Plain(questID, "number")
  local title = pendingQuestTitle or S.QuestTitle(questID)
  pendingQuestTitle = nil
  S.Log("quest", {
    id = questID, title = title,
    xp = S.Plain(xp, "number"), money = S.Plain(money, "number"),
    zone = S.currentZone,
  })
end

-- ---------------------------------------------------------------------------
-- Travel
-- ---------------------------------------------------------------------------

local function CheckInstance()
  local name, instanceType, _, difficultyName, maxPlayers = S.Try(GetInstanceInfo)
  name = S.Plain(name, "string")
  instanceType = S.Plain(instanceType, "string")
  local inDungeon = instanceType == "party" or instanceType == "raid"
  if inDungeon and name and name ~= S.currentInstance then
    S.currentInstance = name
    S.Log("dungeon", {
      event = "enter", name = name, type = instanceType,
      difficulty = S.Plain(difficultyName, "string"),
      size = S.Plain(maxPlayers, "number"),
    })
  elseif not inDungeon and S.currentInstance then
    S.Log("dungeon", { event = "leave", name = S.currentInstance })
    S.currentInstance = nil
  end
end

function H.ZONE_CHANGED_NEW_AREA()
  local zone = S.Plain(S.Try(GetRealZoneText), "string")
  if not zone or zone == "" then return end
  local sub = S.Plain(S.Try(GetSubZoneText), "string")
  if sub == "" then sub = nil end

  if zone ~= S.currentZone then
    local seen = S.char.seenZones
    local first = seen[zone] == nil
    if first then seen[zone] = {} end
    S.currentZone = zone
    S.currentSub = nil
    S.Log("zone", { zone = zone, first = first })
  end
  H.ZONE_CHANGED(sub)
  CheckInstance()
end

-- Subzones churn constantly, so only first-ever visits are logged.
function H.ZONE_CHANGED(subOverride)
  local sub = type(subOverride) == "string" and subOverride
    or S.Plain(S.Try(GetSubZoneText), "string")
  if not sub or sub == "" or sub == S.currentSub then return end
  S.currentSub = sub
  local zone = S.currentZone
  if not zone then return end
  local seen = S.char.seenZones
  seen[zone] = seen[zone] or {}
  if not seen[zone][sub] then
    seen[zone][sub] = true
    S.Log("subzone", { zone = zone, sub = sub })
  end
end
H.ZONE_CHANGED_INDOORS = H.ZONE_CHANGED

function H.PLAYER_ENTERING_WORLD()
  H.ZONE_CHANGED_NEW_AREA()
end

-- ---------------------------------------------------------------------------
-- Loot
-- ---------------------------------------------------------------------------

function H.CHAT_MSG_LOOT(text)
  text = S.Plain(text, "string")
  if not text then return end
  for _, lp in ipairs(lootPatterns) do
    local link, count = string.match(text, lp.pattern)
    if link then
      local q = S.ItemQuality(link)
      if q and q >= 2 then
        S.Log("loot", {
          item = S.ItemNameFromLink(link), id = S.ItemIdFromLink(link),
          q = q, n = tonumber(count) or 1,
          how = (string.find(lp.source, "CREATED") and "created")
            or (string.find(lp.source, "PUSHED") and "received") or "looted",
          zone = S.currentZone,
        })
      end
      return
    end
  end
end

-- ---------------------------------------------------------------------------
-- Money
-- ---------------------------------------------------------------------------

function H.PLAYER_MONEY()
  local s = S.session
  local m = S.Plain(S.Try(GetMoney), "number")
  if not s or not m then return end
  local delta = m - (S.lastMoney or m)
  S.lastMoney = m
  if delta > 0 then
    s.gained = (s.gained or 0) + delta
  elseif delta < 0 then
    s.lost = (s.lost or 0) - delta
  end
  if delta >= BIG_MONEY or delta <= -BIG_MONEY then
    S.Log("money", { delta = delta, total = m, zone = S.currentZone })
  end
end

-- ---------------------------------------------------------------------------
-- Group
-- ---------------------------------------------------------------------------

local function ReadRoster()
  local now = {}
  local n = S.Plain(S.Try(GetNumGroupMembers), "number") or 0
  if n <= 0 then return now end
  local raid = S.Plain(S.Try(IsInRaid)) == true
  local prefix, count = "party", n - 1
  if raid then prefix, count = "raid", n end
  local me = S.UnitName("player")
  for i = 1, count do
    local unit = prefix .. i
    local name = S.UnitName(unit)
    if name and name ~= me and name ~= _G.UNKNOWNOBJECT then
      local _, classToken = S.Try(UnitClass, unit)
      now[name] = {
        class = S.Plain(classToken, "string"),
        level = S.Plain(S.Try(UnitLevel, unit), "number"),
      }
    end
  end
  return now
end

local rosterPending = false
local function ProcessRoster(initial)
  rosterPending = false
  local now = ReadRoster()
  local s = S.session
  for name, info in pairs(now) do
    if not roster[name] then
      S.Log("group", {
        event = "join", name = name, class = info.class, level = info.level,
        already = initial and true or nil,
      })
      if s then
        s.party[name] = s.party[name] or { class = info.class, level = info.level }
      end
    end
  end
  for name in pairs(roster) do
    if not now[name] then
      S.Log("group", { event = "leave", name = name })
    end
  end
  roster = now
end

-- Roster updates arrive in bursts; batch them.
function H.GROUP_ROSTER_UPDATE(initial)
  if initial == true then
    ProcessRoster(true)
    return
  end
  if rosterPending then return end
  rosterPending = true
  S.After(2, function() ProcessRoster(false) end)
end

-- ---------------------------------------------------------------------------
-- Bosses (reliable): ENCOUNTER_END / BOSS_KILL
-- ---------------------------------------------------------------------------

local function LogBoss(name, source, encounterID)
  name = S.Plain(name, "string")
  if not name then return end
  local t = Now()
  if recentBoss[name] and t - recentBoss[name] < BOSS_DEDUPE then return end
  recentBoss[name] = t
  S.Log("boss", {
    name = name, id = S.Plain(encounterID, "number"), source = source,
    dungeon = S.currentInstance, zone = S.currentZone,
  })
end

function H.ENCOUNTER_END(encounterID, encounterName, _, _, success)
  if S.Plain(success) == 1 or S.Plain(success) == true then
    LogBoss(encounterName, "encounter", encounterID)
  end
end

function H.BOSS_KILL(encounterID, encounterName)
  LogBoss(encounterName, "bosskill", encounterID)
end

-- ---------------------------------------------------------------------------
-- Notable units: remember elites/rares we see and fight
-- ---------------------------------------------------------------------------

local function Remember(unit)
  if not S.UnitIsHostile(unit) then return end
  local class = S.NotableClass(unit)
  if not class then return end
  local guid = S.UnitGUID(unit)
  if not guid then return end
  local rec = notable[guid]
  if not rec then
    rec = {
      name = S.UnitName(unit), class = class,
      level = S.Plain(S.Try(UnitLevel, unit), "number"),
    }
    notable[guid] = rec
  end
  return rec, guid
end

local function LogKill(rec, guid, inferred)
  if not rec or rec.logged then return end
  rec.logged = true
  -- Dungeon bosses are already covered by ENCOUNTER_END.
  if rec.name and recentBoss[rec.name] and Now() - recentBoss[rec.name] < BOSS_DEDUPE then
    return
  end
  S.Log("kill", {
    name = rec.name, class = rec.class, level = rec.level,
    inferred = inferred and true or nil,
    dungeon = S.currentInstance, zone = S.currentZone, sub = S.currentSub,
  })
  notable[guid] = nil
end

-- Fallback kill detection (no combat log): our engaged notable target dies.
local function CheckTargetDeath()
  if S.caps.combatlog then return end
  local guid = S.UnitGUID("target")
  if not guid then return end
  local rec = notable[guid]
  if rec and rec.engaged and S.UnitIsDead("target") and not S.UnitIsTapDenied("target") then
    LogKill(rec, guid, true)
  end
end

function H.PLAYER_TARGET_CHANGED()
  local rec = Remember("target")
  if S.UnitIsHostile("target") then
    lastHostileTarget = { name = S.UnitName("target"), t = Now() }
  end
  if rec and S.Plain(S.Try(UnitAffectingCombat, "player")) == true then
    rec.engaged = true
  end
  CheckTargetDeath()
end

function H.UPDATE_MOUSEOVER_UNIT() Remember("mouseover") end
function H.NAME_PLATE_UNIT_ADDED(unit) if unit then Remember(unit) end end

function H.UNIT_HEALTH(unit)
  if unit ~= "target" then return end
  CheckTargetDeath()
end

function H.PLAYER_REGEN_DISABLED()
  if S.UnitIsHostile("target") then
    lastHostileTarget = { name = S.UnitName("target"), t = Now() }
  end
  local guid = S.UnitGUID("target")
  if guid and notable[guid] then notable[guid].engaged = true end
end

function H.PLAYER_REGEN_ENABLED()
  CheckTargetDeath()
  -- Forget unengaged notables so the table doesn't grow all session.
  for guid, rec in pairs(notable) do
    if not rec.engaged then notable[guid] = nil end
  end
end

-- ---------------------------------------------------------------------------
-- Combat log path (only if this client still exposes it)
-- ---------------------------------------------------------------------------

local playerGUID
local DAMAGE = {
  SWING_DAMAGE = true, RANGE_DAMAGE = true, SPELL_DAMAGE = true,
  SPELL_PERIODIC_DAMAGE = true, ENVIRONMENTAL_DAMAGE = true,
}

function H.COMBAT_LOG_EVENT_UNFILTERED()
  local info = S.CombatLogInfo()
  if not info then
    -- Forbidden at runtime: stop listening and fall back to heuristics.
    S.caps.combatlog = false
    pcall(frame.UnregisterEvent, frame, "COMBAT_LOG_EVENT_UNFILTERED")
    return
  end
  local _, sub, _, srcGUID, srcName, _, _, dstGUID, dstName = unpack(info, 1, 9)
  if S.IsSecret(sub) or S.IsSecret(srcGUID) or S.IsSecret(dstGUID) then return end
  playerGUID = playerGUID or S.UnitGUID("player")

  if DAMAGE[sub] and dstGUID == playerGUID then
    local spell
    if sub == "ENVIRONMENTAL_DAMAGE" then
      spell = S.Plain(info[12], "string")   -- "Falling", "Drowning", "Lava"...
      srcName = spell
    elseif sub ~= "SWING_DAMAGE" then
      spell = S.Plain(info[13], "string")
    end
    lastHit = { name = S.Plain(srcName, "string"), spell = spell, t = Now(),
                env = sub == "ENVIRONMENTAL_DAMAGE" or nil }
    return
  end

  -- Mark notables we (or our pet) actually hit.
  if dstGUID and notable[dstGUID]
      and (srcGUID == playerGUID or srcGUID == S.UnitGUID("pet")) then
    notable[dstGUID].engaged = true
  end

  if (sub == "UNIT_DIED" or sub == "PARTY_KILL") and dstGUID then
    local rec = notable[dstGUID]
    if rec and rec.engaged then LogKill(rec, dstGUID, false) end
  end
end

-- ---------------------------------------------------------------------------
-- Death
-- ---------------------------------------------------------------------------

function H.PLAYER_DEAD()
  local t = Now()
  local data = ZoneData()
  data.level = S.char and S.char.level
  data.dungeon = S.currentInstance
  if lastHit and t - lastHit.t <= DEATH_LOOKBACK then
    data.killer = lastHit.name
    data.spell = lastHit.spell
    data.env = lastHit.env
    data.source = "combatlog"
  else
    -- No combat log: best guess is whatever hostile thing we were targeting.
    local guess
    if S.UnitIsHostile("target") then
      guess = S.UnitName("target")
    elseif lastHostileTarget and t - lastHostileTarget.t <= 60 then
      guess = lastHostileTarget.name
    end
    if guess then
      data.killer = guess
      data.source = "target"
      data.inferred = true
    end
  end
  S.Log("death", data)
  lastHit = nil
end

-- ---------------------------------------------------------------------------
-- Registration
-- ---------------------------------------------------------------------------

local GAMEPLAY_EVENTS = {
  "PLAYER_LOGOUT", "PLAYER_LEVEL_UP", "QUEST_COMPLETE", "QUEST_TURNED_IN",
  "ZONE_CHANGED_NEW_AREA", "ZONE_CHANGED", "ZONE_CHANGED_INDOORS",
  "PLAYER_ENTERING_WORLD", "CHAT_MSG_LOOT", "PLAYER_MONEY",
  "GROUP_ROSTER_UPDATE", "ENCOUNTER_END", "BOSS_KILL", "PLAYER_DEAD",
  "PLAYER_TARGET_CHANGED", "UPDATE_MOUSEOVER_UNIT", "NAME_PLATE_UNIT_ADDED",
  "PLAYER_REGEN_DISABLED", "PLAYER_REGEN_ENABLED",
}

function S.RegisterGameplayEvents()
  if S.registered then return end
  S.registered = true
  for _, ev in ipairs(GAMEPLAY_EVENTS) do
    S.SafeRegister(frame, ev)
  end
  S.SafeRegister(frame, "UNIT_HEALTH", "target")
  if S.caps.combatlog then
    S.caps.combatlog = S.SafeRegister(frame, "COMBAT_LOG_EVENT_UNFILTERED")
  end
end

frame:SetScript("OnEvent", function(_, event, ...)
  local fn = H[event]
  if not fn then return end
  -- A bug in one handler must never surface as a Lua error popup mid-game.
  local ok, err = pcall(fn, ...)
  if not ok then
    S.errors = (S.errors or 0) + 1
    if S.session and (S.session.errors or 0) < 5 then
      S.session.errors = (S.session.errors or 0) + 1
      S.Log("error", { event = event, msg = tostring(err) })
    end
  end
end)

S.SafeRegister(frame, "PLAYER_LOGIN")
S.H = H  -- exposed for the offline test harness

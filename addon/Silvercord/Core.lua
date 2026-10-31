-- Silvercord: Core.lua
-- SavedVariables layout, session lifecycle, the event log, and /chron.
-- Observe-only: nothing here acts on the game world.

local ADDON, S = ...

S.SCHEMA = 1
S.MAX_EVENTS = 400          -- soft cap per session; after it only priority kinds
S.HARD_MAX_EVENTS = 500     -- absolute cap per session
S.MAX_SESSIONS = 60         -- per character; oldest pruned (companion archives them)
S.RESUME_WINDOW = 120       -- seconds: /reload or quick relog continues the session
S.MAX_NOTE_LEN = 500

-- Kinds still recorded after the soft cap is hit.
S.PRIORITY = {
  level = true, death = true, boss = true, kill = true, note = true,
  dungeon = true, session = true,
}

-- ---------------------------------------------------------------------------
-- Database
-- ---------------------------------------------------------------------------

function S.CharKey()
  local name = S.UnitName("player") or "Unknown"
  local realm = S.Plain(S.Try(GetRealmName), "string") or "UnknownRealm"
  return realm .. "-" .. name, name, realm
end

function S.InitDB()
  if type(SilvercordDB) ~= "table" then SilvercordDB = {} end
  local db = SilvercordDB
  db.schema = db.schema or S.SCHEMA
  db.chars = db.chars or {}

  local key, name, realm = S.CharKey()
  local c = db.chars[key]
  if not c then
    c = { name = name, realm = realm, nextSessionId = 1, seenZones = {}, sessions = {} }
    db.chars[key] = c
  end
  local _, classToken = S.Try(UnitClass, "player")
  local _, raceToken = S.Try(UnitRace, "player")
  c.class = S.Plain(classToken, "string") or c.class
  c.race = S.Plain(raceToken, "string") or c.race
  c.faction = S.Plain(S.Try(UnitFactionGroup, "player"), "string") or c.faction
  c.level = S.Plain(S.Try(UnitLevel, "player"), "number") or c.level
  db.client = S.ClientInfo()
  S.char = c
  return c
end

-- ---------------------------------------------------------------------------
-- Sessions
-- ---------------------------------------------------------------------------

local function Money()
  return S.Plain(S.Try(GetMoney), "number") or 0
end

function S.StartSession()
  local c = S.char
  local now = time()
  local last = c.sessions[#c.sessions]

  -- /reload fires PLAYER_LOGOUT then PLAYER_LOGIN; treat it (and a quick
  -- relog) as the same sitting rather than a new chapter.
  if last and last.stop and (now - last.stop) <= S.RESUME_WINDOW then
    last.stop = nil
    last.resumed = (last.resumed or 0) + 1
    S.session = last
    S.lastMoney = Money()
    return last, true
  end

  local s = {
    id = c.nextSessionId,
    start = now,
    startLevel = c.level,
    startMoney = Money(),
    gained = 0,
    lost = 0,
    caps = {},
    party = {},
    events = {},
  }
  c.nextSessionId = c.nextSessionId + 1
  c.sessions[#c.sessions + 1] = s

  while #c.sessions > S.MAX_SESSIONS do
    table.remove(c.sessions, 1)
  end

  S.session = s
  S.lastMoney = s.startMoney
  return s, false
end

function S.EndSession()
  local s = S.session
  if not s then return end
  s.stop = time()
  -- UnitLevel can lag behind PLAYER_LEVEL_UP, so trust the highest we've seen.
  local lvl = S.Plain(S.Try(UnitLevel, "player"), "number")
  local best = math.max(lvl or 0, S.char.level or 0, s.endLevel or 0)
  if best > 0 then s.endLevel = best end
  s.endMoney = Money()
  -- Snapshot which observation channels worked, so the companion knows
  -- whether "no deaths logged" means none happened or none were visible.
  for k, v in pairs(S.caps) do s.caps[k] = v end
end

-- ---------------------------------------------------------------------------
-- Event log
-- ---------------------------------------------------------------------------

-- Append one entry. data is a flat table of plain values; nils are fine.
function S.Log(kind, data)
  local s = S.session
  if not s then return end
  local n = #s.events
  if n >= S.HARD_MAX_EVENTS then
    s.truncated = true
    return
  end
  if n >= S.MAX_EVENTS and not S.PRIORITY[kind] then
    s.truncated = true
    s.dropped = (s.dropped or 0) + 1
    return
  end
  local e = { t = time(), k = kind }
  if data then
    for k, v in pairs(data) do
      local tv = type(v)
      if (tv == "string" or tv == "number" or tv == "boolean") and not S.IsSecret(v) then
        e[k] = v
      end
    end
  end
  s.events[n + 1] = e
  return e
end

-- ---------------------------------------------------------------------------
-- /chron
-- ---------------------------------------------------------------------------

local function Trim(s)
  return (string.gsub(s or "", "^%s*(.-)%s*$", "%1"))
end

function S.HandleSlash(msg)
  msg = Trim(msg)
  if msg == "" then
    local s = S.session
    local count = s and #s.events or 0
    S.Print(string.format(
      "/chron <text> adds a note to this session's chronicle. (Session #%s, %d entries logged.)",
      s and tostring(s.id) or "?", count))
    return
  end
  if #msg > S.MAX_NOTE_LEN then
    msg = string.sub(msg, 1, S.MAX_NOTE_LEN)
  end
  S.Log("note", { text = msg, zone = S.currentZone, sub = S.currentSub })
  S.Print("noted.")
end

SLASH_SILVERCORD1 = "/chron"
SLASH_SILVERCORD2 = "/chronicle"
SlashCmdList = SlashCmdList or {}
SlashCmdList["SILVERCORD"] = function(msg) S.HandleSlash(msg) end

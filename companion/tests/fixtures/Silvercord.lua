
SilvercordDB = {
	["chars"] = {
		["Ashvale-Grukk"] = {
			["class"] = "WARRIOR",
			["faction"] = "Horde",
			["level"] = 16,
			["name"] = "Grukk",
			["nextSessionId"] = 5,
			["race"] = "Orc",
			["realm"] = "Ashvale",
			["seenZones"] = {
				["Durotar"] = {
					["Burning Blade Coven"] = true,
					["Razor Hill"] = true,
					["Sen'jin Village"] = true,
					["Valley of Trials"] = true,
				},
				["Orgrimmar"] = {
					["Cleft of Shadow"] = true,
					["Valley of Strength"] = true,
				},
				["Ragefire Chasm"] = {
				},
				["The Barrens"] = {
					["Boulder Lode Mine"] = true,
					["Dreadmist Peak"] = true,
					["Far Watch Post"] = true,
					["Forgotten Pools"] = true,
					["Grol'dom Farm"] = true,
					["Lushwater Oasis"] = true,
					["Northwatch Hold"] = true,
					["Ratchet"] = true,
					["Southfury River"] = true,
					["The Crossroads"] = true,
					["The Dry Hills"] = true,
					["The Merchant Coast"] = true,
					["The Mor'shan Rampart"] = true,
					["The Sludge Fen"] = true,
					["The Stagnant Oasis"] = true,
					["Thorn Hill"] = true,
				},
			},
			["sessions"] = {
				{
					["caps"] = {
						["BOSS_KILL"] = false,
						["CHAT_MSG_LOOT"] = true,
						["ENCOUNTER_END"] = true,
						["GROUP_ROSTER_UPDATE"] = true,
						["NAME_PLATE_UNIT_ADDED"] = true,
						["PLAYER_DEAD"] = true,
						["PLAYER_ENTERING_WORLD"] = true,
						["PLAYER_LEVEL_UP"] = true,
						["PLAYER_LOGIN"] = true,
						["PLAYER_LOGOUT"] = true,
						["PLAYER_MONEY"] = true,
						["PLAYER_REGEN_DISABLED"] = true,
						["PLAYER_REGEN_ENABLED"] = true,
						["PLAYER_TARGET_CHANGED"] = true,
						["QUEST_COMPLETE"] = true,
						["QUEST_TURNED_IN"] = true,
						["UNIT_HEALTH"] = true,
						["UPDATE_MOUSEOVER_UNIT"] = true,
						["ZONE_CHANGED"] = true,
						["ZONE_CHANGED_INDOORS"] = true,
						["ZONE_CHANGED_NEW_AREA"] = true,
						["combatlog"] = false,
						["lootPatterns"] = 4,
					},
					["endLevel"] = 6,
					["endMoney"] = 10,
					["events"] = {
						{
							["class"] = "WARRIOR",
							["event"] = "start",
							["k"] = "session",
							["level"] = 1,
							["money"] = 0,
							["race"] = "Orc",
							["t"] = 1793837160,
						}, -- [1]
						{
							["first"] = true,
							["k"] = "zone",
							["t"] = 1793837160,
							["zone"] = "Durotar",
						}, -- [2]
						{
							["k"] = "subzone",
							["sub"] = "Valley of Trials",
							["t"] = 1793837160,
							["zone"] = "Durotar",
						}, -- [3]
						{
							["k"] = "note",
							["sub"] = "Valley of Trials",
							["t"] = 1793837280,
							["text"] = "Launch night. The queue was 3 hours. I have never been more ready to punch a boar.",
							["zone"] = "Durotar",
						}, -- [4]
						{
							["id"] = 4641,
							["k"] = "quest",
							["money"] = 0,
							["t"] = 1793837520,
							["title"] = "Your Place In The World",
							["xp"] = 40,
							["zone"] = "Durotar",
						}, -- [5]
						{
							["id"] = 788,
							["k"] = "quest",
							["money"] = 0,
							["t"] = 1793838060,
							["title"] = "Cutting Teeth",
							["xp"] = 170,
							["zone"] = "Durotar",
						}, -- [6]
						{
							["k"] = "level",
							["level"] = 2,
							["t"] = 1793838060,
							["zone"] = "Durotar",
						}, -- [7]
						{
							["id"] = 790,
							["k"] = "quest",
							["money"] = 0,
							["t"] = 1793838780,
							["title"] = "Sarkoth",
							["xp"] = 225,
							["zone"] = "Durotar",
						}, -- [8]
						{
							["id"] = 804,
							["k"] = "quest",
							["money"] = 35,
							["t"] = 1793838960,
							["title"] = "Sarkoth",
							["xp"] = 250,
							["zone"] = "Durotar",
						}, -- [9]
						{
							["k"] = "level",
							["level"] = 3,
							["t"] = 1793838960,
							["zone"] = "Durotar",
						}, -- [10]
						{
							["id"] = 792,
							["k"] = "quest",
							["money"] = 0,
							["t"] = 1793839800,
							["title"] = "Vile Familiars",
							["xp"] = 340,
							["zone"] = "Durotar",
						}, -- [11]
						{
							["how"] = "received",
							["id"] = 2316,
							["item"] = "Rugged Leather Pants",
							["k"] = "loot",
							["n"] = 1,
							["q"] = 2,
							["t"] = 1793839800,
							["zone"] = "Durotar",
						}, -- [12]
						{
							["k"] = "level",
							["level"] = 4,
							["t"] = 1793840160,
							["zone"] = "Durotar",
						}, -- [13]
						{
							["k"] = "subzone",
							["sub"] = "Burning Blade Coven",
							["t"] = 1793840160,
							["zone"] = "Durotar",
						}, -- [14]
						{
							["inferred"] = true,
							["k"] = "death",
							["killer"] = "Yarrog Baneshadow",
							["level"] = 4,
							["source"] = "target",
							["sub"] = "Burning Blade Coven",
							["t"] = 1793840700,
							["zone"] = "Durotar",
						}, -- [15]
						{
							["k"] = "note",
							["sub"] = "Burning Blade Coven",
							["t"] = 1793840700,
							["text"] = "Yarrog Baneshadow is a coward who hides in a cave full of his friends.",
							["zone"] = "Durotar",
						}, -- [16]
						{
							["id"] = 794,
							["k"] = "quest",
							["money"] = 95,
							["t"] = 1793841480,
							["title"] = "Burning Blade Medallion",
							["xp"] = 450,
							["zone"] = "Durotar",
						}, -- [17]
						{
							["k"] = "level",
							["level"] = 5,
							["t"] = 1793841480,
							["zone"] = "Durotar",
						}, -- [18]
						{
							["how"] = "received",
							["id"] = 2489,
							["item"] = "Tribal Warrior's Shield",
							["k"] = "loot",
							["n"] = 1,
							["q"] = 2,
							["t"] = 1793841480,
							["zone"] = "Durotar",
						}, -- [19]
						{
							["k"] = "subzone",
							["sub"] = "Razor Hill",
							["t"] = 1793842380,
							["zone"] = "Durotar",
						}, -- [20]
						{
							["id"] = 805,
							["k"] = "quest",
							["money"] = 0,
							["t"] = 1793842380,
							["title"] = "Report to Sen'jin Village",
							["xp"] = 50,
							["zone"] = "Durotar",
						}, -- [21]
						{
							["k"] = "subzone",
							["sub"] = "Sen'jin Village",
							["t"] = 1793843700,
							["zone"] = "Durotar",
						}, -- [22]
						{
							["k"] = "level",
							["level"] = 6,
							["t"] = 1793843700,
							["zone"] = "Durotar",
						}, -- [23]
						{
							["k"] = "note",
							["sub"] = "Sen'jin Village",
							["t"] = 1793844180,
							["text"] = "Trained Thunder Clap. The boars of Durotar should be worried.",
							["zone"] = "Durotar",
						}, -- [24]
						{
							["event"] = "end",
							["k"] = "session",
							["money"] = 10,
							["t"] = 1793844420,
						}, -- [25]
					},
					["gained"] = 130,
					["id"] = 1,
					["lost"] = 120,
					["party"] = {
					},
					["start"] = 1793837160,
					["startLevel"] = 1,
					["startMoney"] = 0,
					["stop"] = 1793844420,
				}, -- [1]
				{
					["caps"] = {
						["BOSS_KILL"] = false,
						["CHAT_MSG_LOOT"] = true,
						["ENCOUNTER_END"] = true,
						["GROUP_ROSTER_UPDATE"] = true,
						["NAME_PLATE_UNIT_ADDED"] = true,
						["PLAYER_DEAD"] = true,
						["PLAYER_ENTERING_WORLD"] = true,
						["PLAYER_LEVEL_UP"] = true,
						["PLAYER_LOGIN"] = true,
						["PLAYER_LOGOUT"] = true,
						["PLAYER_MONEY"] = true,
						["PLAYER_REGEN_DISABLED"] = true,
						["PLAYER_REGEN_ENABLED"] = true,
						["PLAYER_TARGET_CHANGED"] = true,
						["QUEST_COMPLETE"] = true,
						["QUEST_TURNED_IN"] = true,
						["UNIT_HEALTH"] = true,
						["UPDATE_MOUSEOVER_UNIT"] = true,
						["ZONE_CHANGED"] = true,
						["ZONE_CHANGED_INDOORS"] = true,
						["ZONE_CHANGED_NEW_AREA"] = true,
						["combatlog"] = false,
						["lootPatterns"] = 4,
					},
					["endLevel"] = 6,
					["endMoney"] = 393,
					["events"] = {
						{
							["class"] = "WARRIOR",
							["event"] = "start",
							["k"] = "session",
							["level"] = 6,
							["money"] = 455,
							["race"] = "Orc",
							["t"] = 1793926860,
						}, -- [1]
						{
							["first"] = false,
							["k"] = "zone",
							["t"] = 1793926860,
							["zone"] = "Durotar",
						}, -- [2]
						{
							["event"] = "end",
							["k"] = "session",
							["money"] = 393,
							["t"] = 1793927100,
						}, -- [3]
					},
					["gained"] = 0,
					["id"] = 2,
					["lost"] = 62,
					["party"] = {
					},
					["start"] = 1793926860,
					["startLevel"] = 6,
					["startMoney"] = 455,
					["stop"] = 1793927100,
				}, -- [2]
				{
					["caps"] = {
						["BOSS_KILL"] = false,
						["CHAT_MSG_LOOT"] = true,
						["ENCOUNTER_END"] = true,
						["GROUP_ROSTER_UPDATE"] = true,
						["NAME_PLATE_UNIT_ADDED"] = true,
						["PLAYER_DEAD"] = true,
						["PLAYER_ENTERING_WORLD"] = true,
						["PLAYER_LEVEL_UP"] = true,
						["PLAYER_LOGIN"] = true,
						["PLAYER_LOGOUT"] = true,
						["PLAYER_MONEY"] = true,
						["PLAYER_REGEN_DISABLED"] = true,
						["PLAYER_REGEN_ENABLED"] = true,
						["PLAYER_TARGET_CHANGED"] = true,
						["QUEST_COMPLETE"] = true,
						["QUEST_TURNED_IN"] = true,
						["UNIT_HEALTH"] = true,
						["UPDATE_MOUSEOVER_UNIT"] = true,
						["ZONE_CHANGED"] = true,
						["ZONE_CHANGED_INDOORS"] = true,
						["ZONE_CHANGED_NEW_AREA"] = true,
						["combatlog"] = false,
						["lootPatterns"] = 4,
					},
					["endLevel"] = 14,
					["endMoney"] = 5470,
					["events"] = {
						{
							["class"] = "WARRIOR",
							["event"] = "start",
							["k"] = "session",
							["level"] = 12,
							["money"] = 8130,
							["race"] = "Orc",
							["t"] = 1794007920,
						}, -- [1]
						{
							["first"] = false,
							["k"] = "zone",
							["t"] = 1794007920,
							["zone"] = "Durotar",
						}, -- [2]
						{
							["first"] = true,
							["k"] = "zone",
							["t"] = 1794008520,
							["zone"] = "Orgrimmar",
						}, -- [3]
						{
							["k"] = "subzone",
							["sub"] = "Valley of Strength",
							["t"] = 1794008520,
							["zone"] = "Orgrimmar",
						}, -- [4]
						{
							["k"] = "subzone",
							["sub"] = "Cleft of Shadow",
							["t"] = 1794008520,
							["zone"] = "Orgrimmar",
						}, -- [5]
						{
							["class"] = "ROGUE",
							["event"] = "join",
							["k"] = "group",
							["level"] = 12,
							["name"] = "Mokvar",
							["t"] = 1794008880,
						}, -- [6]
						{
							["class"] = "SHAMAN",
							["event"] = "join",
							["k"] = "group",
							["level"] = 13,
							["name"] = "Thrallina",
							["t"] = 1794008880,
						}, -- [7]
						{
							["class"] = "MAGE",
							["event"] = "join",
							["k"] = "group",
							["level"] = 14,
							["name"] = "Seylah",
							["t"] = 1794009120,
						}, -- [8]
						{
							["class"] = "WARLOCK",
							["event"] = "join",
							["k"] = "group",
							["level"] = 13,
							["name"] = "Brekk",
							["t"] = 1794009120,
						}, -- [9]
						{
							["first"] = true,
							["k"] = "zone",
							["t"] = 1794009300,
							["zone"] = "Ragefire Chasm",
						}, -- [10]
						{
							["difficulty"] = "Normal",
							["event"] = "enter",
							["k"] = "dungeon",
							["name"] = "Ragefire Chasm",
							["size"] = 5,
							["t"] = 1794009300,
							["type"] = "party",
						}, -- [11]
						{
							["dungeon"] = "Ragefire Chasm",
							["id"] = 1443,
							["k"] = "boss",
							["name"] = "Oggleflint",
							["source"] = "encounter",
							["t"] = 1794010020,
							["zone"] = "Ragefire Chasm",
						}, -- [12]
						{
							["how"] = "looted",
							["id"] = 14149,
							["item"] = "Ragefire Wand",
							["k"] = "loot",
							["n"] = 1,
							["q"] = 2,
							["t"] = 1794010020,
							["zone"] = "Ragefire Chasm",
						}, -- [13]
						{
							["k"] = "note",
							["t"] = 1794010920,
							["text"] = "Brekk pulled the whole room. Brekk is no longer allowed to touch things.",
							["zone"] = "Ragefire Chasm",
						}, -- [14]
						{
							["dungeon"] = "Ragefire Chasm",
							["inferred"] = true,
							["k"] = "death",
							["killer"] = "Ragefire Trogg",
							["level"] = 12,
							["source"] = "target",
							["t"] = 1794010980,
							["zone"] = "Ragefire Chasm",
						}, -- [15]
						{
							["dungeon"] = "Ragefire Chasm",
							["id"] = 1444,
							["k"] = "boss",
							["name"] = "Taragaman the Hungerer",
							["source"] = "encounter",
							["t"] = 1794011340,
							["zone"] = "Ragefire Chasm",
						}, -- [16]
						{
							["how"] = "looted",
							["id"] = 14145,
							["item"] = "Cursed Felblade",
							["k"] = "loot",
							["n"] = 1,
							["q"] = 3,
							["t"] = 1794011340,
							["zone"] = "Ragefire Chasm",
						}, -- [17]
						{
							["k"] = "level",
							["level"] = 13,
							["t"] = 1794011340,
							["zone"] = "Ragefire Chasm",
						}, -- [18]
						{
							["dungeon"] = "Ragefire Chasm",
							["id"] = 1445,
							["k"] = "boss",
							["name"] = "Jergosh the Invoker",
							["source"] = "encounter",
							["t"] = 1794012420,
							["zone"] = "Ragefire Chasm",
						}, -- [19]
						{
							["dungeon"] = "Ragefire Chasm",
							["id"] = 1446,
							["k"] = "boss",
							["name"] = "Bazzalan",
							["source"] = "encounter",
							["t"] = 1794012960,
							["zone"] = "Ragefire Chasm",
						}, -- [20]
						{
							["how"] = "looted",
							["id"] = 14150,
							["item"] = "Bloodpike",
							["k"] = "loot",
							["n"] = 1,
							["q"] = 2,
							["t"] = 1794012960,
							["zone"] = "Ragefire Chasm",
						}, -- [21]
						{
							["first"] = false,
							["k"] = "zone",
							["t"] = 1794013200,
							["zone"] = "Orgrimmar",
						}, -- [22]
						{
							["event"] = "leave",
							["k"] = "dungeon",
							["name"] = "Ragefire Chasm",
							["t"] = 1794013200,
						}, -- [23]
						{
							["event"] = "leave",
							["k"] = "group",
							["name"] = "Seylah",
							["t"] = 1794013200,
						}, -- [24]
						{
							["event"] = "leave",
							["k"] = "group",
							["name"] = "Brekk",
							["t"] = 1794013200,
						}, -- [25]
						{
							["event"] = "leave",
							["k"] = "group",
							["name"] = "Mokvar",
							["t"] = 1794013200,
						}, -- [26]
						{
							["event"] = "leave",
							["k"] = "group",
							["name"] = "Thrallina",
							["t"] = 1794013320,
						}, -- [27]
						{
							["k"] = "note",
							["sub"] = "Valley of Strength",
							["t"] = 1794014520,
							["text"] = "Bought a better axe from the Valley of Honor. Spent most of my gold. Worth it.",
							["zone"] = "Orgrimmar",
						}, -- [28]
						{
							["first"] = false,
							["k"] = "zone",
							["t"] = 1794016080,
							["zone"] = "Durotar",
						}, -- [29]
						{
							["k"] = "level",
							["level"] = 14,
							["t"] = 1794016080,
							["zone"] = "Durotar",
						}, -- [30]
						{
							["event"] = "end",
							["k"] = "session",
							["money"] = 5470,
							["t"] = 1794016980,
						}, -- [31]
					},
					["gained"] = 1840,
					["id"] = 3,
					["lost"] = 4500,
					["party"] = {
						["Brekk"] = {
							["class"] = "WARLOCK",
							["level"] = 13,
						},
						["Mokvar"] = {
							["class"] = "ROGUE",
							["level"] = 12,
						},
						["Seylah"] = {
							["class"] = "MAGE",
							["level"] = 14,
						},
						["Thrallina"] = {
							["class"] = "SHAMAN",
							["level"] = 13,
						},
					},
					["start"] = 1794007920,
					["startLevel"] = 12,
					["startMoney"] = 8130,
					["stop"] = 1794016980,
				}, -- [3]
				{
					["caps"] = {
						["BOSS_KILL"] = false,
						["CHAT_MSG_LOOT"] = true,
						["ENCOUNTER_END"] = true,
						["GROUP_ROSTER_UPDATE"] = true,
						["NAME_PLATE_UNIT_ADDED"] = true,
						["PLAYER_DEAD"] = true,
						["PLAYER_ENTERING_WORLD"] = true,
						["PLAYER_LEVEL_UP"] = true,
						["PLAYER_LOGIN"] = true,
						["PLAYER_LOGOUT"] = true,
						["PLAYER_MONEY"] = true,
						["PLAYER_REGEN_DISABLED"] = true,
						["PLAYER_REGEN_ENABLED"] = true,
						["PLAYER_TARGET_CHANGED"] = true,
						["QUEST_COMPLETE"] = true,
						["QUEST_TURNED_IN"] = true,
						["UNIT_HEALTH"] = true,
						["UPDATE_MOUSEOVER_UNIT"] = true,
						["ZONE_CHANGED"] = true,
						["ZONE_CHANGED_INDOORS"] = true,
						["ZONE_CHANGED_NEW_AREA"] = true,
						["combatlog"] = false,
						["lootPatterns"] = 4,
					},
					["dropped"] = 9,
					["endLevel"] = 16,
					["endMoney"] = 6250,
					["events"] = {
						{
							["class"] = "WARRIOR",
							["event"] = "start",
							["k"] = "session",
							["level"] = 14,
							["money"] = 4890,
							["race"] = "Orc",
							["t"] = 1794096120,
						}, -- [1]
						{
							["first"] = false,
							["k"] = "zone",
							["t"] = 1794096120,
							["zone"] = "Durotar",
						}, -- [2]
						{
							["first"] = true,
							["k"] = "zone",
							["t"] = 1794096600,
							["zone"] = "The Barrens",
						}, -- [3]
						{
							["k"] = "subzone",
							["sub"] = "The Crossroads",
							["t"] = 1794096600,
							["zone"] = "The Barrens",
						}, -- [4]
						{
							["id"] = 842,
							["k"] = "quest",
							["money"] = 175,
							["t"] = 1794096600,
							["title"] = "Crossroads Conscription",
							["xp"] = 420,
							["zone"] = "The Barrens",
						}, -- [5]
						{
							["k"] = "subzone",
							["sub"] = "Far Watch Post",
							["t"] = 1794096960,
							["zone"] = "The Barrens",
						}, -- [6]
						{
							["how"] = "looted",
							["id"] = 4000,
							["item"] = "Barbaric Cloth Robe",
							["k"] = "loot",
							["n"] = 1,
							["q"] = 2,
							["t"] = 1794096960,
							["zone"] = "The Barrens",
						}, -- [7]
						{
							["k"] = "subzone",
							["sub"] = "The Dry Hills",
							["t"] = 1794097320,
							["zone"] = "The Barrens",
						}, -- [8]
						{
							["k"] = "subzone",
							["sub"] = "Lushwater Oasis",
							["t"] = 1794097680,
							["zone"] = "The Barrens",
						}, -- [9]
						{
							["k"] = "subzone",
							["sub"] = "Thorn Hill",
							["t"] = 1794098040,
							["zone"] = "The Barrens",
						}, -- [10]
						{
							["how"] = "looted",
							["id"] = 4003,
							["item"] = "Raptor Hide Belt",
							["k"] = "loot",
							["n"] = 1,
							["q"] = 2,
							["t"] = 1794098040,
							["zone"] = "The Barrens",
						}, -- [11]
						{
							["k"] = "subzone",
							["sub"] = "The Stagnant Oasis",
							["t"] = 1794098400,
							["zone"] = "The Barrens",
						}, -- [12]
						{
							["k"] = "subzone",
							["sub"] = "Forgotten Pools",
							["t"] = 1794098760,
							["zone"] = "The Barrens",
						}, -- [13]
						{
							["k"] = "level",
							["level"] = 15,
							["t"] = 1794098760,
							["zone"] = "The Barrens",
						}, -- [14]
						{
							["k"] = "subzone",
							["sub"] = "The Sludge Fen",
							["t"] = 1794099120,
							["zone"] = "The Barrens",
						}, -- [15]
						{
							["how"] = "looted",
							["id"] = 4006,
							["item"] = "Barbaric Cloth Robe",
							["k"] = "loot",
							["n"] = 1,
							["q"] = 2,
							["t"] = 1794099120,
							["zone"] = "The Barrens",
						}, -- [16]
						{
							["k"] = "subzone",
							["sub"] = "Grol'dom Farm",
							["t"] = 1794099480,
							["zone"] = "The Barrens",
						}, -- [17]
						{
							["k"] = "subzone",
							["sub"] = "Dreadmist Peak",
							["t"] = 1794099840,
							["zone"] = "The Barrens",
						}, -- [18]
						{
							["class"] = "rare",
							["inferred"] = true,
							["k"] = "kill",
							["level"] = 23,
							["name"] = "Humar the Pridelord",
							["sub"] = "Dreadmist Peak",
							["t"] = 1794099960,
							["zone"] = "The Barrens",
						}, -- [19]
						{
							["k"] = "note",
							["sub"] = "Dreadmist Peak",
							["t"] = 1794099960,
							["text"] = "Humar the Pridelord, level 23, fell to a level 15 orc. I will be insufferable about this.",
							["zone"] = "The Barrens",
						}, -- [20]
						{
							["k"] = "level",
							["level"] = 16,
							["t"] = 1794102720,
							["zone"] = "The Barrens",
						}, -- [21]
						{
							["event"] = "end",
							["k"] = "session",
							["money"] = 6250,
							["t"] = 1794103020,
						}, -- [22]
					},
					["gained"] = 1360,
					["id"] = 4,
					["lost"] = 0,
					["party"] = {
					},
					["start"] = 1794096120,
					["startLevel"] = 14,
					["startMoney"] = 4890,
					["stop"] = 1794103020,
					["truncated"] = true,
				}, -- [4]
			},
		},
		["Ashvale-Zen'jah"] = {
			["class"] = "PRIEST",
			["faction"] = "Horde",
			["level"] = 9,
			["name"] = "Zen'jah",
			["nextSessionId"] = 2,
			["race"] = "Troll",
			["realm"] = "Ashvale",
			["seenZones"] = {
				["Durotar"] = {
					["Echo Isles"] = true,
					["Sen'jin Village"] = true,
				},
			},
			["sessions"] = {
				{
					["caps"] = {
						["BOSS_KILL"] = false,
						["CHAT_MSG_LOOT"] = true,
						["COMBAT_LOG_EVENT_UNFILTERED"] = true,
						["ENCOUNTER_END"] = true,
						["GROUP_ROSTER_UPDATE"] = true,
						["NAME_PLATE_UNIT_ADDED"] = true,
						["PLAYER_DEAD"] = true,
						["PLAYER_ENTERING_WORLD"] = true,
						["PLAYER_LEVEL_UP"] = true,
						["PLAYER_LOGIN"] = true,
						["PLAYER_LOGOUT"] = true,
						["PLAYER_MONEY"] = true,
						["PLAYER_REGEN_DISABLED"] = true,
						["PLAYER_REGEN_ENABLED"] = true,
						["PLAYER_TARGET_CHANGED"] = true,
						["QUEST_COMPLETE"] = true,
						["QUEST_TURNED_IN"] = true,
						["UNIT_HEALTH"] = true,
						["UPDATE_MOUSEOVER_UNIT"] = true,
						["ZONE_CHANGED"] = true,
						["ZONE_CHANGED_INDOORS"] = true,
						["ZONE_CHANGED_NEW_AREA"] = true,
						["combatlog"] = true,
						["lootPatterns"] = 4,
					},
					["endLevel"] = 9,
					["events"] = {
						{
							["class"] = "PRIEST",
							["event"] = "start",
							["k"] = "session",
							["level"] = 8,
							["money"] = 1210,
							["race"] = "Troll",
							["t"] = 1794190500,
						}, -- [1]
						{
							["first"] = true,
							["k"] = "zone",
							["t"] = 1794190500,
							["zone"] = "Durotar",
						}, -- [2]
						{
							["k"] = "subzone",
							["sub"] = "Sen'jin Village",
							["t"] = 1794190500,
							["zone"] = "Durotar",
						}, -- [3]
						{
							["k"] = "subzone",
							["sub"] = "Echo Isles",
							["t"] = 1794190800,
							["zone"] = "Durotar",
						}, -- [4]
						{
							["k"] = "note",
							["sub"] = "Echo Isles",
							["t"] = 1794190800,
							["text"] = "Zen’jah’s first rule of the Echo Isles: never trust a naga with a smile.",
							["zone"] = "Durotar",
						}, -- [5]
						{
							["id"] = 808,
							["k"] = "quest",
							["money"] = 0,
							["t"] = 1794191220,
							["title"] = "Minshina's Skull",
							["xp"] = 520,
							["zone"] = "Durotar",
						}, -- [6]
						{
							["how"] = "received",
							["id"] = 4421,
							["item"] = "Voodoo Charm",
							["k"] = "loot",
							["n"] = 1,
							["q"] = 2,
							["t"] = 1794191220,
							["zone"] = "Durotar",
						}, -- [7]
						{
							["k"] = "death",
							["killer"] = "Zalazane",
							["level"] = 8,
							["source"] = "combatlog",
							["spell"] = "Shadow Bolt",
							["sub"] = "Echo Isles",
							["t"] = 1794191760,
							["zone"] = "Durotar",
						}, -- [8]
						{
							["k"] = "level",
							["level"] = 9,
							["t"] = 1794192120,
							["zone"] = "Durotar",
						}, -- [9]
					},
					["gained"] = 0,
					["id"] = 1,
					["lost"] = 0,
					["party"] = {
					},
					["start"] = 1794190500,
					["startLevel"] = 8,
					["startMoney"] = 1210,
				}, -- [1]
			},
		},
	},
	["client"] = {
		["build"] = "70374",
		["interface"] = 16001,
		["version"] = "1.60.1",
	},
	["schema"] = 1,
}

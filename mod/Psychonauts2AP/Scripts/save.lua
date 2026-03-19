--- Psychonauts 2 Archipelago Mod — AP State Persistence
---
--- Persists the mod's runtime state to `ap_save.json` in the game root so
--- that the player can close and re-open the game without losing their AP
--- progress.
---
--- State saved:
---   checked_locations  — set of location IDs already sent to the server
---   received_index     — index of the last item received from the server
---   ability_tiers      — current progressive-ability tier counts
---   received_area_flags — set of area-access item names already received
---                         (re-applied on every connect so unlocks survive
---                          a fresh-game-save with an existing ap_save.json)
---   slot_data          — win-condition and option flags from the server

local Save = {}

local SAVE_FILENAME = "ap_save.json"

-- ---------------------------------------------------------------------------
-- In-memory state
-- ---------------------------------------------------------------------------

Save.checked_locations  = {}   -- { [loc_id] = true }
Save.received_index     = 0    -- last processed ReceivedItems index
Save.ability_tiers      = {}   -- { [prog_name] = tier_count }
Save.received_area_flags = {}  -- { [item_name] = true } area-access items received
Save.slot_data          = {}   -- slot data received on connect

-- ---------------------------------------------------------------------------
-- Minimal JSON helpers (same approach as config.lua)
-- ---------------------------------------------------------------------------

--- Encode a flat mixed table (string keys, number/bool/string values)
--- plus a number-indexed "checked_locations" sub-array.
local function _encode(state)
    local parts = {}

    -- checked_locations as a JSON array of numbers
    local loc_ids = {}
    for id, _ in pairs(state.checked_locations or {}) do
        table.insert(loc_ids, tostring(id))
    end
    table.sort(loc_ids)
    table.insert(parts, '  "checked_locations": [' .. table.concat(loc_ids, ", ") .. "]")

    -- received_index
    table.insert(parts, '  "received_index": ' .. tostring(state.received_index or 0))

    -- ability_tiers as a nested object
    local tier_parts = {}
    for name, tier in pairs(state.ability_tiers or {}) do
        local name_esc = name:gsub('"', '\\"')
        table.insert(tier_parts, '    "' .. name_esc .. '": ' .. tostring(tier))
    end
    table.sort(tier_parts)
    table.insert(parts, '  "ability_tiers": {\n' .. table.concat(tier_parts, ",\n") .. "\n  }")

    -- received_area_flags as a JSON array of strings
    local flag_names = {}
    for name, _ in pairs(state.received_area_flags or {}) do
        table.insert(flag_names, '"' .. name:gsub('"', '\\"') .. '"')
    end
    table.sort(flag_names)
    table.insert(parts, '  "received_area_flags": [' .. table.concat(flag_names, ", ") .. "]")

    return "{\n" .. table.concat(parts, ",\n") .. "\n}\n"
end

--- Parse the save file.  Returns a table with the expected fields.
local function _decode(text)
    local result = {
        checked_locations   = {},
        received_index      = 0,
        ability_tiers       = {},
        received_area_flags = {},
    }

    -- checked_locations array
    local loc_array = text:match('"checked_locations"%s*:%s*%[([^%]]*)%]')
    if loc_array then
        for num_str in loc_array:gmatch("%d+") do
            result.checked_locations[tonumber(num_str)] = true
        end
    end

    -- received_index
    local ri = text:match('"received_index"%s*:%s*(%d+)')
    if ri then
        result.received_index = tonumber(ri)
    end

    -- ability_tiers object
    local tiers_block = text:match('"ability_tiers"%s*:%s*{([^}]*)}')
    if tiers_block then
        for name, tier in tiers_block:gmatch('"([^"]+)"%s*:%s*(%d+)') do
            result.ability_tiers[name] = tonumber(tier)
        end
    end

    -- received_area_flags array of strings
    local flags_array = text:match('"received_area_flags"%s*:%s*%[([^%]]*)%]')
    if flags_array then
        for name in flags_array:gmatch('"([^"]+)"') do
            result.received_area_flags[name] = true
        end
    end

    return result
end

-- ---------------------------------------------------------------------------
-- Public API
-- ---------------------------------------------------------------------------

--- Load state from ap_save.json.  Returns true if loaded successfully.
function Save.load()
    local fh = io.open(SAVE_FILENAME, "r")
    if not fh then
        print("[AP] No ap_save.json found; starting fresh.")
        return false
    end
    local text = fh:read("*a")
    fh:close()

    local ok, data = pcall(_decode, text)
    if not ok or not data then
        print("[AP] ap_save.json is corrupt; starting fresh.")
        return false
    end

    Save.checked_locations   = data.checked_locations   or {}
    Save.received_index      = data.received_index      or 0
    Save.ability_tiers       = data.ability_tiers       or {}
    Save.received_area_flags = data.received_area_flags or {}

    local loc_count = 0
    for _ in pairs(Save.checked_locations) do loc_count = loc_count + 1 end
    local flag_count = 0
    for _ in pairs(Save.received_area_flags) do flag_count = flag_count + 1 end
    print("[AP] Loaded save: " .. loc_count .. " locations checked, "
          .. "item index=" .. Save.received_index .. ", "
          .. flag_count .. " area flags")
    return true
end

--- Persist the current state to ap_save.json.
function Save.write()
    local state = {
        checked_locations   = Save.checked_locations,
        received_index      = Save.received_index,
        ability_tiers       = Save.ability_tiers,
        received_area_flags = Save.received_area_flags,
    }
    local encoded = _encode(state)
    local fh, err = io.open(SAVE_FILENAME, "w")
    if fh then
        fh:write(encoded)
        fh:close()
    else
        print("[AP] Could not write ap_save.json: " .. tostring(err))
    end
end

--- Record that a location has been checked.  Returns true if it was new.
function Save.mark_checked(loc_id)
    if Save.checked_locations[loc_id] then
        return false  -- Already sent
    end
    Save.checked_locations[loc_id] = true
    Save.write()
    return true
end

--- Return true if a location ID has already been checked.
function Save.is_checked(loc_id)
    return Save.checked_locations[loc_id] == true
end

--- Update the received item index and persist.
function Save.set_received_index(idx)
    Save.received_index = idx
    Save.write()
end

--- Update an ability tier and persist.
function Save.set_ability_tier(prog_name, tier)
    Save.ability_tiers[prog_name] = tier
    Save.write()
end

--- Record that an area-access item has been received and persist.
--- These flags are re-applied on every connect so that area unlocks survive
--- a fresh game-save combined with an existing ap_save.json.
function Save.set_area_flag(item_name)
    if not Save.received_area_flags[item_name] then
        Save.received_area_flags[item_name] = true
        Save.write()
    end
end

--- Reset all save state (used when starting a new seed).
function Save.reset()
    Save.checked_locations   = {}
    Save.received_index      = 0
    Save.ability_tiers       = {}
    Save.received_area_flags = {}
    Save.slot_data           = {}
    Save.write()
    print("[AP] Save state reset.")
end

return Save

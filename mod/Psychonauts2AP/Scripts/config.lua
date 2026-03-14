--- Psychonauts 2 Archipelago Mod — Configuration
---
--- Reads and writes `ap_config.json` from the Psychonauts 2 game root
--- directory.  This file is the player-facing configuration that controls
--- which Archipelago server to connect to, which slot name to use, and
--- optionally a password.
---
--- Expected ap_config.json format:
--- {
---   "server":    "archipelago.gg:38281",
---   "slot_name": "YourName",
---   "password":  ""
--- }
---
--- A missing file or missing keys produce safe defaults (empty values that
--- prevent an accidental connection to a server the player has not configured).

local Config = {}

-- ---------------------------------------------------------------------------
-- Defaults
-- ---------------------------------------------------------------------------

Config.server    = ""
Config.slot_name = ""
Config.password  = ""

-- Path relative to the game executable directory.
local CONFIG_FILENAME = "ap_config.json"

-- ---------------------------------------------------------------------------
-- Minimal JSON parser (no external dependency)
-- ---------------------------------------------------------------------------
-- Only handles the flat key/value string format used by ap_config.json.
-- Does not attempt to handle arrays, nested objects, or escaped unicode.

local function _json_parse_flat(text)
    local result = {}
    -- Strip outer braces
    local body = text:match("^%s*{(.+)}%s*$")
    if not body then return result end
    -- Match "key": "value" pairs
    for key, value in body:gmatch('"([^"]+)"%s*:%s*"([^"]*)"') do
        result[key] = value
    end
    -- Also match "key": number (for future extensibility)
    for key, value in body:gmatch('"([^"]+)"%s*:%s*(%d+)') do
        if result[key] == nil then
            result[key] = tonumber(value)
        end
    end
    -- Also match "key": true/false
    for key, value in body:gmatch('"([^"]+)"%s*:%s*(true)') do
        if result[key] == nil then result[key] = true end
    end
    for key, value in body:gmatch('"([^"]+)"%s*:%s*(false)') do
        if result[key] == nil then result[key] = false end
    end
    return result
end

--- Minimal JSON serialiser for flat string/bool/number tables.
local function _json_dump_flat(tbl)
    local parts = {}
    for k, v in pairs(tbl) do
        local val_str
        if type(v) == "string" then
            val_str = '"' .. v:gsub('\\', '\\\\'):gsub('"', '\\"') .. '"'
        elseif type(v) == "boolean" then
            val_str = tostring(v)
        else
            val_str = tostring(v)
        end
        table.insert(parts, '  "' .. k .. '": ' .. val_str)
    end
    return "{\n" .. table.concat(parts, ",\n") .. "\n}\n"
end

-- ---------------------------------------------------------------------------
-- Public API
-- ---------------------------------------------------------------------------

--- Load configuration from ap_config.json.
--- Populates Config.server, Config.slot_name, and Config.password.
--- Returns true on success, false if the file is missing or unreadable.
function Config.load()
    local fh, err = io.open(CONFIG_FILENAME, "r")
    if not fh then
        print("[AP] ap_config.json not found (" .. tostring(err) .. "). "
              .. "Create it in the game folder to connect to a server.")
        return false
    end
    local text = fh:read("*a")
    fh:close()

    local data = _json_parse_flat(text)
    Config.server    = data["server"]    or ""
    Config.slot_name = data["slot_name"] or ""
    Config.password  = data["password"]  or ""

    if Config.server == "" or Config.slot_name == "" then
        print("[AP] ap_config.json is missing 'server' or 'slot_name'. "
              .. "Edit ap_config.json and restart the game.")
        return false
    end

    print("[AP] Config loaded — server=" .. Config.server
          .. " slot=" .. Config.slot_name)
    return true
end

--- Write an example ap_config.json to disk so the player can see the format.
--- Only written if the file does not already exist.
function Config.write_example()
    -- Check for existing file first
    local fh = io.open(CONFIG_FILENAME, "r")
    if fh then
        fh:close()
        return  -- Already exists; do not overwrite
    end

    local example = _json_dump_flat({
        server    = "archipelago.gg:38281",
        slot_name = "YourName",
        password  = "",
    })
    local wh, err = io.open(CONFIG_FILENAME, "w")
    if wh then
        wh:write(example)
        wh:close()
        print("[AP] Created example ap_config.json — edit it and restart the game.")
    else
        print("[AP] Could not write ap_config.json: " .. tostring(err))
    end
end

return Config

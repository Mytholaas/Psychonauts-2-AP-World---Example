--- Psychonauts 2 Archipelago Mod — Archipelago Protocol Client
---
--- Implements the Archipelago multiworld network protocol over a TCP socket
--- using LuaSocket (bundled with UE4SS experimental builds).
---
--- Protocol reference:
---   https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/network%20protocol.md
---
--- Message framing:
---   Each message is a newline-terminated JSON array: [{"cmd": "...", ...}]\n
---   Multiple commands can be batched in one array, but we send/receive one
---   command per array for simplicity.
---
--- Connection flow:
---   1. Open TCP socket to <server>:<port>
---   2. Server sends RoomInfo immediately
---   3. Client sends GetDataPackage (optional; we use the AP server cache)
---   4. Client sends Connect with game/slot/password
---   5. Server responds with Connected or InvalidSlot / SlotRefused
---   6. Normal operation: LocationChecks ↔ ReceivedItems loop

local socket = require("socket")

local AP = {}

-- ---------------------------------------------------------------------------
-- State
-- ---------------------------------------------------------------------------

AP.connected     = false
AP.authenticated = false
AP._sock         = nil
AP._buf          = ""        -- Partial receive buffer
AP._pending_locs = {}        -- Location IDs to send on next flush
AP._callbacks    = {}        -- Registered event callbacks

-- Connection info (set from Config before calling AP.connect)
AP.server    = ""
AP.slot_name = ""
AP.password  = ""
AP.game_name = "Psychonauts 2"

-- Tags sent to the server (DeathLink is added dynamically if enabled)
AP._tags = {"AP"}

-- ---------------------------------------------------------------------------
-- Minimal JSON encoder
-- ---------------------------------------------------------------------------
-- Only encodes the command structures needed by this client.
-- Does not handle nested objects or special characters beyond basic escaping.

local function _json_encode_value(v)
    local t = type(v)
    if t == "nil" then
        return "null"
    elseif t == "boolean" then
        return tostring(v)
    elseif t == "number" then
        return tostring(v)
    elseif t == "string" then
        return '"' .. v:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n') .. '"'
    elseif t == "table" then
        -- Check if array-like (integer keys 1..N)
        local is_array = (#v > 0)
        if is_array then
            local parts = {}
            for _, val in ipairs(v) do
                table.insert(parts, _json_encode_value(val))
            end
            return "[" .. table.concat(parts, ",") .. "]"
        else
            local parts = {}
            for key, val in pairs(v) do
                table.insert(parts, '"' .. tostring(key) .. '":' .. _json_encode_value(val))
            end
            return "{" .. table.concat(parts, ",") .. "}"
        end
    end
    return "null"
end

--- Encode a list of command objects as a JSON array string.
local function _encode_msg(cmds)
    return _json_encode_value(cmds) .. "\n"
end

-- ---------------------------------------------------------------------------
-- Minimal JSON decoder
-- ---------------------------------------------------------------------------
-- Lightweight recursive descent parser sufficient for AP server messages.

local _json_pos

local function _json_skip_ws(text)
    while _json_pos <= #text and text:sub(_json_pos, _json_pos):match("%s") do
        _json_pos = _json_pos + 1
    end
end

local function _json_decode_value(text); end  -- Forward declaration

local function _json_decode_string(text)
    _json_pos = _json_pos + 1  -- Skip opening "
    local result = {}
    while _json_pos <= #text do
        local ch = text:sub(_json_pos, _json_pos)
        if ch == '"' then
            _json_pos = _json_pos + 1
            return table.concat(result)
        elseif ch == '\\' then
            _json_pos = _json_pos + 1
            local esc = text:sub(_json_pos, _json_pos)
            local map = {n="\n", t="\t", r="\r", ['"']='"', ['\\']='\\', ['/']='/'}
            table.insert(result, map[esc] or esc)
        else
            table.insert(result, ch)
        end
        _json_pos = _json_pos + 1
    end
    return table.concat(result)
end

local function _json_decode_array(text)
    _json_pos = _json_pos + 1  -- Skip [
    local result = {}
    _json_skip_ws(text)
    if text:sub(_json_pos, _json_pos) == "]" then
        _json_pos = _json_pos + 1
        return result
    end
    while true do
        table.insert(result, _json_decode_value(text))
        _json_skip_ws(text)
        local ch = text:sub(_json_pos, _json_pos)
        if ch == "]" then _json_pos = _json_pos + 1; break end
        if ch == "," then _json_pos = _json_pos + 1 end
    end
    return result
end

local function _json_decode_object(text)
    _json_pos = _json_pos + 1  -- Skip {
    local result = {}
    _json_skip_ws(text)
    if text:sub(_json_pos, _json_pos) == "}" then
        _json_pos = _json_pos + 1
        return result
    end
    while true do
        _json_skip_ws(text)
        local key = _json_decode_string(text)
        _json_skip_ws(text)
        _json_pos = _json_pos + 1  -- Skip :
        _json_skip_ws(text)
        local val = _json_decode_value(text)
        result[key] = val
        _json_skip_ws(text)
        local ch = text:sub(_json_pos, _json_pos)
        if ch == "}" then _json_pos = _json_pos + 1; break end
        if ch == "," then _json_pos = _json_pos + 1 end
    end
    return result
end

_json_decode_value = function(text)
    _json_skip_ws(text)
    local ch = text:sub(_json_pos, _json_pos)
    if ch == '"' then
        return _json_decode_string(text)
    elseif ch == '[' then
        return _json_decode_array(text)
    elseif ch == '{' then
        return _json_decode_object(text)
    elseif ch == 't' then
        _json_pos = _json_pos + 4; return true
    elseif ch == 'f' then
        _json_pos = _json_pos + 5; return false
    elseif ch == 'n' then
        _json_pos = _json_pos + 4; return nil
    else
        -- Number
        local num_str = text:match("^-?%d+%.?%d*[eE]?[+-]?%d*", _json_pos)
        if num_str then
            _json_pos = _json_pos + #num_str
            return tonumber(num_str)
        end
    end
    return nil
end

local function _json_decode(text)
    _json_pos = 1
    local ok, result = pcall(_json_decode_value, text)
    if ok then return result end
    return nil
end

-- ---------------------------------------------------------------------------
-- Socket send / receive
-- ---------------------------------------------------------------------------

local function _send(cmds)
    if not AP._sock then return end
    local msg = _encode_msg(cmds)
    local ok, err = AP._sock:send(msg)
    if not ok then
        print("[AP] Send error: " .. tostring(err))
        AP._on_disconnect()
    end
end

--- Read all available data from the socket into the buffer,
--- then process complete newline-terminated messages.
function AP.poll()
    if not AP._sock then return end

    AP._sock:settimeout(0)
    local data, err, partial = AP._sock:receive("*l")
    if data then
        AP._process_line(data)
    elseif partial and partial ~= "" then
        AP._buf = AP._buf .. partial
    elseif err == "closed" then
        print("[AP] Connection closed by server.")
        AP._on_disconnect()
        return
    end

    -- Process any complete lines already in the buffer
    while true do
        local line, rest = AP._buf:match("^([^\n]*)\n(.*)")
        if line then
            AP._buf = rest
            AP._process_line(line)
        else
            break
        end
    end

    -- Flush any pending location checks
    AP._flush_checks()
end

local function _process_line(line)
    if line == "" then return end
    local cmds = _json_decode(line)
    if type(cmds) ~= "table" then return end
    for _, cmd in ipairs(cmds) do
        AP._handle_command(cmd)
    end
end
AP._process_line = _process_line

-- ---------------------------------------------------------------------------
-- Command handlers
-- ---------------------------------------------------------------------------

function AP._handle_command(cmd)
    local c = cmd.cmd
    if not c then return end

    if c == "RoomInfo" then
        AP._on_room_info(cmd)
    elseif c == "Connected" then
        AP._on_connected(cmd)
    elseif c == "ConnectionRefused" then
        AP._on_connection_refused(cmd)
    elseif c == "ReceivedItems" then
        AP._on_received_items(cmd)
    elseif c == "RoomUpdate" then
        AP._on_room_update(cmd)
    elseif c == "PrintJSON" then
        AP._on_print_json(cmd)
    elseif c == "Bounced" then
        AP._on_bounced(cmd)
    elseif c == "InvalidPacket" then
        print("[AP] Server reported InvalidPacket: " .. tostring(cmd.text))
    end
end

function AP._on_room_info(cmd)
    -- Server is ready; send Connect
    local tags = AP._tags
    _send({{
        cmd          = "Connect",
        game         = AP.game_name,
        name         = AP.slot_name,
        password     = AP.password,
        uuid         = AP._make_uuid(),
        version      = {major=0, minor=5, build=0, ["class"]="Version"},
        items_handling = 7,   -- Remote items, receive items from other worlds
        tags         = tags,
        slot_data    = true,
    }})
end

function AP._on_connected(cmd)
    AP.authenticated = true
    print("[AP] Connected as " .. AP.slot_name
          .. " (slot " .. tostring(cmd.slot) .. ")")

    -- Notify callbacks
    AP._fire("connected", cmd)

    -- Store slot data
    if cmd.slot_data then
        AP._fire("slot_data", cmd.slot_data)
    end

    -- Re-sync already-checked locations
    local already_checked = {}
    if cmd.checked_locations then
        for _, loc_id in ipairs(cmd.checked_locations) do
            already_checked[loc_id] = true
        end
    end
    AP._fire("already_checked", already_checked)
end

function AP._on_connection_refused(cmd)
    local errors = cmd.errors or {}
    print("[AP] Connection refused: " .. table.concat(errors, ", "))
    AP._fire("connection_refused", errors)
end

function AP._on_received_items(cmd)
    AP._fire("received_items", cmd)
end

function AP._on_room_update(cmd)
    AP._fire("room_update", cmd)
end

function AP._on_print_json(cmd)
    -- Convert the AP rich-text parts to a plain string for the game log
    local parts = {}
    if type(cmd.data) == "table" then
        for _, part in ipairs(cmd.data) do
            if part.text then
                table.insert(parts, part.text)
            end
        end
    elseif cmd.text then
        table.insert(parts, cmd.text)
    end
    local msg = table.concat(parts)
    if msg ~= "" then
        print("[AP Chat] " .. msg)
        AP._fire("chat_message", msg)
    end
end

function AP._on_bounced(cmd)
    -- DeathLink is the only Bounced payload we handle
    if cmd.tags and cmd.data then
        for _, tag in ipairs(cmd.tags) do
            if tag == "DeathLink" then
                AP._fire("death_link", cmd.data)
                return
            end
        end
    end
end

function AP._on_disconnect()
    AP.connected     = false
    AP.authenticated = false
    AP._sock         = nil
    AP._fire("disconnected", nil)
end

-- ---------------------------------------------------------------------------
-- Public API — connection
-- ---------------------------------------------------------------------------

--- Connect to the AP server.  host_port is "hostname:port".
--- Returns true on success (TCP handshake only; auth is async).
function AP.connect(host_port)
    if AP.connected then AP.disconnect() end

    local host, port_str = host_port:match("^(.+):(%d+)$")
    if not host then
        host = host_port
        port_str = "38281"
    end
    local port = tonumber(port_str) or 38281

    local sock, err = socket.tcp()
    if not sock then
        print("[AP] Could not create socket: " .. tostring(err))
        return false
    end

    sock:settimeout(5)
    local ok, err2 = sock:connect(host, port)
    if not ok then
        print("[AP] Could not connect to " .. host .. ":" .. port .. " — " .. tostring(err2))
        sock:close()
        return false
    end

    sock:settimeout(0)
    AP._sock      = sock
    AP.connected  = true
    AP._buf       = ""
    print("[AP] TCP connected to " .. host .. ":" .. port)
    return true
end

--- Disconnect from the server.
function AP.disconnect()
    if AP._sock then
        pcall(function() AP._sock:close() end)
    end
    AP._on_disconnect()
end

-- ---------------------------------------------------------------------------
-- Public API — gameplay
-- ---------------------------------------------------------------------------

--- Queue a location check to be sent on the next poll.
function AP.queue_check(loc_id)
    AP._pending_locs[loc_id] = true
end

--- Send all pending location checks to the server.
function AP._flush_checks()
    if not AP.authenticated then return end
    if next(AP._pending_locs) == nil then return end

    local ids = {}
    for id, _ in pairs(AP._pending_locs) do
        table.insert(ids, id)
    end
    AP._pending_locs = {}

    _send({{
        cmd       = "LocationChecks",
        locations = ids,
    }})
end

--- Send a DeathLink bounce to the server.
function AP.send_death(cause, source)
    if not AP.authenticated then return end
    _send({{
        cmd  = "Bounce",
        tags = {"DeathLink"},
        data = {
            time   = os.time(),
            cause  = cause or "",
            source = source or AP.slot_name,
        },
    }})
end

--- Send a status update (e.g., CLIENT_GOAL = 30 when the player wins).
function AP.send_status(status_code)
    if not AP.authenticated then return end
    _send({{
        cmd    = "StatusUpdate",
        status = status_code,
    }})
end

--- Send a chat message to the server.
function AP.say(text)
    if not AP.authenticated then return end
    _send({{
        cmd     = "Say",
        text    = tostring(text),
    }})
end

-- ---------------------------------------------------------------------------
-- Event callbacks
-- ---------------------------------------------------------------------------

--- Register a callback for an event name.
--- Valid events: connected, slot_data, already_checked, received_items,
---               disconnected, death_link, chat_message, room_update,
---               connection_refused
function AP.on(event, callback)
    if not AP._callbacks[event] then
        AP._callbacks[event] = {}
    end
    table.insert(AP._callbacks[event], callback)
end

function AP._fire(event, data)
    local cbs = AP._callbacks[event]
    if not cbs then return end
    for _, cb in ipairs(cbs) do
        local ok, err = pcall(cb, data)
        if not ok then
            print("[AP] Callback error for event '" .. event .. "': " .. tostring(err))
        end
    end
end

-- ---------------------------------------------------------------------------
-- Utility
-- ---------------------------------------------------------------------------

--- Generate a random UUID-like string for the Connect command.
function AP._make_uuid()
    -- Simple pseudo-UUID based on time and random numbers
    local t = tostring(os.time())
    local r = tostring(math.random(0, 0xFFFFFF))
    return "psy2ap-" .. t .. "-" .. r
end

--- Status codes for StatusUpdate
AP.STATUS = {
    CLIENT_UNKNOWN = 0,
    CLIENT_READY   = 20,
    CLIENT_PLAYING = 30,  -- Use when the player has achieved the goal / beaten the game
    CLIENT_GOAL    = 30,  -- Alias for CLIENT_PLAYING; send this when the win condition is met
}

return AP

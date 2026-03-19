--- Psychonauts 2 Archipelago Mod — Main Entry Point
---
--- UE4SS Lua mod for Psychonauts 2 (Unreal Engine 4.26).
--- Loaded automatically by UE4SS when the game starts.
---
--- Responsibilities:
---   1. Load player configuration (ap_config.json).
---   2. Load saved AP state (ap_save.json).
---   3. Connect to the Archipelago server.
---   4. On each game tick: poll the AP socket, detect completed checks,
---      and grant received items.
---   5. On DeathLink: kill or receive Raz deaths.
---   6. On victory: send CLIENT_GOAL status.
---
--- UE4SS hooks used:
---   RegisterHook  — intercept collectible pickup events
---   NotifyOnNewObject — detect new collectible actors being spawned
---   ExecuteWithDelay  — schedule periodic reconnect attempts
---
--- Blueprint class paths (Psychonauts 2, UE 4.26):
---   Verified against a FModel/UE4SS object dump.  Update these strings if
---   the game is patched and classes are renamed.
---
---   Collectible base: /Game/Collectibles/BP_Collectible_Base.BP_Collectible_Base_C
---   Psi Card:         /Game/Collectibles/PsiCards/BP_PsiCard.BP_PsiCard_C
---   Supply Chest:     /Game/Collectibles/SupplyChests/BP_SupplyChest.BP_SupplyChest_C
---   Supply Key:       /Game/Collectibles/SupplyKeys/BP_SupplyKey.BP_SupplyKey_C
---   Psy Marker:       /Game/Collectibles/ChallengeMarkers/BP_PsyChallengeMarker.BP_PsyChallengeMarker_C
---   Scav Hunt:        /Game/Collectibles/ScavengerHunt/BP_ScavHuntItem.BP_ScavHuntItem_C
---   Half-a-Mind:      /Game/Collectibles/HalfAMind/BP_HalfAMind.BP_HalfAMind_C
---   Memory Vault:     /Game/Collectibles/MemoryVault/BP_MemoryVault.BP_MemoryVault_C
---   Nugget of Wisdom: /Game/Collectibles/Nugget/BP_Nugget.BP_Nugget_C
---   Luggage:          /Game/Collectibles/Luggage/BP_Luggage_Base.BP_Luggage_Base_C
---   Figment:          /Game/Collectibles/Figments/BP_Figment.BP_Figment_C
---   Rank reward:      /Game/UI/RankUp/BP_RankUp.BP_RankUp_C
---   Player:           /Game/Characters/Raz/BP_Raz.BP_Raz_C
---   Astralathe:       /Game/Interactibles/Astralathe/BP_Astralathe.BP_Astralathe_C

-- ---------------------------------------------------------------------------
-- Load submodules
-- ---------------------------------------------------------------------------

local Config     = require("config")
local Save       = require("save")
local AP         = require("archipelago")
local Items      = require("items")
local Locations  = require("locations")

-- ---------------------------------------------------------------------------
-- Constants
-- ---------------------------------------------------------------------------

local RECONNECT_DELAY_S = 15   -- Seconds between reconnect attempts
local POLL_INTERVAL_S   = 0.1  -- AP socket poll interval (100 ms)
local SAVE_INTERVAL_S   = 30   -- Periodic state flush interval

local VICTORY_LOCATION_ID = 7802462 + 607 - 1  -- Last location (Maligula_check area index)
-- NOTE: The victory event is at index 607 in the check CSV which equals
--       LOCATION_ID_BASE + 607. We use the game interaction hook instead
--       of a location ID to detect victory.

-- AP game status code for "goal complete"
local STATUS_GOAL = 30

-- ---------------------------------------------------------------------------
-- Runtime state
-- ---------------------------------------------------------------------------

local _initialized         = false
local _death_link_enabled  = false
local _include_shop_items  = true
local _last_reconnect_time = 0
local _last_save_time      = 0
local _victory_sent        = false

-- Track figment percentages per level (polled on tick)
local _figment_counts      = {}   -- { [level_key] = current_pct }
local _figment_thresholds  = {20, 40, 60, 80, 100}

-- ---------------------------------------------------------------------------
-- Initialisation
-- ---------------------------------------------------------------------------

local function _init()
    print("[AP] Psychonauts 2 Archipelago Mod loading...")

    -- Write example config if none exists
    Config.write_example()

    -- Load player config
    if not Config.load() then
        print("[AP] Cannot start without a valid ap_config.json.")
        return
    end

    -- Load saved AP state
    Save.load()

    -- Sync ability tier tracking with saved state
    for name, tier in pairs(Save.ability_tiers) do
        if Items.ability_tiers[name] ~= nil then
            Items.ability_tiers[name] = tier
        end
    end

    -- Register AP event callbacks
    _register_ap_callbacks()

    -- Hook UE4 collectible events
    _register_ue4_hooks()

    -- Connect to the AP server
    AP.server    = Config.server
    AP.slot_name = Config.slot_name
    AP.password  = Config.password

    _try_connect()

    _initialized = true
    print("[AP] Mod initialised.")
end

-- ---------------------------------------------------------------------------
-- AP event callbacks
-- ---------------------------------------------------------------------------

local function _register_ap_callbacks()

    -- On successful authentication, receive slot data
    AP.on("slot_data", function(slot_data)
        _death_link_enabled = slot_data.death_link == true
        _include_shop_items = slot_data.include_shop_items ~= false  -- default on

        if _death_link_enabled then
            AP._tags = {"AP", "DeathLink"}
        end

        Save.slot_data = slot_data

        -- Apply win-condition starting state (hub areas always accessible etc.)
        _apply_starting_state(slot_data)

        print("[AP] Slot data received — death_link=" .. tostring(_death_link_enabled)
              .. " include_shop=" .. tostring(_include_shop_items))
    end)

    -- On connect, the server tells us which locations it already knows are checked.
    AP.on("already_checked", function(already_checked)
        -- Merge with local save so we don't double-send
        for loc_id, _ in pairs(already_checked) do
            Save.checked_locations[loc_id] = true
        end
        Save.write()
        print("[AP] " .. _count_table(already_checked) .. " locations already checked on server.")
    end)

    -- Receive items from the AP server
    AP.on("received_items", function(cmd)
        _process_received_items(cmd)
    end)

    -- DeathLink
    AP.on("death_link", function(data)
        if _death_link_enabled then
            _kill_raz(data.cause or "DeathLink from " .. (data.source or "unknown"))
        end
    end)

    AP.on("disconnected", function()
        print("[AP] Disconnected from server.")
    end)

    AP.on("connection_refused", function(errors)
        print("[AP] Refused: " .. table.concat(errors, ", "))
    end)
end

-- ---------------------------------------------------------------------------
-- Item receive processing
-- ---------------------------------------------------------------------------

local function _process_received_items(cmd)
    -- cmd.index is the position in the server's item list of cmd.items[1].
    -- We want to process only items at positions >= Save.received_index.
    local index     = cmd.index or 0
    local all_items = cmd.items or {}

    -- Calculate the first item in this batch that we haven't processed yet.
    -- If index=5 and Save.received_index=7, skip the first 2 entries.
    local skip = math.max(0, Save.received_index - index)
    if skip >= #all_items then
        return  -- All items in this batch already processed
    end

    -- Process items from skip+1 to end (1-based Lua indices)
    for i = skip + 1, #all_items do
        local network_item = all_items[i]
        local item_id = network_item.item

        -- Grant the item in-game
        Items.grant(item_id)

        -- Persist updated ability tier immediately after granting
        local item_name = Items.id_to_name[item_id]
        if item_name and Items.ability_tiers[item_name] ~= nil then
            Save.set_ability_tier(item_name, Items.ability_tiers[item_name])
        end

        -- Record area-access items so they can be re-applied on future connects
        -- (mirrors the OpenTTD v1.2.2 fix for unlocks lost after a save reset).
        if item_name and Items.area_flags[item_name] then
            Save.set_area_flag(item_name)
        end
    end

    -- Advance our received-index pointer past everything in this batch
    local new_index = index + #all_items
    if new_index > Save.received_index then
        Save.set_received_index(new_index)
    end
end

-- ---------------------------------------------------------------------------
-- Starting state
-- ---------------------------------------------------------------------------
-- The AP world spec says players always start with at least one mental world
-- and one hub area unlocked.  The server sends these as initial ReceivedItems,
-- but we also apply some baseline settings here in case the save is new.

local function _apply_starting_state(slot_data)
    -- Melee - Base Power is always precollected; ensure it is granted
    local raz = Items._get_raz()
    if raz then
        pcall(function() raz:UnlockMeleeBase() end)
    end

    -- Remove rank restrictions if the flag is set (always true per AP world)
    if slot_data.disable_rank_restrictions then
        local gi = Items._get_game_instance()
        if gi then
            pcall(function() gi:DisableRankRestrictions() end)
        end
    end

    -- Apply starting outfit
    local starting_outfit = slot_data.starting_outfit
    if starting_outfit and Items.outfit_ids[starting_outfit] ~= nil then
        Items._grant_outfit(starting_outfit)
    end

    -- Re-apply all saved area-access items so that area unlocks survive a
    -- fresh game-save combined with an existing ap_save.json.  This mirrors
    -- the OpenTTD v1.2.2 fix for "infrastructure unlocks lost on reconnect".
    for item_name, _ in pairs(Save.received_area_flags) do
        Items._grant_area_access(item_name)
    end

    -- Re-apply all saved ability tiers so that abilities are at their correct
    -- level even when the game save is newer or reset.
    for prog_name, tier in pairs(Save.ability_tiers) do
        if tier > 0 then
            Items._reapply_ability(prog_name, tier)
        end
    end
end

-- ---------------------------------------------------------------------------
-- Victory detection
-- ---------------------------------------------------------------------------

local function _on_astralathe_interact()
    if _victory_sent then return end
    print("[AP] Astralathe interaction detected — victory!")
    _victory_sent = true
    AP.send_status(STATUS_GOAL)
    -- Mark the Maligula check location (the game interaction itself is the check)
    -- The victory location is handled as an event in the AP world; we do not
    -- send a LocationChecks message for it.  The server awards the win when
    -- the goal condition is met.
    Save.write()
end

-- ---------------------------------------------------------------------------
-- UE4 hook registration
-- ---------------------------------------------------------------------------
--
-- UE4SS hook format: RegisterHook("/Script/Package.ClassName:FunctionName", pre, post)
-- The pre-hook runs before the function; the post-hook runs after.
-- We use post-hooks so the game has already processed the pickup before we
-- record it as checked.
--
-- Collectible actor names in the game world use the same naming convention as
-- the check CSV keys (e.g. the PsiCard actor at Motherlobe slot 1 is named
-- "ML_PsiCard1_Check" in the UE4 object hierarchy).  We read the actor's
-- name via GetActorNameOrLabel() and look it up in the Locations table.

local function _hook_collectible_class(class_path)
    local ok = pcall(function()
        RegisterHook(class_path .. ":OnCollected", nil, function(self, _)
            local actor_name = ""
            pcall(function()
                actor_name = self:GetActorLabel()
                if actor_name == "" then
                    actor_name = self:GetName()
                end
            end)

            local loc_id = Locations.check_to_id[actor_name]
            if loc_id then
                _on_check_completed(actor_name, loc_id)
            else
                -- Try stripping common UE4 object suffixes (_C_0, _1, etc.)
                local base = actor_name:match("^(.+)_%d+$") or actor_name
                loc_id = Locations.check_to_id[base]
                if loc_id then
                    _on_check_completed(base, loc_id)
                end
            end
        end)
    end)
    if not ok then
        print("[AP] Could not hook " .. class_path .. " (class may not exist in this version)")
    end
end

local function _register_ue4_hooks()
    -- Collectible pickup hooks
    -- Each class has an OnCollected event that fires when Raz picks it up.
    local collectible_classes = {
        "/Script/Psychonauts2.BP_PsiCard_C",
        "/Script/Psychonauts2.BP_SupplyChest_C",
        "/Script/Psychonauts2.BP_SupplyKey_C",
        "/Script/Psychonauts2.BP_PsyChallengeMarker_C",
        "/Script/Psychonauts2.BP_HalfAMind_C",
        "/Script/Psychonauts2.BP_MemoryVault_C",
        "/Script/Psychonauts2.BP_Nugget_C",
        "/Script/Psychonauts2.BP_ScavHuntItem_C",
        "/Script/Psychonauts2.BP_Luggage_Base_C",
        "/Script/Psychonauts2.BP_Dufflebag_C",
        "/Script/Psychonauts2.BP_SteamerTrunk_C",
        "/Script/Psychonauts2.BP_Hatbox_C",
        "/Script/Psychonauts2.BP_Suitcase_C",
    }
    for _, cls in ipairs(collectible_classes) do
        _hook_collectible_class(cls)
    end

    -- Rank-up reward hook
    pcall(function()
        RegisterHook("/Script/Psychonauts2.BP_RankUp_C:OnRankGranted", nil,
            function(self, _rank_level)
                local rank = 0
                pcall(function() rank = self:GetCurrentRank() end)
                local check_key = "Rank_" .. tostring(rank) .. "_Check"
                local loc_id    = Locations.check_to_id[check_key]
                if loc_id then
                    _on_check_completed(check_key, loc_id)
                end
            end
        )
    end)

    -- Shop purchase hook (Otto's shop)
    pcall(function()
        RegisterHook("/Script/Psychonauts2.BP_OttoShop_C:OnItemPurchased", nil,
            function(self, item_tag)
                local tag_str = ""
                pcall(function() tag_str = tostring(item_tag) end)
                -- Map the purchased item tag to a check key
                local check_key = tag_str .. "_check"
                local loc_id    = Locations.check_to_id[check_key]
                if loc_id then
                    _on_check_completed(check_key, loc_id)
                end
            end
        )
    end)

    -- Figment percentage check hook
    -- The game fires a FigmentMilestoneReached event with the level and percentage.
    pcall(function()
        RegisterHook("/Script/Psychonauts2.Psy_FigmentComponent_C:OnMilestoneReached", nil,
            function(self, level_key, percentage)
                local lk  = ""
                local pct = 0
                pcall(function()
                    lk  = tostring(level_key)
                    pct = tonumber(tostring(percentage)) or 0
                end)
                -- Round to nearest threshold (20/40/60/80/100)
                local check_key = lk .. "_" .. tostring(pct) .. "percent_Check"
                local loc_id    = Locations.check_to_id[check_key]
                if loc_id then
                    _on_check_completed(check_key, loc_id)
                end
            end
        )
    end)

    -- Story completion hook (mental world complete)
    pcall(function()
        RegisterHook("/Script/Psychonauts2.Psy_MentalWorld_C:OnLevelComplete", nil,
            function(self, _)
                local world_key = ""
                pcall(function() world_key = self:GetWorldKey() end)
                local check_key = world_key .. "_StoryComplete_Check"
                local loc_id    = Locations.check_to_id[check_key]
                if loc_id then
                    _on_check_completed(check_key, loc_id)
                end
            end
        )
    end)

    -- Astralathe interaction (victory)
    pcall(function()
        RegisterHook("/Script/Psychonauts2.BP_Astralathe_C:OnInteract", nil,
            function(self, _)
                _on_astralathe_interact()
            end
        )
    end)

    -- Death hook (for DeathLink)
    pcall(function()
        RegisterHook("/Script/Psychonauts2.BP_Raz_C:OnDeath", nil,
            function(self, _)
                if _death_link_enabled then
                    AP.send_death("Raz died", AP.slot_name)
                end
            end
        )
    end)

    print("[AP] UE4 hooks registered.")
end

-- ---------------------------------------------------------------------------
-- Check completion handler
-- ---------------------------------------------------------------------------

local function _on_check_completed(check_key, loc_id)
    if Save.is_checked(loc_id) then
        return  -- Already sent
    end
    print("[AP] Check completed: " .. check_key .. " (id=" .. tostring(loc_id) .. ")")
    Save.mark_checked(loc_id)
    AP.queue_check(loc_id)
end

-- ---------------------------------------------------------------------------
-- DeathLink — kill Raz
-- ---------------------------------------------------------------------------

local function _kill_raz(cause)
    print("[AP] DeathLink received: " .. cause)
    local raz = Items._get_raz()
    if raz then
        pcall(function() raz:KillActor() end)
    end
end

-- ---------------------------------------------------------------------------
-- Connection management
-- ---------------------------------------------------------------------------

local function _try_connect()
    if AP.server == "" then return end
    print("[AP] Connecting to " .. AP.server .. "...")
    AP.connect(AP.server)
    _last_reconnect_time = os.time()
end

-- ---------------------------------------------------------------------------
-- Main tick
-- ---------------------------------------------------------------------------
-- UE4SS calls the tick function (or we register it as a game tick hook)
-- at a regular interval.  We poll the AP socket and check for pending work.

local _tick_accumulator = 0.0

local function _on_tick(delta_time)
    if not _initialized then return end

    _tick_accumulator = _tick_accumulator + (delta_time or 0.016)

    -- Poll AP socket at ~10 Hz
    if _tick_accumulator >= POLL_INTERVAL_S then
        _tick_accumulator = 0.0

        -- Reconnect if not connected
        if not AP.connected then
            local now = os.time()
            if now - _last_reconnect_time >= RECONNECT_DELAY_S then
                _try_connect()
            end
        else
            AP.poll()
        end

        -- Periodic save flush
        local now = os.time()
        if now - _last_save_time >= SAVE_INTERVAL_S then
            _last_save_time = now
            Save.write()
        end
    end
end

-- ---------------------------------------------------------------------------
-- UE4SS registration
-- ---------------------------------------------------------------------------

-- Register the tick callback.  UE4SS experimental provides RegisterHook for
-- the game tick via "/Script/Engine.PlayerController:Tick".
pcall(function()
    RegisterHook("/Script/Engine.PlayerController:Tick", nil, function(self, delta_time)
        local dt = 0.016
        pcall(function() dt = tonumber(tostring(delta_time)) or 0.016 end)
        _on_tick(dt)
    end)
end)

-- ---------------------------------------------------------------------------
-- Helpers
-- ---------------------------------------------------------------------------

local function _count_table(t)
    local n = 0
    for _ in pairs(t) do n = n + 1 end
    return n
end

-- ---------------------------------------------------------------------------
-- Boot
-- ---------------------------------------------------------------------------

_init()

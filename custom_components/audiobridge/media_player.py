from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from .const import DOMAIN
from .audiobridge_api import AudioBridgeAPI

SOURCES = {
    "Entrada 1": 1, "Entrada 2": 2, "Entrada 3": 3, "Entrada 4": 4,
    "Entrada 5": 5, "Entrada 6": 6, "Entrada 7": 7, "Entrada 8": 8
}

async def async_setup_entry(hass, config_entry, async_add_entities):
    data = hass.data[DOMAIN][config_entry.entry_id]
    api = AudioBridgeAPI(data[CONF_HOST], data[CONF_PORT])
    
    # Adiciona as 8 zonas suportadas pela matriz AudioBRIDGE[cite: 1]
    entities = []
    for zone_id in range(1, 9):
        entities.append(AudioBridgeZone(api, controller_id=1, zone_id=zone_id))
    
    async_add_entities(entities, update_before_add=True)

class AudioBridgeZone(MediaPlayerEntity):
    def __init__(self, api: AudioBridgeAPI, controller_id: int, zone_id: int):
        self._api = api
        self._controller_id = controller_id
        self._zone_id = zone_id
        self._attr_name = f"AudioBRIDGE Zona {zone_id}"
        self._attr_unique_id = f"audiobridge_{controller_id}_{zone_id}"
        self._state = MediaPlayerState.OFF
        self._volume = 0.0
        self._is_mute = False
        self._source = "Entrada 1"

    @property
    def supported_features(self):
        return (
            MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.SELECT_SOURCE
        )

    @property
    def state(self):
        return self._state

    @property
    def volume_level(self):
        return self._volume / 38.0  # Mapeia escopo de 0 a 38[cite: 1] para 0.0 a 1.0

    @property
    def is_volume_muted(self):
        return self._is_mute

    @property
    def source(self):
        return self._source

    @property
    def source_list(self):
        return list(SOURCES.keys())

    async def async_update(self):
        data = await self._api.get_zone_status(self._controller_id, self._zone_id)
        self._state = MediaPlayerState.ON if data["power"] else MediaPlayerState.OFF
        self._is_mute = data["mute"]
        self._volume = data["volume"]
        
        # Mapeia ID da fonte para o nome legível
        for name, src_id in SOURCES.items():
            if src_id == data["source"]:
                self._source = name

    async def async_turn_on(self):
        await self._api.set_power(self._controller_id, self._zone_id, True)
        self._state = MediaPlayerState.ON

    async def async_turn_off(self):
        await self._api.set_power(self._controller_id, self._zone_id, False)
        self._state = MediaPlayerState.OFF

    async def async_set_volume_level(self, volume):
        vol_38 = int(volume * 38)
        await self._api.set_volume(self._controller_id, self._zone_id, vol_38)
        self._volume = vol_38

    async def async_mute_volume(self, mute):
        await self._api.set_mute(self._controller_id, self._zone_id, mute)
        self._is_mute = mute

    async def async_select_source(self, source):
        if source in SOURCES:
            await self._api.set_source(self._controller_id, self._zone_id, SOURCES[source])
            self._source = source
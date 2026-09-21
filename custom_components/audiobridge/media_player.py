from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.entity import DeviceInfo

from .audiobridge_api import AudioBridgeAPI
from .const import DOMAIN

SOURCES = {
    "Entrada 1": 1,
    "Entrada 2": 2,
    "Entrada 3": 3,
    "Entrada 4": 4,
    "Entrada 5": 5,
    "Entrada 6": 6,
    "Entrada 7": 7,
    "Entrada 8": 8,
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    data = hass.data[DOMAIN][config_entry.entry_id]
    api = AudioBridgeAPI(data[CONF_HOST], data[CONF_PORT])

    model_name = data.get("model", "AudioBRIDGE Matrix")
    host = data[CONF_HOST]

    entities = []
    for zone_id in range(1, 9):
        entities.append(
            AudioBridgeZone(
                api=api,
                controller_id=1,
                zone_id=zone_id,
                entry_id=config_entry.entry_id,
                host=host,
                model_name=model_name,
            )
        )

    async_add_entities(entities, update_before_add=True)


class AudioBridgeZone(MediaPlayerEntity):
    def __init__(
        self,
        api: AudioBridgeAPI,
        controller_id: int,
        zone_id: int,
        entry_id: str,
        host: str,
        model_name: str,
    ):
        self._api = api
        self._controller_id = controller_id
        self._zone_id = zone_id
        self._entry_id = entry_id
        self._host = host
        self._model_name = model_name

        self._attr_name = f"AudioBRIDGE Zona {zone_id}"
        self._attr_unique_id = f"audiobridge_{entry_id}_zone_{zone_id}"

        self._state = MediaPlayerState.OFF
        self._volume = 0.0
        self._is_mute = False
        self._source = "Entrada 1"

    @property
    def device_info(self) -> DeviceInfo:
        """Cria e vincula esta entidade ao Dispositivo Pai (Matriz AudioBRIDGE)."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=f"AudioBRIDGE ({self._host})",
            manufacturer="AudioBRIDGE",
            model=self._model_name,
            configuration_url=f"http://{self._host}",
        )

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
        return self._volume / 38.0  # Mapeia de 0..38 para 0.0..1.0

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
        """Lê o status da zona e atualiza as variáveis da entidade."""
        data = await self._api.get_zone_status(self._controller_id, self._zone_id)

        if not data:
            return

        self._state = (
            MediaPlayerState.ON if data.get("power", False) else MediaPlayerState.OFF
        )
        self._is_mute = data.get("mute", False)
        self._volume = data.get("volume", 0)

        for name, src_id in SOURCES.items():
            if src_id == data.get("source", 1):
                self._source = name

    async def async_turn_on(self):
        """Liga a zona e avisa a interface do HA imediatamente."""
        await self._api.set_power(self._controller_id, self._zone_id, True)
        self._state = MediaPlayerState.ON
        self.async_write_ha_state()

    async def async_turn_off(self):
        """Desliga a zona e avisa a interface do HA imediatamente."""
        await self._api.set_power(self._controller_id, self._zone_id, False)
        self._state = MediaPlayerState.OFF
        self.async_write_ha_state()

    async def async_set_volume_level(self, volume):
        """Ajusta o volume (0.0 a 1.0) para a escala 0 a 38."""
        vol_38 = int(volume * 38)
        await self._api.set_volume(self._controller_id, self._zone_id, vol_38)
        self._volume = vol_38
        self.async_write_ha_state()

    async def async_mute_volume(self, mute):
        """Ativa ou desativa o mute."""
        await self._api.set_mute(self._controller_id, self._zone_id, mute)
        self._is_mute = mute
        self.async_write_ha_state()

    async def async_select_source(self, source):
        """Muda a fonte de entrada de áudio."""
        if source in SOURCES:
            await self._api.set_source(
                self._controller_id, self._zone_id, SOURCES[source]
            )
            self._source = source
            self.async_write_ha_state()
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.const import CONF_HOST
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SOURCES


async def async_setup_entry(hass, config_entry, async_add_entities):
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    api = entry_data["api"]
    coordinator = entry_data["coordinator"]
    host = config_entry.data[CONF_HOST]
    model_name = config_entry.data.get("model", "AudioBRIDGE Matrix")

    entities = []
    for zone_id in range(1, 9):
        # Lê o nome configurado pelo utilizador ou usa o padrão "AudioBRIDGE Zona X"
        custom_name = config_entry.options.get(
            f"zone_{zone_id}_name", f"Zona {zone_id}"
        )
        full_name = f"AudioBRIDGE {custom_name}"

        entities.append(
            AudioBridgeZone(
                coordinator=coordinator,
                api=api,
                controller_id=1,
                zone_id=zone_id,
                entry_id=config_entry.entry_id,
                host=host,
                model_name=model_name,
                zone_name=full_name,
            )
        )

    async_add_entities(entities)


class AudioBridgeZone(CoordinatorEntity, MediaPlayerEntity):
    def __init__(
        self,
        coordinator,
        api,
        controller_id: int,
        zone_id: int,
        entry_id: str,
        host: str,
        model_name: str,
        zone_name: str,
    ):
        super().__init__(coordinator)
        self._api = api
        self._controller_id = controller_id
        self._zone_id = zone_id
        self._entry_id = entry_id
        self._host = host
        self._model_name = model_name

        self._attr_name = zone_name
        self._attr_unique_id = f"audiobridge_{entry_id}_zone_{zone_id}"

    @property
    def device_info(self) -> DeviceInfo:
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
    def zone_data(self):
        if self.coordinator.data and self._zone_id in self.coordinator.data:
            return self.coordinator.data[self._zone_id]
        return {}

    @property
    def state(self):
        return (
            MediaPlayerState.ON
            if self.zone_data.get("power", False)
            else MediaPlayerState.OFF
        )

    @property
    def volume_level(self):
        return self.zone_data.get("volume", 0) / 38.0

    @property
    def is_volume_muted(self):
        return self.zone_data.get("mute", False)

    @property
    def source(self):
        current_src_id = self.zone_data.get("source", 1)
        for name, src_id in SOURCES.items():
            if src_id == current_src_id:
                return name
        return "Entrada 1"

    @property
    def source_list(self):
        return list(SOURCES.keys())

    async def async_turn_on(self):
        await self._api.set_power(self._controller_id, self._zone_id, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        await self._api.set_power(self._controller_id, self._zone_id, False)
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume):
        vol_38 = int(volume * 38)
        await self._api.set_volume(self._controller_id, self._zone_id, vol_38)
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute):
        await self._api.set_mute(self._controller_id, self._zone_id, mute)
        await self.coordinator.async_request_refresh()

    async def async_select_source(self, source):
        if source in SOURCES:
            await self._api.set_source(
                self._controller_id, self._zone_id, SOURCES[source]
            )
            await self.coordinator.async_request_refresh()
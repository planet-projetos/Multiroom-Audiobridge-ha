import logging
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.const import CONF_HOST
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SOURCES

_LOGGER = logging.getLogger(__name__)

MAX_VOLUME_LEVEL = 38


async def async_setup_entry(hass, config_entry, async_add_entities):
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    api = entry_data["api"]
    coordinator = entry_data["coordinator"]
    host = config_entry.data[CONF_HOST]
    model_name = config_entry.data.get("model", "AudioBRIDGE Matrix")

    entities = []
    for zone_id in range(1, 9):
        zone_name = config_entry.options.get(
            f"zone_{zone_id}_name", f"Zona {zone_id}"
        )

        entities.append(
            AudioBridgeZone(
                coordinator=coordinator,
                api=api,
                controller_id=1,
                zone_id=zone_id,
                entry_id=config_entry.entry_id,
                host=host,
                model_name=model_name,
                zone_name=zone_name,
            )
        )

    async_add_entities(entities)


class AudioBridgeZone(CoordinatorEntity, MediaPlayerEntity):
    """Representa cada zona individual de áudio da matriz."""

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
        
        # Estado interno de apoio para resposta imediata ao clicar no botão
        self._assumed_power = None

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
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Habilita controle de volume, seleção de fonte e liga/desliga."""
        return (
            MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.SELECT_SOURCE
        )

    @property
    def zone_data(self) -> dict:
        """Retorna os dados atualizados da zona."""
        if self.coordinator.data and self._zone_id in self.coordinator.data:
            return self.coordinator.data[self._zone_id]
        return {}

    @property
    def state(self) -> MediaPlayerState:
        """Estado da zona. Usa estado otimista se houver um clique recente."""
        if self._assumed_power is not None:
            return MediaPlayerState.ON if self._assumed_power else MediaPlayerState.OFF

        is_powered = self.zone_data.get("power", False)
        return MediaPlayerState.ON if is_powered else MediaPlayerState.OFF

    @property
    def icon(self) -> str:
        """Define explicitamente os ícones pedidos."""
        if self.state == MediaPlayerState.ON:
            return "mdi:speaker"
        return "mdi:speaker-off"

    @property
    def volume_level(self) -> float | None:
        """Nível de volume normalizado de 0.0 a 1.0."""
        if "volume" not in self.zone_data:
            return None
        raw_vol = self.zone_data.get("volume", 0)
        return min(max(raw_vol / float(MAX_VOLUME_LEVEL), 0.0), 1.0)

    @property
    def is_volume_muted(self) -> bool:
        return self.zone_data.get("mute", False)

    @property
    def source(self) -> str:
        current_src_id = self.zone_data.get("source", 1)
        for name, src_id in SOURCES.items():
            if src_id == current_src_id:
                return name
        return "Entrada 1"

    @property
    def source_list(self) -> list[str]:
        return list(SOURCES.keys())

    def _handle_coordinator_update(self) -> None:
        """Limpa o estado otimista somente após receber power válido."""
        if self.zone_data.get("_valid", False):
            self._assumed_power = None
        super()._handle_coordinator_update()

    async def async_turn_on(self):
        """Liga a zona individualmente."""
        self._assumed_power = True
        self.async_write_ha_state()
        
        await self._api.set_power(self._controller_id, self._zone_id, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        """Desliga a zona individualmente."""
        self._assumed_power = False
        self.async_write_ha_state()

        await self._api.set_power(self._controller_id, self._zone_id, False)
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume: float):
        """Ajusta o volume da zona (0.0..1.0 -> 0..38)."""
        vol_38 = int(round(volume * MAX_VOLUME_LEVEL))
        vol_38 = min(max(vol_38, 0), MAX_VOLUME_LEVEL)

        await self._api.set_volume(self._controller_id, self._zone_id, vol_38)
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool):
        """Ativa/Desativa o Mute."""
        await self._api.set_mute(self._controller_id, self._zone_id, mute)
        await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str):
        """Seleção de entrada de áudio."""
        if source in SOURCES:
            await self._api.set_source(
                self._controller_id, self._zone_id, SOURCES[source]
            )
            await self.coordinator.async_request_refresh()
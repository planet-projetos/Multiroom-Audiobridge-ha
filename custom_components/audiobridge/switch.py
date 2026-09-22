from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_HOST
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    api = entry_data["api"]
    coordinator = entry_data["coordinator"]
    host = config_entry.data[CONF_HOST]

    entities = [
        AudioBridgeGlobalMuteSwitch(
            coordinator=coordinator,
            api=api,
            entry_id=config_entry.entry_id,
            host=host,
        ),
        AudioBridgeGlobalPowerSwitch(
            coordinator=coordinator,
            api=api,
            entry_id=config_entry.entry_id,
            host=host,
        ),
    ]

    async_add_entities(entities)


class AudioBridgeGlobalPowerSwitch(CoordinatorEntity, SwitchEntity):
    """Switch global 'Power'."""

    def __init__(self, coordinator, api, entry_id: str, host: str):
        super().__init__(coordinator)
        self._api = api
        self._entry_id = entry_id
        self._host = host
        self._attr_name = "Power"
        self._attr_icon = "mdi:power"
        self._attr_unique_id = f"audiobridge_{entry_id}_switch_power"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=f"AudioBRIDGE ({self._host})",
            manufacturer="AudioBRIDGE",
            model="AudioBRIDGE Matrix",
            configuration_url=f"http://{self._host}",
        )

    @property
    def is_on(self) -> bool:
        # Se pelo menos uma zona estiver ligada, considerá-lo ON
        if self.coordinator.data:
            return any(
                z_data.get("power", False)
                for z_data in self.coordinator.data.values()
            )
        return False

    async def async_turn_on(self, **kwargs):
        for z in range(1, 9):
            await self._api.set_power(1, z, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        for z in range(1, 9):
            await self._api.set_power(1, z, False)
        await self.coordinator.async_request_refresh()


class AudioBridgeGlobalMuteSwitch(CoordinatorEntity, SwitchEntity):
    """Switch global 'Mute All'."""

    def __init__(self, coordinator, api, entry_id: str, host: str):
        super().__init__(coordinator)
        self._api = api
        self._entry_id = entry_id
        self._host = host
        self._attr_name = "Mute All"
        self._attr_icon = "mdi:volume-off"
        self._attr_unique_id = f"audiobridge_{entry_id}_switch_mute_all"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=f"AudioBRIDGE ({self._host})",
            manufacturer="AudioBRIDGE",
            model="AudioBRIDGE Matrix",
            configuration_url=f"http://{self._host}",
        )

    @property
    def is_on(self) -> bool:
        # Se todas as zonas ligadas estiverem em mute, considerá-lo ON
        if self.coordinator.data:
            active_zones = [
                z_data for z_data in self.coordinator.data.values() if z_data.get("power", False)
            ]
            if not active_zones:
                return False
            return all(z_data.get("mute", False) for z_data in active_zones)
        return False

    async def async_turn_on(self, **kwargs):
        for z in range(1, 9):
            await self._api.set_mute(1, z, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        for z in range(1, 9):
            await self._api.set_mute(1, z, False)
        await self.coordinator.async_request_refresh()
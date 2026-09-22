from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_HOST
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    api = entry_data["api"]
    coordinator = entry_data["coordinator"]
    host = config_entry.data[CONF_HOST]

    entities = [
        AudioBridgeButton(
            api=api,
            coordinator=coordinator,
            entry_id=config_entry.entry_id,
            host=host,
            action="turn_off_all",
            name="Desligar todas as zonas",
            icon="mdi:volume-off",
        ),
        AudioBridgeButton(
            api=api,
            coordinator=coordinator,
            entry_id=config_entry.entry_id,
            host=host,
            action="unmute_all",
            name="Desmutar tudo",
            icon="mdi:volume-high",
        ),
        AudioBridgeButton(
            api=api,
            coordinator=coordinator,
            entry_id=config_entry.entry_id,
            host=host,
            action="turn_on_all",
            name="Ligar todas as zonas",
            icon="mdi:speaker-multiple",
        ),
        AudioBridgeButton(
            api=api,
            coordinator=coordinator,
            entry_id=config_entry.entry_id,
            host=host,
            action="mute_all",
            name="Mutar tudo",
            icon="mdi:volume-mute",
        ),
    ]

    async_add_entities(entities)


class AudioBridgeButton(ButtonEntity):
    def __init__(
        self,
        api,
        coordinator,
        entry_id: str,
        host: str,
        action: str,
        name: str,
        icon: str,
    ):
        self._api = api
        self._coordinator = coordinator
        self._entry_id = entry_id
        self._host = host
        self._action = action
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"audiobridge_{entry_id}_btn_{action}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=f"AudioBRIDGE ({self._host})",
            manufacturer="AudioBRIDGE",
            model="AudioBRIDGE Matrix",
            configuration_url=f"http://{self._host}",
        )

    async def async_press(self) -> None:
        if self._action == "turn_on_all":
            for z in range(1, 9):
                await self._api.set_power(1, z, True)
        elif self._action == "turn_off_all":
            for z in range(1, 9):
                await self._api.set_power(1, z, False)
        elif self._action == "mute_all":
            for z in range(1, 9):
                await self._api.set_mute(1, z, True)
        elif self._action == "unmute_all":
            for z in range(1, 9):
                await self._api.set_mute(1, z, False)

        await self._coordinator.async_request_refresh()
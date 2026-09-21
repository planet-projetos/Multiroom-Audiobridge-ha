from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.entity import DeviceInfo

from .audiobridge_api import AudioBridgeAPI
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    data = hass.data[DOMAIN][config_entry.entry_id]
    api = AudioBridgeAPI(data[CONF_HOST], data[CONF_PORT])
    host = data[CONF_HOST]

    entities = [
        AudioBridgeMasterButton(
            api=api,
            entry_id=config_entry.entry_id,
            host=host,
            action="turn_on_all",
            name="Ligar Todas as Zonas",
        ),
        AudioBridgeMasterButton(
            api=api,
            entry_id=config_entry.entry_id,
            host=host,
            action="turn_off_all",
            name="Desligar Todas as Zonas",
        ),
    ]

    async_add_entities(entities)


class AudioBridgeMasterButton(ButtonEntity):
    def __init__(self, api: AudioBridgeAPI, entry_id: str, host: str, action: str, name: str):
        self._api = api
        self._entry_id = entry_id
        self._host = host
        self._action = action
        self._attr_name = name
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
        """Ação executada ao apertar o botão."""
        state = True if self._action == "turn_on_all" else False
        for zone_id in range(1, 9):
            await self._api.set_power(1, zone_id, state)
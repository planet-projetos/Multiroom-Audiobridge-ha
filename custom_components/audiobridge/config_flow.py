import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import selector

from .audiobridge_api import AudioBridgeAPI
from .const import (
    DEFAULT_GROUP_NAMES,
    DEFAULT_PORT,
    DEFAULT_SOURCE_NAMES,
    DEFAULT_ZONE_NAMES,
    DOMAIN,
    GROUP_COUNT,
    SOURCE_COUNT,
    ZONE_COUNT,
    parse_group_zone_ids,
)


class AudioBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            api = AudioBridgeAPI(host, port)
            model = await api.get_model()

            if model:
                await self.async_set_unique_id(f"audiobridge_{host}")
                self._abort_if_unique_id_configured()

                self._device_data = {
                    CONF_HOST: host,
                    CONF_PORT: port,
                    "model": model,
                }
                return await self.async_step_names()
            else:
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_names(self, user_input=None):
        if user_input is not None:
            self._names_data = user_input
            return await self.async_step_groups()

        return self.async_show_form(
            step_id="names",
            data_schema=_names_schema(),
        )

    async def async_step_groups(self, user_input=None):
        if user_input is not None:
            options = {**self._names_data, **user_input}
            return self.async_create_entry(
                title=f"AudioBRIDGE ({self._device_data[CONF_HOST]})",
                data=self._device_data,
                options=options,
            )

        return self.async_show_form(
            step_id="groups",
            data_schema=_groups_schema(),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return AudioBridgeOptionsFlowHandler(config_entry)


class AudioBridgeOptionsFlowHandler(config_entries.OptionsFlow):
    """Permite personalizar os nomes das zonas, entradas e grupos nas opções da integração."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            self._names_data = user_input
            return await self.async_step_groups()

        return self.async_show_form(
            step_id="init",
            data_schema=_names_schema(self.config_entry.options),
        )

    async def async_step_groups(self, user_input=None):
        if user_input is not None:
            data = {**self._names_data, **user_input}
            return self.async_create_entry(title="", data=data)

        return self.async_show_form(
            step_id="groups",
            data_schema=_groups_schema(self.config_entry.options),
        )


def _names_schema(options=None):
    options = options or {}
    schema = {}

    for index in range(1, ZONE_COUNT + 1):
        key = f"zone_{index}_name"
        schema[vol.Required(key, default=options.get(key, DEFAULT_ZONE_NAMES[key]))] = str

    for index in range(1, SOURCE_COUNT + 1):
        key = f"source_{index}_name"
        schema[vol.Required(key, default=options.get(key, DEFAULT_SOURCE_NAMES[key]))] = str

    return vol.Schema(schema)


def _groups_schema(options=None):
    options = options or {}
    schema = {}
    zone_options = [
        {"value": str(zone_id), "label": f"Zona {zone_id}"}
        for zone_id in range(1, ZONE_COUNT + 1)
    ]

    for index in range(1, GROUP_COUNT + 1):
        name_key = f"group_{index}_name"
        zones_key = f"group_{index}_zones"
        default_zones = options.get(zones_key, [])
        if isinstance(default_zones, str):
            default_zones = [str(zone_id) for zone_id in parse_group_zone_ids(default_zones)]
        elif default_zones is None:
            default_zones = []
        else:
            default_zones = [str(zone_id) for zone_id in parse_group_zone_ids(default_zones)]

        schema[vol.Optional(name_key, default=options.get(name_key, DEFAULT_GROUP_NAMES[name_key]))] = str
        schema[vol.Optional(zones_key, default=default_zones)] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=zone_options,
                multiple=True,
                custom_value=False,
            )
        )

    return vol.Schema(schema)
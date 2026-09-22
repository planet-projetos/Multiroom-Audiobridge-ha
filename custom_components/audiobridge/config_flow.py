import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .audiobridge_api import AudioBridgeAPI
from .const import DEFAULT_NAME, DEFAULT_PORT, DOMAIN

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

                return self.async_create_entry(
                    title=f"AudioBRIDGE ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        "model": model,
                    },
                )
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return AudioBridgeOptionsFlowHandler(config_entry)


class AudioBridgeOptionsFlowHandler(config_entries.OptionsFlow):
    """Permite personalizar os nomes das zonas nas Opções da Integração."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        schema = {}

        # Cria 8 campos de texto para renomear as zonas
        for z in range(1, 9):
            default_name = options.get(f"zone_{z}_name", f"Zona {z}")
            schema[vol.Optional(f"zone_{z}_name", default=default_name)] = str

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema)
        )
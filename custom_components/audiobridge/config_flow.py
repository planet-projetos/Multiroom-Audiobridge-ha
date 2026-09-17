import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from .const import DOMAIN, DEFAULT_PORT
from .audiobridge_api import AudioBridgeAPI

class AudioBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            api = AudioBridgeAPI(user_input[CONF_HOST], user_input[CONF_PORT])
            model = await api.get_model()
            
            if model:
                return self.async_create_entry(
                    title=f"{model} ({user_input[CONF_HOST]})",
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        "model": model
                    }
                )
            else:
                errors["base"] = "cannot_connect"

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
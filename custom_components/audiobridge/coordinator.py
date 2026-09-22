from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .audiobridge_api import AudioBridgeAPI

_LOGGER = logging.getLogger(__name__)

class AudioBridgeDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, api: AudioBridgeAPI):
        super().__init__(
            hass,
            _LOGGER,
            name="AudioBRIDGE Update Coordinator",
            update_interval=timedelta(seconds=10),
        )
        self.api = api

    async def _async_update_data(self):
        """Consulta o status de todas as 8 zonas sequencialmente."""
        data = {}
        try:
            for zone_id in range(1, 9):
                zone_data = await self.api.get_zone_status(1, zone_id)
                data[zone_id] = zone_data
            return data
        except Exception as err:
            raise UpdateFailed(f"Erro ao atualizar dados do AudioBRIDGE: {err}")
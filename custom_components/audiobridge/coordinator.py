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
            update_interval=timedelta(seconds=5),
        )
        self.api = api

    async def _async_update_data(self):
        """Consulta o status de todas as 8 zonas sequencialmente."""
        previous_data = self.data or {}
        data = {}
        try:
            power_status = await self.api.get_power_status(1)
            volume_status = await self.api.get_volume_status(1)
            for zone_id in range(1, 9):
                previous_zone_data = previous_data.get(zone_id, {})
                zone_data = await self.api.get_zone_status(
                    1,
                    zone_id,
                    previous_zone_data.get("source"),
                )
                if zone_data is None:
                    zone_data = dict(previous_zone_data)
                if zone_id in power_status:
                    zone_data["power"] = power_status[zone_id]
                    zone_data["_valid"] = True
                if zone_id in volume_status:
                    zone_data["volume"] = volume_status[zone_id]
                    zone_data["_valid"] = True
                data[zone_id] = zone_data
            return data
        except Exception as err:
            raise UpdateFailed(f"Erro ao atualizar dados do AudioBRIDGE: {err}")
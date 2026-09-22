import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AudioBridgeDataUpdateCoordinator(DataUpdateCoordinator):
    """Gerencia a consulta periódica de estado da matriz AudioBRIDGE."""

    def __init__(self, hass, api):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            # Atualiza o estado no Home Assistant a cada 5 segundos
            update_interval=timedelta(seconds=10),
        )
        self.api = api

    async def _async_update_data(self):
        """Busca o estado atual de todas as zonas na matriz AudioBRIDGE."""
        try:
            # Obtém o dicionário com o estado de todas as zonas (1 a 8)
            data = await self.api.async_get_all_zones_status()
            return data
        except Exception as err:
            raise UpdateFailed(f"Erro ao comunicar com a AudioBRIDGE: {err}")
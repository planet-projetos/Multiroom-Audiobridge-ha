import asyncio
import logging
import re

_LOGGER = logging.getLogger(__name__)


class AudioBridgeAPI:
    def __init__(self, host: str, port: int = 23):
        self.host = host
        self.port = port

    async def send_command(self, command: str) -> str:
        """Envia um comando Telnet e lê a resposta."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=3.0
            )

            # Aguarda a mensagem inicial de boas-vindas se existir
            try:
                await asyncio.wait_for(reader.read(1024), timeout=0.5)
            except asyncio.TimeoutError:
                pass

            cmd_bytes = f"> {command}\r\n".encode("utf-8")
            writer.write(cmd_bytes)
            await writer.drain()

            # Lê a resposta enviada pela matriz
            response = ""
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                response = data.decode("utf-8", errors="ignore")
            except asyncio.TimeoutError:
                pass

            writer.close()
            await writer.wait_closed()
            return response

        except Exception as err:
            _LOGGER.error("Erro na conexão Telnet com AudioBRIDGE (%s): %s", self.host, err)
            return ""

    async def async_get_all_zones_status(self) -> dict:
        """Consulta o estado real de todas as zonas (1 a 8)."""
        status_dict = {}

        # Loop pelas 8 zonas para obter o estado atualizado
        for z in range(1, 9):
            # Envia comando de consulta para a zona (ex: 11??)
            response = await self.send_command(f"1{z}??")

            # Valores padrão de fallback
            power = False
            volume = 0
            mute = False
            source = 1

            if response:
                # Interpreta retornos do tipo PR (Power), VO (Volume), MU (Mute) e CH (Source)
                # Exemplo de resposta: > 11PR01 / > 11VO19 / > 11MU00 / > 11CH01
                pr_match = re.search(r"1" + str(z) + r"PR(\d{2})", response)
                vo_match = re.search(r"1" + str(z) + r"VO(\d{2})", response)
                mu_match = re.search(r"1" + str(z) + r"MU(\d{2})", response)
                ch_match = re.search(r"1" + str(z) + r"CH(\d{2})", response)

                if pr_match:
                    power = int(pr_match.group(1)) == 1
                if vo_match:
                    volume = int(vo_match.group(1))
                if mu_match:
                    mute = int(mu_match.group(1)) == 1
                if ch_match:
                    source = int(ch_match.group(1))

            status_dict[z] = {
                "power": power,
                "volume": volume,
                "mute": mute,
                "source": source,
            }

        return status_dict

    async def set_power(self, controller_id: int, zone_id: int, state: bool):
        val = "01" if state else "00"
        await self.send_command(f"{controller_id}{zone_id}PR{val}")

    async def set_volume(self, controller_id: int, zone_id: int, volume: int):
        await self.send_command(f"{controller_id}{zone_id}VO{volume:02d}")

    async def set_mute(self, controller_id: int, zone_id: int, state: bool):
        val = "01" if state else "00"
        await self.send_command(f"{controller_id}{zone_id}MU{val}")

    async def set_source(self, controller_id: int, zone_id: int, source: int):
        await self.send_command(f"{controller_id}{zone_id}CH{source:02d}")
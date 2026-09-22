import asyncio
import logging
import re

_LOGGER = logging.getLogger(__name__)


class AudioBridgeAPI:
    def __init__(self, host: str, port: int = 23):
        self.host = host
        self.port = port

    async def send_command(self, command: str) -> str:
        """Envia um comando Telnet pontual para a matriz."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=3.0
            )

            try:
                await asyncio.wait_for(reader.read(1024), timeout=0.3)
            except asyncio.TimeoutError:
                pass

            cmd_bytes = f"> {command}\r\n".encode("utf-8")
            writer.write(cmd_bytes)
            await writer.drain()

            response = ""
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=0.8)
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
        """Consulta o estado de todas as zonas em UMA ÚNICA conexão Telnet."""
        status_dict = {}

        # Inicializa o dicionário padrão para as 8 zonas
        for z in range(1, 9):
            status_dict[z] = {
                "power": False,
                "volume": 0,
                "mute": False,
                "source": 1,
            }

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=4.0
            )

            # Limpa buffer inicial de conexão
            try:
                await asyncio.wait_for(reader.read(1024), timeout=0.3)
            except asyncio.TimeoutError:
                pass

            # Pergunta o estado de cada zona dentro da MESMA conexão
            for z in range(1, 9):
                cmd_bytes = f"> 1{z}??\r\n".encode("utf-8")
                writer.write(cmd_bytes)
                await writer.drain()

                try:
                    data = await asyncio.wait_for(reader.read(1024), timeout=0.4)
                    response = data.decode("utf-8", errors="ignore")

                    pr_match = re.search(r"1" + str(z) + r"PR(\d{2})", response)
                    vo_match = re.search(r"1" + str(z) + r"VO(\d{2})", response)
                    mu_match = re.search(r"1" + str(z) + r"MU(\d{2})", response)
                    ch_match = re.search(r"1" + str(z) + r"CH(\d{2})", response)

                    if pr_match:
                        status_dict[z]["power"] = int(pr_match.group(1)) == 1
                    if vo_match:
                        status_dict[z]["volume"] = int(vo_match.group(1))
                    if mu_match:
                        status_dict[z]["mute"] = int(mu_match.group(1)) == 1
                    if ch_match:
                        status_dict[z]["source"] = int(ch_match.group(1))

                except asyncio.TimeoutError:
                    continue

            writer.close()
            await writer.wait_closed()

        except Exception as err:
            _LOGGER.warning("Falha ao consultar estado da AudioBRIDGE: %s", err)

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
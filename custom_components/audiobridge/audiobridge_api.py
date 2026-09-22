import asyncio
import logging
import re

_LOGGER = logging.getLogger(__name__)


class AudioBridgeAPI:
    def __init__(self, host: str, port: int = 23):
        self.host = host
        self.port = port

    async def _send_raw(self, payload: str) -> str:
        """Envia comandos via Telnet e trata a resposta bruta do equipamento."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=5
            )

            writer.write(f"{payload}\r\n".encode("utf-8"))
            await writer.drain()
            await asyncio.sleep(0.1)

            data = await asyncio.wait_for(reader.read(1024), timeout=5)
            response = data.decode("utf-8", errors="ignore").strip()

            if "Welcome to telnet" in response:
                lines = response.splitlines()
                clean_lines = [
                    line.strip()
                    for line in lines
                    if "Welcome to telnet" not in line and line.strip()
                ]
                if clean_lines:
                    response = clean_lines[0]
                else:
                    extra = await asyncio.wait_for(reader.read(1024), timeout=5)
                    response = extra.decode("utf-8", errors="ignore").strip()

            writer.close()
            await writer.wait_closed()

            _LOGGER.warning("RAW RESPONSE: %r", response)
            _LOGGER.debug(
                "Enviado para AudioBRIDGE (%s): %s | Resposta: %s",
                self.host,
                payload,
                response,
            )
            return response

        except asyncio.TimeoutError:
            _LOGGER.error(
                "Timeout na comunicação Telnet com AudioBRIDGE em %s:%s",
                self.host,
                self.port,
            )
            return ""
        except Exception as err:
            _LOGGER.error(
                "Erro na comunicação Telnet com AudioBRIDGE em %s:%s - %s",
                self.host,
                self.port,
                err,
            )
            return ""

    async def send_command(self, command: str) -> str:
        """Envia um comando de ação para a matriz."""
        return await self._send_raw(f"> {command}")

    async def send_query(self, query: str) -> str:
        """Envia um comando de consulta para a matriz."""
        return await self._send_raw(f"# {query}")

    async def get_model(self) -> str:
        """Consulta o modelo do equipamento."""
        res = await self.send_query("10M")
        if res:
            return res.replace("<", "").strip()
        return "AudioBRIDGE Matrix"

    async def get_zone_status(self, controller_id: int, zone_id: int) -> dict:
        """Consulta o estado completo de uma zona."""
        raw_cmd = f"{controller_id}{zone_id}ST"
        res = await self.send_query(raw_cmd)

        data = {
            "power": False,
            "mute": False,
            "volume": 0,
            "source": 1,
        }

        if "PR" in res:
            pr_match = re.search(r"PR(\d{2})", res)
            if pr_match:
                data["power"] = pr_match.group(1) == "01"

        if "MU" in res:
            mu_match = re.search(r"MU(\d{2})", res)
            if mu_match:
                data["mute"] = mu_match.group(1) == "01"

        if "VO" in res:
            vo_match = re.search(r"VO(\d{2})", res)
            if vo_match:
                data["volume"] = int(vo_match.group(1))

        if "CH" in res:
            ch_match = re.search(r"CH(\d{2})", res)
            if ch_match:
                data["source"] = int(ch_match.group(1))

        return data

    async def set_power(self, controller_id: int, zone_id: int, state: bool):
        val = "01" if state else "00"
        return await self.send_command(f"{controller_id}{zone_id}PR{val}")

    async def set_mute(self, controller_id: int, zone_id: int, state: bool):
        val = "01" if state else "00"
        return await self.send_command(f"{controller_id}{zone_id}MU{val}")

    async def set_volume(self, controller_id: int, zone_id: int, vol_level: int):
        vol_str = f"{vol_level:02d}"
        return await self.send_command(f"{controller_id}{zone_id}VO{vol_str}")

    async def set_source(self, controller_id: int, zone_id: int, source_id: int):
        src_str = f"{source_id:02d}"
        return await self.send_command(f"{controller_id}{zone_id}CH{src_str}")
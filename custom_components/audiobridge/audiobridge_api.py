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
        writer = None
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=5
            )

            writer.write(f"{payload}\r\n".encode("utf-8"))
            await writer.drain()
            chunks = []
            while True:
                try:
                    data = await asyncio.wait_for(reader.read(1024), timeout=0.5)
                except asyncio.TimeoutError:
                    break
                if not data:
                    break
                chunks.append(data)

            response = b"".join(chunks).decode("utf-8", errors="ignore")
            response_lines = [
                line.strip()
                for line in response.splitlines()
                if line.strip() and "Welcome to telnet" not in line
            ]
            response = "\n".join(response_lines)

            _LOGGER.debug("RAW RESPONSE: %r", response)
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
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()

    async def send_command(self, command: str) -> str:
        """Envia um comando de ação usando o prefixo do protocolo."""
        return await self._send_raw(f"> {command}")

    async def send_query(self, query: str) -> str:
        """Envia um comando de consulta usando o prefixo do protocolo."""
        return await self._send_raw(f"# {query}")

    async def get_model(self) -> str:
        """Consulta o modelo do equipamento."""
        res = await self.send_query("DEV")
        if res:
            model_match = re.search(r"MODEL\s+(.+?)(?:\s+V[\d.]+)?$", res, re.MULTILINE)
            if model_match:
                return model_match.group(1).strip()
        return "AudioBRIDGE Matrix"

    async def get_zone_status(self, controller_id: int, zone_id: int) -> dict:
        """Consulta o estado completo de uma zona usando o formato de zona do equipamento."""
        zone_target = int(f"{controller_id}{zone_id}")
        raw_cmd = f"{zone_target}PT00"
        res = await self.send_query(raw_cmd)

        data = {
            "power": False,
            "mute": False,
            "volume": 0,
            "source": 1,
        }

        for field, pattern in (
            ("power", r"PR(\d{2})"),
            ("mute", r"MU(\d{2})"),
            ("volume", r"VO(\d{2})"),
            ("source", r"CH(\d{2})"),
        ):
            match = re.search(pattern, res)
            if match:
                value = int(match.group(1))
                data[field] = value == 1 if field in ("power", "mute") else value

        return data

    async def set_power(self, controller_id: int, zone_id: int, state: bool):
        val = "01" if state else "00"
        zone_target = int(f"{controller_id}{zone_id}")
        return await self.send_command(f"{zone_target}PR{val}")

    async def set_mute(self, controller_id: int, zone_id: int, state: bool):
        val = "01" if state else "00"
        zone_target = int(f"{controller_id}{zone_id}")
        return await self.send_command(f"{zone_target}MU{val}")

    async def set_volume(self, controller_id: int, zone_id: int, vol_level: int):
        vol_str = f"{vol_level:02d}"
        zone_target = int(f"{controller_id}{zone_id}")
        return await self.send_command(f"{zone_target}VO{vol_str}")

    async def set_source(self, controller_id: int, zone_id: int, source_id: int):
        src_str = f"{source_id:02d}"
        zone_target = int(f"{controller_id}{zone_id}")
        return await self.send_command(f"{zone_target}CH{src_str}")
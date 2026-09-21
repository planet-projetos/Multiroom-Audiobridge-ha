import asyncio
import logging
import re

_LOGGER = logging.getLogger(__name__)


class AudioBridgeAPI:
    def __init__(self, host: str, port: int = 23):
        self.host = host
        self.port = port

    async def _read_response(self, reader) -> str:
        """Lê a resposta do socket sem perder o conteúdo do banner de boas-vindas."""
        chunks = []
        deadline = asyncio.get_running_loop().time() + 5

        while asyncio.get_running_loop().time() < deadline:
            try:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=1)
            except asyncio.TimeoutError:
                break

            if not chunk:
                break

            chunks.append(chunk)
            if len(chunk) < 4096:
                break

        data = b"".join(chunks)
        response = data.decode("utf-8", errors="ignore").strip()

        if not response:
            return ""

        lines = [line.strip() for line in response.splitlines() if line.strip()]
        clean_lines = [
            line for line in lines if "Welcome to telnet" not in line and line not in (">", "#")
        ]

        if clean_lines:
            response = clean_lines[0]

        return response

    async def _send_raw(self, payload: str) -> str:
        """Envia a string formatada e trata a recepção via Telnet."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=5
            )

            cmd_formatted = f"{payload}\r\n".encode("utf-8")
            writer.write(cmd_formatted)
            await writer.drain()

            response = await self._read_response(reader)

            writer.close()
            await writer.wait_closed()

            _LOGGER.debug("Enviado: %s | Resposta: %s", payload, response)
            return response

        except asyncio.TimeoutError:
            _LOGGER.error(
                "Timeout de conexão Telnet com AudioBRIDGE em %s:%s",
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
        """Envia comandos de ação/escrita iniciados por '> '."""
        return await self._send_raw(f"> {command}")

    async def send_query(self, query: str) -> str:
        """Envia requisições de estado/status iniciadas por '# '."""
        return await self._send_raw(f"# {query}")

    async def get_model(self) -> str:
        """Consulta o modelo do equipamento via comando de status # 10M."""
        res = await self.send_query("10M")
        if res:
            return res.replace("<", "").strip()
        return "AudioBRIDGE Matrix"

    async def get_zone_status(self, controller_id: int, zone_id: int) -> dict:
        """Consulta o status completo de uma zona usando # XYST (ex: # 11ST)."""
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
                data["power"] = pr_match.group(1) != "00"

        if "MU" in res:
            mu_match = re.search(r"MU(\d{2})", res)
            if mu_match:
                data["mute"] = mu_match.group(1) != "00"

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
        await self.send_command(f"{controller_id}{zone_id}PR{val}")

    async def set_mute(self, controller_id: int, zone_id: int, state: bool):
        val = "01" if state else "00"
        await self.send_command(f"{controller_id}{zone_id}MU{val}")

    async def set_volume(self, controller_id: int, zone_id: int, vol_level: int):
        vol_str = f"{vol_level:02d}"
        await self.send_command(f"{controller_id}{zone_id}VO{vol_str}")

    async def set_source(self, controller_id: int, zone_id: int, source_id: int):
        src_str = f"{source_id:02d}"
        await self.send_command(f"{controller_id}{zone_id}CH{src_str}")
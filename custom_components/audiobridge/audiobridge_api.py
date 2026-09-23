import asyncio
import logging
import re

_LOGGER = logging.getLogger(__name__)


def parse_zone_status_response(response: str, previous_source: int | None = None) -> dict | None:
    """Parsea a resposta de status da zona do AudioBRIDGE."""
    data = {
        "power": False,
        "mute": False,
        "volume": 0,
        "source": previous_source if previous_source is not None else 1,
        "group": 0,
        "_valid": False,
        "_source_confirmed": False,
    }
    found_field = False

    for field, pattern in (
        ("group", r"(?i)(?:^|[^A-Z])PT(?:\s*)0*(\d{1,2})(?=PR)"),
        ("power", r"(?i)(?:^|[^A-Z])PR(?:\s*)0*(\d{1,2})(?!\d)"),
        ("mute", r"(?i)(?:^|[^A-Z])MU(?:\s*)0*(\d{1,2})(?!\d)"),
        ("volume", r"(?i)(?:^|[^A-Z])VO(?:\s*)0*(\d{1,2})(?!\d)"),
        ("source", r"(?i)(?:^|[^A-Z])CH(?:\s*)0*(\d{1,2})(?!\d)"),
    ):
        match = re.search(pattern, response)
        if not match:
            continue

        found_field = True
        value = int(match.group(1))
        if field == "group":
            data[field] = value if 0 <= value <= 3 else 0
        elif field in ("power", "mute"):
            data[field] = bool(value)
        elif field == "source":
            if 1 <= value <= 8:
                data[field] = value
                data["_source_confirmed"] = True
            elif previous_source is not None:
                data[field] = previous_source
            else:
                data[field] = 1
        else:
            data[field] = value

    if previous_source is not None and not data["_source_confirmed"]:
        data["source"] = previous_source

    data["_valid"] = found_field
    return data if found_field else None


class AudioBridgeAPI:
    def __init__(self, host: str, port: int = 23):
        self.host = host
        self.port = port
        self._reader = None
        self._writer = None
        self._connection_lock = asyncio.Lock()

    async def _close_connection(self) -> None:
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except (ConnectionError, OSError):
                pass
        self._reader = None
        self._writer = None

    async def async_close(self) -> None:
        """Fecha a conexão Telnet quando a integração é descarregada."""
        async with self._connection_lock:
            await self._close_connection()

    async def _send_raw(self, payload: str) -> str:
        """Envia comandos via Telnet e trata a resposta bruta do equipamento."""
        async with self._connection_lock:
            try:
                if self._writer is None or self._writer.is_closing():
                    self._reader, self._writer = await asyncio.wait_for(
                        asyncio.open_connection(self.host, self.port), timeout=5
                    )

                self._writer.write(f"{payload}\r\n".encode("utf-8"))
                await self._writer.drain()
                chunks = []
                connection_closed = False
                while True:
                    try:
                        data = await asyncio.wait_for(self._reader.read(1024), timeout=0.5)
                    except asyncio.TimeoutError:
                        break
                    if not data:
                        connection_closed = True
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
                if connection_closed:
                    await self._close_connection()
                return response

            except asyncio.TimeoutError:
                _LOGGER.error(
                    "Timeout na comunicação Telnet com AudioBRIDGE em %s:%s",
                    self.host,
                    self.port,
                )
            except Exception as err:
                _LOGGER.error(
                    "Erro na comunicação Telnet com AudioBRIDGE em %s:%s - %s",
                    self.host,
                    self.port,
                    err,
                )
            await self._close_connection()
            return ""

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

    async def get_zone_status(
        self, controller_id: int, zone_id: int, previous_source: int | None = None
    ) -> dict | None:
        """Consulta o estado completo de uma zona usando o formato de zona do equipamento."""
        zone_target = int(f"{controller_id}{zone_id}")
        raw_cmd = f"{zone_target}PT00"
        res = await self.send_query(raw_cmd)
        return parse_zone_status_response(res, previous_source=previous_source)

    async def get_power_status(self, controller_id: int) -> dict[int, bool]:
        """Consulta o power de todas as zonas usando a consulta global do equipamento."""
        res = await self.send_query(f"{controller_id}0PR")
        power_status = {}
        for match in re.finditer(r"<(?:\s*)?(\d)(\d)PR(\d{2})", res):
            zone_id = int(match.group(2))
            power_status[zone_id] = match.group(3) == "01"
        return power_status

    async def get_volume_status(self, controller_id: int) -> dict[int, int]:
        """Consulta o volume de todas as zonas usando a consulta global do equipamento."""
        res = await self.send_query(f"{controller_id}0VO")
        volume_status = {}
        for match in re.finditer(r"<(?:\s*)?(\d)(\d)VO(\d{1,2})", res):
            zone_id = int(match.group(2))
            volume_status[zone_id] = int(match.group(3))
        return volume_status

    async def get_group_status(self, controller_id: int) -> dict[int, int]:
        """Consulta a associação das zonas aos grupos do controlador."""
        res = await self.send_query(f"{controller_id}0PT")
        group_status = {}
        for match in re.finditer(r"<(?:\s*)?(\d)(\d)PT(\d{2})PR", res):
            zone_id = int(match.group(2))
            group_status[zone_id] = int(match.group(3))
        return group_status

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
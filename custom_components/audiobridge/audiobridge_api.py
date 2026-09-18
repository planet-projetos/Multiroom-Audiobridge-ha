import asyncio
import logging
import re

_LOGGER = logging.getLogger(__name__)

class AudioBridgeAPI:
    def __init__(self, host: str, port: int = 23):
        self.host = host
        self.port = port

    async def _send_raw(self, payload: str) -> str:
        """Envia a string devidamente formatada e finalizada em \r\n via Telnet."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=5
            )
            
            # Garantir terminação CRLF conforme exige a especificação[cite: 1]
            cmd_formatted = f"{payload}\r\n".encode("utf-8")
            writer.write(cmd_formatted)
            await writer.drain()

            data = await asyncio.wait_for(reader.read(1024), timeout=5)
            writer.close()
            await writer.wait_closed()

            response = data.decode("utf-8", errors="ignore").strip()
            _LOGGER.debug("Enviado: %s | Recebido: %s", payload, response)
            return response
        except Exception as err:
            _LOGGER.error("Erro de comunicação Telnet com AudioBRIDGE em %s: %s", self.host, err)
            return ""

    async def send_command(self, command: str) -> str:
        """Envia comandos de ação/escrita iniciados por '> '[cite: 1]."""
        return await self._send_raw(f"> {command}")

    async def send_query(self, query: str) -> str:
        """Envia requisições de estado/status iniciadas por '# '[cite: 1]."""
        return await self._send_raw(f"# {query}")

    async def get_model(self) -> str:
        """Consulta o modelo do equipamento via comando de status # 10MODEL ou # 10M[cite: 1]."""
        res = await self.send_query("10M")
        if res:
            return res.replace("<", "").strip()
        return "AudioBRIDGE Unknown"

    async def get_zone_status(self, controller_id: int, zone_id: int) -> dict:
        """Consulta o status completo de uma zona usando # XYST (ex: # 11ST)[cite: 1]."""
        raw_cmd = f"{controller_id}{zone_id}ST"
        res = await self.send_query(raw_cmd)
        
        # O retorno segue o padrão < XYPTAAPRBBMUCCDTDDVOEETRFFBSGGBLHHCHII[cite: 1]
        data = {
            "power": False,
            "mute": False,
            "volume": 0,
            "source": 1
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
                # O volume varia entre 00 e 38[cite: 1]
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
        # Formata para string de 2 dígitos com zero à esquerda (00 a 38)[cite: 1]
        vol_str = f"{vol_level:02d}"
        await self.send_command(f"{controller_id}{zone_id}VO{vol_str}")

    async def set_source(self, controller_id: int, zone_id: int, source_id: int):
        src_str = f"{source_id:02d}"
        await self.send_command(f"{controller_id}{zone_id}CH{src_str}")
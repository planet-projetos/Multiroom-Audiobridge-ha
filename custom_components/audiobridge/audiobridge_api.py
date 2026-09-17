import asyncio
import logging
import re

_LOGGER = logging.getLogger(__name__)

class AudioBridgeAPI:
    def __init__(self, host: str, port: int = 23):
        self.host = host
        self.port = port

    async def _send_command(self, command: str) -> str:
        """Envia comandos Telnet no formato exigido pelo manual."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=5
            )
            
            # Formatação do comando segundo o manual: > COMANDO\r\n
            cmd_formatted = f"> {command}\r\n".encode("utf-8")
            writer.write(cmd_formatted)
            await writer.drain()

            data = await asyncio.wait_for(reader.read(1024), timeout=5)
            writer.close()
            await writer.wait_closed()

            response = data.decode("utf-8", errors="ignore").strip()
            return response
        except Exception as err:
            _LOGGER.error("Erro de comunicação Telnet com AudioBRIDGE em %s: %s", self.host, err)
            return ""

    async def get_model(self) -> str:
        """Consulta o modelo do equipamento via comando > 10X MODEL."""
        res = await self._send_command("10X MODEL")[cite: 1]
        if res:
            return res.replace("<", "").strip()
        return "AudioBRIDGE Unknown"

    async def get_zone_status(self, controller_id: int, zone_id: int) -> dict:
        """Consulta o status completo de uma zona usando # XYST."""
        # Comando de consulta de status: # XYST (ex: # 11ST)
        raw_cmd = f"# {controller_id}{zone_id}ST"[cite: 1]
        res = await self._send_command(raw_cmd)
        
        # O retorno é no formato < XYPTAAPRBBMUCCDTDDVOEETRFFBSGGBLHHCHII[cite: 1]
        # Exemplo: < 11PT00PR01MU00DT01VO15TR07BS07BL10CH01[cite: 1]
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
                # Volume vai de 00 a 38
                data["volume"] = int(vo_match.group(1))

        if "CH" in res:
            ch_match = re.search(r"CH(\d{2})", res)
            if ch_match:
                data["source"] = int(ch_match.group(1))

        return data

    async def set_power(self, controller_id: int, zone_id: int, state: bool):
        val = "01" if state else "00"
        await self._send_command(f"{controller_id}{zone_id}PR{val}")[cite: 1]

    async def set_mute(self, controller_id: int, zone_id: int, state: bool):
        val = "01" if state else "00"
        await self._send_command(f"{controller_id}{zone_id}MU{val}")[cite: 1]

    async def set_volume(self, controller_id: int, zone_id: int, vol_level: int):
        # Transforma para string de 2 dígitos com zero à esquerda (00 a 38)
        vol_str = f"{vol_level:02d}"
        await self._send_command(f"{controller_id}{zone_id}VO{vol_str}")[cite: 1]

    async def set_source(self, controller_id: int, zone_id: int, source_id: int):
        src_str = f"{source_id:02d}"
        await self._send_command(f"{controller_id}{zone_id}CH{src_str}")[cite: 1]
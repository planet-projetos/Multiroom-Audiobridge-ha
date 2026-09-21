import asyncio
import logging
import re

_LOGGER = logging.getLogger(__name__)

class AudioBridgeAPI:
    def __init__(self, host: str, port: int = 23):
        self.host = host
        self.port = port

    async def _send_raw(self, payload: str) -> str:
        """Envia a string formatada e trata a receção de dados via Telnet."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=5
            )
            
            # Envia o comando finalizado com \r\n (CRLF) obrigatório
            cmd_formatted = f"{payload}\r\n".encode("utf-8")
            writer.write(cmd_formatted)
            await writer.drain()

            # Pequena pausa para garantir o processamento na matriz
            await asyncio.sleep(0.1)

            # Primeira leitura de dados do socket TCP
            data = await asyncio.wait_for(reader.read(1024), timeout=5)
            response = data.decode("utf-8", errors="ignore").strip()

            # Trata o banner "Welcome to telnet." enviado pela matriz ao abrir a ligação
            if "Welcome to telnet" in response:
                lines = response.splitlines()
                clean_lines = [l.strip() for l in lines if "Welcome to telnet" not in l and l.strip()]
                
                if clean_lines:
                    response = clean_lines[0]
                else:
                    # Se apenas veio o banner, faz uma segunda leitura para obter a resposta real
                    data = await asyncio.wait_for(reader.read(1024), timeout=5)
                    response = data.decode("utf-8", errors="ignore").strip()

            writer.close()
            await writer.wait_closed()

            _LOGGER.debug("Enviado: %s | Resposta: %s", payload, response)
            return response

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout de ligação Telnet com AudioBRIDGE em %s:%s", self.host, self.port)
            return ""
        except Exception as err:
            _LOGGER.error("Erro na comunicação Telnet com AudioBRIDGE em %s:%s - %s", self.host, self.port, err)
            return ""

    async def send_command(self, command: str) -> str:
        """Envia comandos de ação/escrita iniciados por '> '[cite: 1]."""
        return await self._send_raw(f"> {command}")

    async def send_query(self, query: str) -> str:
        """Envia pedidos de estado/status iniciados por '# '[cite: 1]."""
        return await self._send_raw(f"# {query}")

    async def get_model(self) -> str:
        """Consulta o modelo do equipamento via comando de status # 10M[cite: 1]."""
        res = await self.send_query("10M")[cite: 1]
        if res:
            return res.replace("<", "").strip()
        return "AudioBRIDGE Matrix"

    async def get_zone_status(self, controller_id: int, zone_id: int) -> dict:
        """Consulta o estado completo de uma zona usando # XYST (ex: # 11ST)[cite: 1]."""
        raw_cmd = f"{controller_id}{zone_id}ST"[cite: 1]
        res = await self.send_query(raw_cmd)
        
        data = {
            "power": False,
            "mute": False,
            "volume": 0,
            "source": 1
        }
        
        if "PR" in res:
            pr_match = re.search(r"PR(\d{2})", res)
            if pr_match:
                data["power"] = (pr_match.group(1) == "01")[cite: 1]
        
        if "MU" in res:
            mu_match = re.search(r"MU(\d{2})", res)
            if mu_match:
                data["mute"] = (mu_match.group(1) == "01")[cite: 1]

        if "VO" in res:
            vo_match = re.search(r"VO(\d{2})", res)
            if vo_match:
                data["volume"] = int(vo_match.group(1))[cite: 1]

        if "CH" in res:
            ch_match = re.search(r"CH(\d{2})", res)
            if ch_match:
                data["source"] = int(ch_match.group(1))[cite: 1]

        return data

    async def set_power(self, controller_id: int, zone_id: int, state: bool):
        val = "01" if state else "00"[cite: 1]
        return await self.send_command(f"{controller_id}{zone_id}PR{val}")[cite: 1]

    async def set_mute(self, controller_id: int, zone_id: int, state: bool):
        val = "01" if state else "00"[cite: 1]
        return await self.send_command(f"{controller_id}{zone_id}MU{val}")[cite: 1]

    async def set_volume(self, controller_id: int, zone_id: int, vol_level: int):
        vol_str = f"{vol_level:02d}"[cite: 1]
        return await self.send_command(f"{controller_id}{zone_id}VO{vol_str}")[cite: 1]

    async def set_source(self, controller_id: int, zone_id: int, source_id: int):
        src_str = f"{source_id:02d}"[cite: 1]
        return await self.send_command(f"{controller_id}{zone_id}CH{src_str}")[cite: 1]
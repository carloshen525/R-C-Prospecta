import re
import httpx
from typing import Tuple, Dict, Any, Optional
from app.config import settings
from app.core.exceptions import EvolutionAPIException
from app.core.logging import logger

class EvolutionAPIClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        instance_name: Optional[str] = None,
        db: Optional[Any] = None,
    ):
        if db:
            from app.models.setting import Setting
            try:
                for s in db.query(Setting).all():
                    if s.key == "EVOLUTION_API_URL" and s.value and not base_url:
                        base_url = s.value.strip()
                    elif s.key == "EVOLUTION_API_KEY" and s.value and not api_key:
                        api_key = s.value.strip()
                    elif s.key == "EVOLUTION_INSTANCE_NAME" and s.value and not instance_name:
                        instance_name = s.value.strip()
            except Exception as db_err:
                logger.warning(f"Erro ao carregar settings da Evolution do banco: {db_err}")

        raw_url = (base_url or settings.EVOLUTION_API_URL or "").strip().rstrip("/")
        if raw_url and not raw_url.startswith("http://") and not raw_url.startswith("https://"):
            raw_url = f"https://{raw_url}"
        self.base_url = raw_url
        self.api_key = (api_key or settings.EVOLUTION_API_KEY or "").strip()
        self.instance_name = (instance_name or settings.EVOLUTION_INSTANCE_NAME or "").strip()

    def _get_headers(self) -> Dict[str, str]:
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    def check_connection(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Verifica o estado da conexão e da instância na Evolution API"""
        if not self.base_url:
            return False, "URL do servidor Evolution API não informada.", {}
        if not self.instance_name:
            return False, "Nome da instância não informado.", {}
        if not self.api_key:
            return False, "API Key da Evolution não informada.", {}

        url = f"{self.base_url}/instance/connectionState/{self.instance_name}"
        try:
            with httpx.Client(timeout=12.0, verify=False) as client:
                res = client.get(url, headers=self._get_headers())
                if res.status_code == 200:
                    try:
                        data = res.json()
                    except Exception:
                        data = {"raw": res.text}

                    state = data.get("instance", {}).get("state") or data.get("state") or "unknown"
                    if str(state).lower() in ("open", "connected"):
                        return True, f"Conexão realizada com sucesso! Instância conectada ao WhatsApp (Status: {state}).", data
                    if str(state).lower() in ("close", "closed", "disconnected"):
                        return False, f"Instância encontrada, porém desconectada do WhatsApp (Status: {state}). Abra o painel da Evolution e escaneie o QR Code.", data
                    return False, f"Instância em estado transitório (Status: {state}).", data
                
                if res.status_code in (401, 403):
                    return False, "API Key inválida ou não autorizada pelo servidor da Evolution API.", {}
                if res.status_code == 404:
                    return False, f"Instância '{self.instance_name}' não encontrada no servidor Evolution. Verifique o nome.", {}

                return False, f"Servidor Evolution retornou status {res.status_code}: {res.text[:120]}", {}
        except httpx.ConnectError:
            return False, f"Não foi possível conectar ao servidor Evolution em {self.base_url}. Verifique se a URL está correta.", {}
        except httpx.TimeoutException:
            return False, "Tempo limite esgotado ao tentar comunicar com a Evolution API (Timeout).", {}
        except Exception as e:
            logger.error(f"Erro ao verificar conexão Evolution API: {e}")
            return False, f"Falha de conexão com a Evolution API: {str(e)}", {}

    def send_text_message(self, phone: str, text: str) -> Dict[str, Any]:
        """
        Envia mensagem de texto via WhatsApp usando Evolution API.
        Formata o número conforme exigido pela API.
        """
        if not self.base_url or not self.api_key or not self.instance_name:
            raise EvolutionAPIException("Credenciais da Evolution API não configuradas")

        # Limpa telefone para apenas dígitos (ex: 5516991234567)
        clean_number = re.sub(r"[^\d]", "", phone)
        url = f"{self.base_url}/message/sendText/{self.instance_name}"
        
        payload = {
            "number": clean_number,
            "text": text,
            "options": {
                "delay": 1200,
                "presence": "composing"
            }
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, headers=self._get_headers(), json=payload)
                if res.status_code in (200, 201):
                    return res.json()
                else:
                    err_msg = f"Evolution API erro {res.status_code}: {res.text}"
                    logger.error(err_msg)
                    raise EvolutionAPIException(err_msg)
        except Exception as e:
            logger.error(f"Falha no envio de mensagem Evolution: {e}")
            raise EvolutionAPIException(str(e))

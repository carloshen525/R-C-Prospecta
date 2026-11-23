from typing import Dict, Any, Tuple, Optional
from app.config import settings
from app.services.ai_providers.base import BaseAIProvider
from app.services.ai_providers.openai_provider import OpenAIProvider
from app.services.ai_providers.groq_provider import GroqProvider
from app.services.ai_providers.gemini_provider import GeminiProvider
from app.schemas.sequence import AISequenceGeneratedOutput
from app.core.exceptions import AIProviderException
from app.core.logging import logger

class AIService:
    def __init__(
        self,
        openai_key: Optional[str] = None,
        groq_key: Optional[str] = None,
        gemini_key: Optional[str] = None,
        default_provider: Optional[str] = None,
        fallback_provider: Optional[str] = None,
        db: Optional[Any] = None,
    ):
        openai_model = settings.OPENAI_MODEL
        groq_model = settings.GROQ_MODEL
        gemini_model = settings.GEMINI_MODEL

        if db:
            from app.models.setting import Setting
            try:
                for s in db.query(Setting).all():
                    if s.key == "OPENAI_API_KEY" and s.value and not openai_key:
                        openai_key = s.value.strip()
                    elif s.key == "GROQ_API_KEY" and s.value and not groq_key:
                        groq_key = s.value.strip()
                    elif s.key == "GEMINI_API_KEY" and s.value and not gemini_key:
                        gemini_key = s.value.strip()
                    elif s.key == "DEFAULT_AI_PROVIDER" and s.value and not default_provider:
                        default_provider = s.value.strip()
                    elif s.key == "FALLBACK_AI_PROVIDER" and s.value and not fallback_provider:
                        fallback_provider = s.value.strip()
                    elif s.key == "OPENAI_MODEL" and s.value:
                        openai_model = s.value.strip()
                    elif s.key == "GROQ_MODEL" and s.value:
                        groq_model = s.value.strip()
                    elif s.key == "GEMINI_MODEL" and s.value:
                        gemini_model = s.value.strip()
            except Exception as db_err:
                logger.warning(f"Erro ao carregar settings de IA do banco: {db_err}")

        self.providers: Dict[str, BaseAIProvider] = {}
        
        # Registra adaptadores
        if openai_key or settings.OPENAI_API_KEY:
            self.providers["openai"] = OpenAIProvider(
                api_key=openai_key or settings.OPENAI_API_KEY,
                model=openai_model
            )
        if groq_key or settings.GROQ_API_KEY:
            self.providers["groq"] = GroqProvider(
                api_key=groq_key or settings.GROQ_API_KEY,
                model=groq_model
            )
        if gemini_key or settings.GEMINI_API_KEY:
            self.providers["gemini"] = GeminiProvider(
                api_key=gemini_key or settings.GEMINI_API_KEY,
                model=gemini_model
            )

        self.default_provider_name = (default_provider or settings.DEFAULT_AI_PROVIDER).lower()
        self.fallback_provider_name = (fallback_provider or settings.FALLBACK_AI_PROVIDER).lower()

    def get_provider(self, name: str) -> Optional[BaseAIProvider]:
        return self.providers.get(name.lower())

    def test_provider(self, provider_name: str, api_key: Optional[str] = None) -> Tuple[bool, str]:
        name = provider_name.lower()
        if name == "openai":
            p = OpenAIProvider(api_key=api_key or settings.OPENAI_API_KEY)
            return p.test_connection()
        elif name == "groq":
            p = GroqProvider(api_key=api_key or settings.GROQ_API_KEY)
            return p.test_connection()
        elif name == "gemini":
            p = GeminiProvider(api_key=api_key or settings.GEMINI_API_KEY)
            return p.test_connection()
        else:
            return False, f"Provedor desconhecido: {provider_name}"

    def generate_sequence_with_fallback(
        self,
        prompt: str,
        system_prompt: str,
        preferred_provider: Optional[str] = None
    ) -> Tuple[AISequenceGeneratedOutput, str, str]:
        """
        Executa a geração com fallback automático:
        1. Tenta o provedor preferido.
        2. Se falhar por conectividade/quota, tenta o provedor de fallback.
        3. Valida a estrutura JSON retornada.
        Retorna (output_validado, provedor_utilizado, modelo_utilizado).
        """
        target_name = (preferred_provider or self.default_provider_name).lower()
        provider = self.get_provider(target_name)

        errors_log = []

        if provider:
            try:
                raw_json = provider.generate_json(prompt, system_prompt)
                validated = self._validate_and_heal(raw_json)
                return validated, target_name, getattr(provider, "model", target_name)
            except Exception as e:
                err_msg = f"Falha no provedor principal '{target_name}': {str(e)}"
                logger.warning(err_msg)
                errors_log.append(err_msg)

        # Fallback
        if self.fallback_provider_name and self.fallback_provider_name != target_name:
            fallback_p = self.get_provider(self.fallback_provider_name)
            if fallback_p:
                logger.info(f"Acionando fallback para '{self.fallback_provider_name}'...")
                try:
                    raw_json = fallback_p.generate_json(prompt, system_prompt)
                    validated = self._validate_and_heal(raw_json)
                    return validated, self.fallback_provider_name, getattr(fallback_p, "model", self.fallback_provider_name)
                except Exception as fb_err:
                    err_msg = f"Falha também no provedor de fallback '{self.fallback_provider_name}': {str(fb_err)}"
                    logger.error(err_msg)
                    errors_log.append(err_msg)

        # Se nenhum provedor com chave estiver configurado no momento, lança exceção com detalhes claros
        raise AIProviderException(
            "Nenhum provedor de IA ativo conseguiu concluir a requisição. Erros: " + " | ".join(errors_log)
        )

    def _validate_and_heal(self, raw_json: Any) -> AISequenceGeneratedOutput:
        """Valida que o retorno tem a lista messages com part 1, 2 e 3"""
        if isinstance(raw_json, list):
            raw_json = {"messages": raw_json}
        elif not isinstance(raw_json, dict):
            raise AIProviderException(f"Resposta da IA não é um objeto JSON válido: {raw_json}")

        messages = raw_json.get("messages")
        if not messages or not isinstance(messages, list):
            # Tenta encontrar chave aninhada
            for k, v in raw_json.items():
                if isinstance(v, list) and len(v) >= 3:
                    messages = v
                    break

        if not messages:
            raise AIProviderException(f"Estrutura JSON inválida da IA: 'messages' ausente")

        # Ordena ou formata as 3 mensagens
        formatted_items = []
        for i, item in enumerate(messages[:3]):
            part_num = item.get("part", i + 1)
            msg_text = item.get("message") or item.get("content") or item.get("text") or ""
            if not msg_text or len(msg_text.strip()) < 5:
                raise AIProviderException(f"Mensagem da parte {part_num} vazia ou muito curta")
            formatted_items.append({"part": part_num, "message": msg_text.strip()})

        return AISequenceGeneratedOutput(messages=formatted_items)

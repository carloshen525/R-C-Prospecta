import json
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.models.campaign import Campaign
from app.models.generated_sequence import GeneratedSequence
from app.models.message import Message
from app.services.ai_providers.ai_service import AIService
from app.services.website_analysis.analyzer import WebsiteAnalysisService
from app.core.scheduler_rules import adjust_to_business_hours
from app.core.logging import logger

SYSTEM_PROMPT = """Você é um redator sênior especializado em prospecção comercial B2B via WhatsApp no Brasil.
Seu objetivo é redigir uma sequência personalizada de 3 mensagens curtas, naturais e humanas para estabelecer contato inicial com donos e gestores de empresas.

REGRAS OBRIGATÓRIAS DE LINGUAGEM:
1. Mensagens escritas em português brasileiro coloquial-profissional, como se fossem digitadas no WhatsApp por uma pessoa real chamada Carlos.
2. Seja direto, amigável e conciso (máximo 2 a 4 linhas por mensagem).
3. NUNCA use clichês corporativos como "Prezados", "Espero que este e-mail o encontre bem", "Venho por meio desta", "Alavancar sinergias".
4. NUNCA faça promessas mirabolantes ou garantias irreais de faturamento.
5. NUNCA invente dados ou fale que você conhece o trabalho deles se não tiver certeza.
6. Mencione que encontrou no Google Maps SOMENTE se a fonte informada for 'Google Maps'.

ESTRUTURA DA SEQUÊNCIA (EXATAMENTE 3 PARTES):
- Parte 1 (Atenção):
  Cumprimento simples (ex: "Olá, tudo bem?"), apresentação breve de Carlos, menção sutil ao nome da empresa e que encontrou o contato ao pesquisar empresas da área na cidade.
- Parte 2 (Interesse):
  Apresentar de forma sutil uma dúvida ou dificuldade comum de captação de clientes no segmento específico e fazer uma pergunta simples e aberta (sem afirmar que a empresa tem o problema).
- Parte 3 (Apresentação e Convite):
  Carlos explica brevemente que atua com gestão de anúncios e campanhas no Instagram e Facebook (Meta Ads) para atrair mais clientes qualificados para a região, e convida para uma conversa rápida de cerca de 15 minutos sem compromisso.

FORMATO DE RESPOSTA OBRIGATÓRIO (JSON PURO):
{
  "messages": [
    { "part": 1, "message": "Texto da mensagem 1" },
    { "part": 2, "message": "Texto da mensagem 2" },
    { "part": 3, "message": "Texto da mensagem 3" }
  ]
}
"""

class MessageGeneratorService:
    def __init__(self, db: Session, ai_service: Optional[AIService] = None):
        self.db = db
        self.ai_service = ai_service or AIService(db=db)
        self.website_service = WebsiteAnalysisService()

    def generate_for_lead(self, campaign_id: int, lead_id: int) -> Tuple[GeneratedSequence, List[Message]]:
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not campaign or not lead:
            raise ValueError("Campanha ou Lead não encontrado")

        # 1. Se o lead tiver website e ainda não foi analisado, realiza a análise
        website_context = ""
        if lead.website and not lead.website_data:
            analysis = self.website_service.analyze(lead.website)
            lead.website_data = analysis
            lead.website_analyzed_at = datetime.utcnow()
            self.db.commit()

        if lead.website_data and lead.website_data.get("status") == "success":
            wb = lead.website_data
            website_context = f"\nInformações públicas do site da empresa:\nTítulo: {wb.get('title')}\nSobre: {wb.get('about_summary')}\nServiços destacados: {', '.join(wb.get('main_headings', []))}"

        # 2. Monta o prompt do lead
        prompt = f"""Gere a sequência de 3 mensagens personalizadas para o seguinte estabelecimento:
Empresa: {lead.company_name}
Segmento: {lead.segment or campaign.segment or 'Comércio/Serviços'}
Cidade: {lead.city or campaign.location or 'Brasil'}
Fonte dos dados: {lead.source}
{website_context}

Instruções adicionais da campanha:
{campaign.custom_prompt or 'Nenhuma instrução específica.'}
"""

        # 3. Executa a IA com fallback automático usando o prompt mestre da automação
        from app.models.setting import Setting
        saved_prompt = None
        saved_provider = None
        try:
            for s in self.db.query(Setting).all():
                if s.key == "AUTOMATION_PROMPT" and s.value:
                    saved_prompt = s.value.strip()
                elif s.key == "DEFAULT_AI_PROVIDER" and s.value:
                    saved_provider = s.value.strip()
        except Exception:
            pass

        system_prompt_to_use = saved_prompt or SYSTEM_PROMPT
        preferred_provider = saved_provider or (campaign.ai_provider if campaign else None) or "groq"
        ai_output, provider_used, model_used = self.ai_service.generate_sequence_with_fallback(
            prompt=prompt,
            system_prompt=system_prompt_to_use,
            preferred_provider=preferred_provider
        )

        # 4. Salva o registro da sequência gerada
        sequence = GeneratedSequence(
            campaign_id=campaign.id,
            lead_id=lead.id,
            ai_provider_used=provider_used,
            ai_model_used=model_used,
            raw_ai_response=ai_output.dict(),
            tokens_used=150,
            is_approved=True
        )
        self.db.add(sequence)
        self.db.flush()

        # 5. Cria as 3 mensagens no banco como sequência sequencial
        now = datetime.utcnow()
        messages_created = []

        delay_map = {
            1: timedelta(seconds=0),
            2: timedelta(seconds=12),
            3: timedelta(seconds=28)
        }

        for item in ai_output.messages:
            scheduled_time = now + delay_map.get(item.part, timedelta(hours=24))
            # Ajusta para horário de funcionamento útil (07:00 às 18:30 America/Sao_Paulo)
            adjusted_scheduled_time = adjust_to_business_hours(scheduled_time)

            msg = Message(
                sequence_id=sequence.id,
                campaign_id=campaign.id,
                lead_id=lead.id,
                part_number=item.part,
                original_content=item.message,
                final_content=item.message,
                status="pendente" if item.part == 1 else "pendente",
                scheduled_for=adjusted_scheduled_time.replace(tzinfo=None)
            )
            self.db.add(msg)
            messages_created.append(msg)

        lead.status = "mensagens_geradas"
        self.db.commit()

        return sequence, messages_created

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

SYSTEM_PROMPT = """<quem_voce_e>
Você é Carlos, especialista em anúncios no Instagram e Facebook para clínicas odontológicas e consultórios.
Você escreve de forma humana, natural e autêntica pelo WhatsApp — como um profissional respeitoso que realmente pesquisou e analisou o site e o perfil da clínica antes de mandar mensagem.
</quem_voce_e>

<diretrizes_de_personalizacao_obrigatorias>
NUNCA repita o mesmo texto padronizado ou genérico para clínicas diferentes.
Cada lead deve ter mensagens ÚNICAS e dinâmicas baseadas nos dados reais do seu site e especialidades.

ESTRUTURA DAS 3 MENSAGENS:

1. MENSAGEM 1 (Abertura simples, educada e humana):
- Cumprimento natural (ex: "Olá, tudo bem? Me chamo Carlos...", "Bom dia! Tudo bem por aí? Aqui é o Carlos...").
- Mencione o nome da clínica e que encontrou o contato deles ao pesquisar clínicas odontológicas na cidade.
- Varie a forma de começar para cada lead para soar totalmente espontâneo.

2. MENSAGEM 2 (O Ponto Alto da Personalização - Dor + Especialidade):
- Conecte a dificuldade comercial DIRETAMENTE aos tratamentos em destaque encontrados no site da clínica (ex: se o site destaca Implantes, Alinhadores Invisíveis, Estética Dental, Próteses, Clareamento ou Odontopediatria, cite esses tratamentos de forma natural!).
- Apresente como um desafio do setor (ex: "Muitas clínicas com foco em [especialidade] sentem que o desafio é manter pessoas novas da cidade agendando avaliações particulares de forma constante, sem depender apenas de indicações boca a boca").
- Termine com uma pergunta leve e aberta para estimular conversa (ex: "Como tem sido essa procura por aí hoje?", "Vocês já fazem alguma divulgação específica para atrair esse público?").

3. MENSAGEM 3 (Apresentação do trabalho + Convite leve):
- Explique brevemente que ajuda clínicas a terem visibilidade no Instagram e Facebook para atrair pessoas da região interessadas nesses tratamentos específicos.
- Convide para uma conversa rápida de 10 a 15 minutos sem compromisso.
</diretrizes_de_personalizacao_obrigatorias>

<proibicoes>
- NUNCA use termos técnicos como "gestão de tráfego", "ROI", "leads", "conversão", "funil".
- NUNCA afirme que a clínica está com agenda vazia ou precisando desesperadamente de clientes.
- NUNCA use bajulação ou elogios forçados.
- NUNCA copie e cole o mesmo modelo de mensagem para clínicas diferentes.
</proibicoes>

<formato_de_saida>
Retorne SOMENTE um JSON válido no formato:
{
  "messages": [
    {"part": 1, "message": "texto da mensagem 1"},
    {"part": 2, "message": "texto da mensagem 2"},
    {"part": 3, "message": "texto da mensagem 3"}
  ]
}
</formato_de_saida>"""

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

        # TRAVA DE SEGURANÇA ABSOLUTA CONTRA DUPLICIDADE:
        # Se o lead já foi contatado ou já possui mensagens geradas no banco, NUNCA gere novamente!
        existing_msgs = self.db.query(Message).filter(Message.lead_id == lead.id).order_by(Message.part_number.asc()).all()
        if existing_msgs or lead.status in ("contatado", "bloqueado", "sem_whatsapp", "respondeu", "interessado", "sem_interesse", "nao_contatar"):
            logger.warning(f"[ANTI-DUPLICIDADE] Lead {lead.id} ({lead.company_name}) já possui {len(existing_msgs)} mensagens ou status '{lead.status}'. Geração duplicada bloqueada.")
            existing_seq = self.db.query(GeneratedSequence).filter(GeneratedSequence.lead_id == lead.id).first()
            return existing_seq, existing_msgs

        # 1. Se o lead tiver website e ainda não foi analisado, realiza a análise
        website_context = ""
        specialties_found = []
        if lead.website:
            if not lead.website_data or not lead.website_data.get("detected_specialties"):
                analysis = self.website_service.analyze(lead.website)
                lead.website_data = analysis
                lead.website_analyzed_at = datetime.utcnow()
                self.db.commit()

        if lead.website_data and lead.website_data.get("status") == "success":
            wb = lead.website_data
            specialties_found = wb.get("detected_specialties") or wb.get("services") or wb.get("main_headings") or []
            summary_desc = wb.get("about_summary") or wb.get("meta_description") or wb.get("summary") or ""
            website_context = f"""
INFORMAÇÕES REAIS EXTRAÍDAS DO WEBSITE DA CLÍNICA:
- URL do Site: {wb.get('url')}
- Título do Site: {wb.get('title')}
- Tratamentos / Especialidades em destaque no site: {', '.join(specialties_found[:6])}
- Resumo institucional do site: {summary_desc[:300]}
"""

        # 2. Monta o prompt do lead com diretrizes ativas de personalização
        prompt = f"""Gere uma sequência de 3 mensagens EXCLUSIVA, autêntica e altamente personalizada para este estabelecimento:
Empresa: {lead.company_name}
Segmento: {lead.segment or campaign.segment or 'Clínica Odontológica'}
Cidade: {lead.city or campaign.location or 'Brasil'}
{website_context}

DIRETRIZES DE PERSONALIZAÇÃO OBRIGATÓRIAS:
1. NÃO use frases genéricas prontas. Cada clínica deve receber uma mensagem única e personalizada.
2. Na Mensagem 1: Apresente Carlos pelo nome de forma leve e natural, citando o nome da clínica e um detalhe da cidade ou que estava conhecendo o trabalho deles.
3. Na Mensagem 2: Conecte a dificuldade comercial DIRETAMENTE aos tratamentos em destaque da clínica (ex: {', '.join(specialties_found[:3]) if specialties_found else 'pacientes particulares para tratamentos odontológicos'}), perguntando de forma curiosa e humilde como está a captação de pacientes para essas áreas específicas.
4. Na Mensagem 3: Apresente a atuação com anúncios no Facebook/Instagram como uma forma prática de atrair mais pessoas da cidade interessadas exatamente nessas especialidades, fechando com convite para conversa rápida de 10 a 15 minutos sem compromisso.
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

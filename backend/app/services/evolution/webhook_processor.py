import re
from datetime import datetime
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.webhook_event import WebhookEvent
from app.models.lead import Lead
from app.models.campaign_lead import CampaignLead
from app.models.message import Message
from app.models.conversation import Conversation, ConversationEvent
from app.models.suppression_list import SuppressionList
from app.services.lead_acquisition.lead_service import normalize_phone_e164
from app.core.logging import logger

STOP_KEYWORDS = ["pare", "parar", "sair", "remover", "não quero", "nao quero", "cancelar", "descadastrar", "bloquear", "stop"]

class EvolutionWebhookProcessor:
    def __init__(self, db: Session):
        self.db = db

    def process_event(self, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Processa webhooks da Evolution API com idempotência garantida.
        """
        # 1. Identifica ID do evento para idempotência
        event_type = payload.get("event") or payload.get("type") or "unknown"
        data_block = payload.get("data") or {}
        
        key_block = data_block.get("key") or {}
        message_id = key_block.get("id") or payload.get("messageId") or str(payload.get("timestamp") or "")

        if not message_id:
            # Fallback para timestamp + remoteJid
            remote = key_block.get("remoteJid", "generic")
            message_id = f"evt_{remote}_{int(datetime.utcnow().timestamp())}"

        # Verifica idempotência
        existing_event = self.db.query(WebhookEvent).filter(WebhookEvent.event_id == message_id).first()
        if existing_event:
            logger.info(f"Evento {message_id} já processado anteriormente. Ignorando duplicata.")
            return True, "Evento duplicado já processado"

        # Registra novo evento
        webhook_rec = WebhookEvent(
            event_id=message_id,
            event_type=event_type,
            source="evolution",
            payload=payload,
            processed=False
        )
        self.db.add(webhook_rec)
        self.db.flush()

        try:
            # Tratamento de mensagem recebida
            # Evolution API v1/v2 emite 'messages.upsert' ou 'MESSAGES_UPSERT'
            if event_type.lower() in ("messages.upsert", "messages_upsert"):
                self._handle_incoming_message(data_block, message_id)
            
            # Confirmações de entrega ou atualização de status
            elif event_type.lower() in ("messages.update", "messages_update"):
                self._handle_status_update(data_block)

            webhook_rec.processed = True
            self.db.commit()
            return True, "Processado com sucesso"

        except Exception as e:
            self.db.rollback()
            webhook_rec.error = str(e)
            self.db.commit()
            logger.error(f"Erro ao processar webhook {message_id}: {e}")
            return False, str(e)

    def _handle_incoming_message(self, data: Dict[str, Any], message_id: str):
        key = data.get("key", {})
        from_me = key.get("fromMe", False)
        
        # Ignora mensagens enviadas por nós mesmos
        if from_me:
            return

        remote_jid = key.get("remoteJid", "")
        # Extrai número de telefone (ex: 5516991234567@s.whatsapp.net)
        phone_match = re.match(r"^(\d+)", remote_jid)
        if not phone_match:
            return

        raw_phone = phone_match.group(1)
        normalized_phone = normalize_phone_e164(raw_phone)

        # Extrai o texto da mensagem recebida
        msg_obj = data.get("message", {})
        text = (
            msg_obj.get("conversation") or
            msg_obj.get("extendedTextMessage", {}).get("text") or
            msg_obj.get("imageMessage", {}).get("caption") or
            ""
        ).strip()

        if not text and not normalized_phone:
            return

        # 1. Localiza ou cria o lead pelo telefone
        lead = self.db.query(Lead).filter(Lead.phone == normalized_phone).first()
        if not lead:
            # Tenta buscar pelo final do número (ex: 8 dígitos sem 9 ou sem código)
            tail = raw_phone[-8:]
            lead = self.db.query(Lead).filter(Lead.phone.endswith(tail)).first()

        # 2. Localiza ou cria a conversa
        conversation = None
        if lead:
            conversation = self.db.query(Conversation).filter(Conversation.lead_id == lead.id).first()
            if not conversation:
                conversation = Conversation(
                    lead_id=lead.id,
                    phone=lead.phone or normalized_phone,
                    status="aberta",
                    last_message_at=datetime.utcnow(),
                    unread_count=1
                )
                self.db.add(conversation)
                self.db.flush()
            else:
                conversation.last_message_at = datetime.utcnow()
                conversation.unread_count += 1

            # Cria evento de mensagem recebida
            event = ConversationEvent(
                conversation_id=conversation.id,
                direction="incoming",
                message_content=text,
                evolution_message_id=message_id,
                raw_payload=data,
                status="received"
            )
            self.db.add(event)

            # Verifica palavras-chave de cancelamento / opt-out
            lowered = text.lower()
            wants_stop = any(kw in lowered for kw in STOP_KEYWORDS)

            if wants_stop:
                logger.info(f"Lead {lead.id} ({normalized_phone}) solicitou interrupção: '{text}'")
                lead.status = "nao_contatar"
                lead.is_eligible = False
                # Adiciona na lista de supressão
                supp = self.db.query(SuppressionList).filter(SuppressionList.phone == normalized_phone).first()
                if not supp:
                    self.db.add(SuppressionList(
                        phone=normalized_phone,
                        reason="opt_out",
                        notes=f"Solicitado via WhatsApp: {text[:100]}"
                    ))
            else:
                # Atualiza status para 'respondeu'
                lead.status = "respondeu"

            # 3. CRÍTICO: Cancela automaticamente todos os envios futuros da sequência deste lead
            pending_messages = self.db.query(Message).filter(
                Message.lead_id == lead.id,
                Message.status.in_(["pendente", "na_fila"])
            ).all()

            for pm in pending_messages:
                pm.status = "cancelado"
                pm.error_message = f"Cancelado automaticamente: lead respondeu em {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}"

            # Atualiza status no CampaignLead
            camp_leads = self.db.query(CampaignLead).filter(CampaignLead.lead_id == lead.id).all()
            for cl in camp_leads:
                cl.status = "respondeu" if not wants_stop else "cancelado"

    def _handle_status_update(self, data: Dict[str, Any]):
        key = data.get("key", {})
        message_id = key.get("id")
        status = data.get("status")
        if message_id and status:
            msg = self.db.query(Message).filter(Message.evolution_message_id == message_id).first()
            if msg:
                status_map = {
                    "PENDING": "na_fila",
                    "SERVER_ACK": "enviado",
                    "DELIVERY_ACK": "entregue",
                    "READ": "lido",
                    "PLAYED": "lido",
                    "FAILED": "falhou"
                }
                new_status = status_map.get(str(status).upper(), "enviado")
                msg.status = new_status

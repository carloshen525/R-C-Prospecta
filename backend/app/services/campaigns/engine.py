import random
from datetime import datetime, date, timedelta
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.config import settings
from app.models.campaign import Campaign
from app.models.lead import Lead
from app.models.campaign_lead import CampaignLead
from app.models.message import Message
from app.models.sending_daily_usage import SendingDailyUsage
from app.models.suppression_list import SuppressionList
from app.models.conversation import Conversation, ConversationEvent
from app.services.evolution.client import EvolutionAPIClient
from app.core.scheduler_rules import (
    is_within_sending_window,
    get_now_in_brazil,
    get_next_allowed_window_start
)
from app.core.exceptions import (
    DailyLimitReachedException,
    OutsideSendingWindowException,
    LeadSuppressedException,
    EvolutionAPIException
)
from app.core.logging import logger

class CampaignExecutionEngine:
    def __init__(self, db: Session, evolution_client: Optional[EvolutionAPIClient] = None):
        self.db = db
        self.evolution_client = evolution_client or EvolutionAPIClient(db=self.db)

    def get_or_create_daily_usage(self, target_date: Optional[date] = None) -> SendingDailyUsage:
        """Obtém ou cria o registro atômico de uso diário global"""
        if target_date is None:
            target_date = get_now_in_brazil().date()

        limit_val = settings.DAILY_CONTACT_LIMIT
        try:
            from app.models.setting import Setting
            s_lim = self.db.query(Setting).filter(Setting.key == "DAILY_CONTACT_LIMIT").first()
            if s_lim and s_lim.value:
                limit_val = min(int(s_lim.value), 20)
        except Exception:
            pass

        usage = self.db.query(SendingDailyUsage).filter(SendingDailyUsage.usage_date == target_date).with_for_update().first()
        if not usage:
            usage = SendingDailyUsage(
                usage_date=target_date,
                contacts_sent_count=0,
                limit_max=limit_val,
                is_limit_reached=False
            )
            self.db.add(usage)
            self.db.commit()
            self.db.refresh(usage)
        else:
            if usage.limit_max != limit_val:
                usage.limit_max = limit_val
                usage.is_limit_reached = (usage.contacts_sent_count >= limit_val)
                self.db.commit()
        return usage

    def can_send_contact_today(self, is_new_contact: bool = True, check_window: bool = True) -> Tuple[bool, str]:
        """
        Verifica se é permitido disparar o contato:
        1. Janela de horário (07:00 às 18:30 America/Sao_Paulo), quando check_window=True.
        2. Se for um novo contato único do dia, verifica se não ultrapassou o limite global de 30.
        """
        # 1. Verifica horário
        if check_window:
            window_open, window_msg = is_within_sending_window()
            if not window_open:
                return False, window_msg

        # 2. Se não é novo contato (ex: followup 2 ou 3 do mesmo lead, ou retry), não consome cota diária
        if not is_new_contact:
            return True, "Horário aberto e contato já contabilizado"

        # 3. Verifica limite diário de contatos únicos
        today_date = get_now_in_brazil().date()
        usage = self.get_or_create_daily_usage(today_date)
        if usage.contacts_sent_count >= usage.limit_max:
            usage.is_limit_reached = True
            self.db.commit()
            return False, f"Limite diário global atingido ({usage.contacts_sent_count}/{usage.limit_max} contatos únicos)"

        return True, "Aprovado para envio"

    def increment_daily_usage_if_first_contact(self, lead_id: int) -> bool:
        """
        Incrementa atomicamente a contagem diária se este lead
        estiver recebendo seu primeiro contato de prospecção hoje.
        """
        today_date = get_now_in_brazil().date()
        
        # Verifica se o lead já recebeu alguma mensagem hoje
        start_of_day = datetime.combine(today_date, datetime.min.time())
        already_sent_today = self.db.query(Message).filter(
            Message.lead_id == lead_id,
            Message.sent_at >= start_of_day,
            Message.status.in_(["enviado", "entregue", "lido"])
        ).first()

        if already_sent_today:
            # Já contabilizado hoje
            return False

        usage = self.get_or_create_daily_usage(today_date)
        if usage.contacts_sent_count >= usage.limit_max:
            usage.is_limit_reached = True
            self.db.commit()
            raise DailyLimitReachedException(f"Limite diário de {usage.limit_max} contatos atingido")

        usage.contacts_sent_count += 1
        if usage.contacts_sent_count >= usage.limit_max:
            usage.is_limit_reached = True
        self.db.commit()
        return True

    def send_lead_sequence(self, lead_id: int, campaign_id: int) -> List[Dict[str, Any]]:
        """
        Envia a sequência completa de mensagens (Partes 1, 2 e 3) para o mesmo lead
        com intervalos naturais de digitação (8 a 14 segundos entre balões).
        """
        import time

        messages = self.db.query(Message).filter(
            Message.lead_id == lead_id,
            Message.campaign_id == campaign_id,
            Message.status.in_(["pendente", "na_fila"])
        ).order_by(Message.part_number.asc()).all()

        results = []
        for i, msg in enumerate(messages):
            if i > 0:
                time.sleep(random.uniform(8.0, 14.0))

            res = self.send_single_message(msg.id)
            results.append(res)

            if res.get("status") in ("error", "failed"):
                # Cancela próximas partes caso uma falhe
                for remaining in messages[i+1:]:
                    remaining.status = "cancelado"
                    remaining.error_message = f"Cancelado: parte {msg.part_number} falhou no envio"
                self.db.commit()
                break

        return results

    def dispatch_next_batch(self, max_messages: int = 5) -> List[Dict[str, Any]]:
        """
        Processa mensagens prontas para envio da fila.
        Dispara a sequência completa (3 mensagens) para cada lead elegível.
        Funciona 24/7 via Celery Beat, respeitando horários e dias configurados.
        """
        # 0. Verifica se a automação está Pausada
        from app.models.setting import Setting
        status_setting = self.db.query(Setting).filter(Setting.key == "AUTOMATION_STATUS").first()
        if status_setting and status_setting.value and status_setting.value.lower() == "pausada":
            logger.info("Motor de prospecção: automação está PAUSADA pelo usuário.")
            return []

        # 1. Verifica se a janela de horário e dia permitido está aberta
        window_open, window_msg = is_within_sending_window(db=self.db)
        if not window_open:
            logger.info(f"Engine de prospecção em pausa de horário: {window_msg}")
            return []

        now_utc = datetime.utcnow()

        # 2. Verifica se o intervalo mínimo entre LEADS DIFERENTES está sendo respeitado
        # Só bloqueia se houve um lead enviado com sucesso recentemente
        try:
            from app.models.setting import Setting
            s_int = self.db.query(Setting).filter(Setting.key == "MIN_INTERVAL_BETWEEN_CONTACTS_SEC").first()
            min_interval = int(s_int.value) if s_int and s_int.value else 180
        except Exception:
            min_interval = 180

        last_sent_msg = self.db.query(Message).filter(
            Message.status == "enviado",
            Message.sent_at.isnot(None)
        ).order_by(Message.sent_at.desc()).first()

        if last_sent_msg and last_sent_msg.sent_at:
            elapsed = (now_utc - last_sent_msg.sent_at).total_seconds()
            if elapsed < min_interval:
                wait_sec = int(min_interval - elapsed)
                logger.info(f"Aguardando delay de segurança entre leads: {wait_sec}s restantes (mínimo de {min_interval}s configurado).")
                return []

        # 3. Busca mensagens de Partes pendentes agendadas
        pending_first_msgs = self.db.query(Message).join(Campaign).join(Lead).filter(
            Campaign.status == "ativa",
            Lead.status.notin_(["nao_contatar", "respondeu", "interessado", "sem_interesse", "sem_whatsapp"]),
            Lead.is_eligible == True,
            Message.status.in_(["pendente", "na_fila"]),
            Message.part_number == 1,
            Message.scheduled_for <= now_utc
        ).order_by(Message.scheduled_for.asc()).limit(max_messages).all()

        results = []
        for fmsg in pending_first_msgs:
            seq_results = self.send_lead_sequence(lead_id=fmsg.lead_id, campaign_id=fmsg.campaign_id)
            results.extend(seq_results)
            # Se o lead foi enviado com sucesso, encerra o lote para aguardar o intervalo do próximo
            if seq_results and any(r.get("status") == "success" for r in seq_results):
                break

        # 4. Se não há mensagens prontas na fila, busca novos leads aguardando processamento
        # Se um lead falhar ou não tiver WhatsApp, pula IMEDIATAMENTE para o próximo da fila!
        if not results:
            from app.api.v1.endpoints.automation import get_or_create_system_campaign
            system_camp = get_or_create_system_campaign(self.db)

            max_consecutive_skips = 10
            while max_consecutive_skips > 0:
                max_consecutive_skips -= 1

                waiting_lead = self.db.query(Lead).filter(
                    Lead.status.in_(["novo", "aguardando"]),
                    Lead.is_eligible == True,
                    Lead.phone.isnot(None)
                ).order_by(Lead.created_at.asc()).first()

                if not waiting_lead:
                    break

                from app.services.message_generator.generator import MessageGeneratorService
                from app.services.ai_providers.ai_service import AIService
                ai_service = AIService(db=self.db)
                generator = MessageGeneratorService(db=self.db, ai_service=ai_service)
                try:
                    generator.generate_for_lead(campaign_id=system_camp.id, lead_id=waiting_lead.id)
                    seq_res = self.send_lead_sequence(lead_id=waiting_lead.id, campaign_id=system_camp.id)
                    results.extend(seq_res)

                    has_success = seq_res and any(r.get("status") == "success" for r in seq_res)
                    if has_success:
                        # Lead contatado com sucesso! Respeita o intervalo antes do próximo
                        logger.info(f"Lead {waiting_lead.company_name} contatado com sucesso via WhatsApp!")
                        break
                    else:
                        # Falhou (ex: telefone fixo ou sem whatsapp) -> pula IMEDIATAMENTE para o próximo
                        logger.info(f"Lead {waiting_lead.company_name} não possui WhatsApp ou falhou. Pulando imediatamente para o próximo da fila!")
                        continue

                except Exception as gen_err:
                    logger.error(f"Erro ao processar lead {waiting_lead.id}: {gen_err}")
                    waiting_lead.status = "erro"
                    self.db.commit()

        return results

    def send_single_message(self, message_id: int) -> Dict[str, Any]:
        """
        Executa todas as validações transacionais e realiza o envio seguro via Evolution API.
        """
        msg = self.db.query(Message).filter(Message.id == message_id).with_for_update().first()
        if not msg:
            return {"status": "error", "message": "Mensagem não encontrada"}

        if msg.status in ("enviado", "entregue", "lido", "cancelado"):
            return {"status": "skipped", "message": f"Mensagem já em status {msg.status}"}

        lead = self.db.query(Lead).filter(Lead.id == msg.lead_id).first()
        campaign = self.db.query(Campaign).filter(Campaign.id == msg.campaign_id).first()

        if not lead or not campaign:
            msg.status = "falhou"
            msg.error_message = "Lead ou Campanha não encontrados"
            self.db.commit()
            return {"status": "failed", "error": msg.error_message}

        # 1. Verifica se a campanha está ativa
        if campaign.status != "ativa":
            return {"status": "skipped", "message": f"Campanha {campaign.name} não está ativa ({campaign.status})"}

        # 2. Verifica se o lead não respondeu nem está na lista de supressão
        if lead.status in ("respondeu", "interessado", "sem_interesse", "nao_contatar"):
            msg.status = "cancelado"
            msg.error_message = f"Envio cancelado pois o lead está em status '{lead.status}'"
            self.db.commit()
            return {"status": "cancelled", "reason": msg.error_message}

        suppressed = self.db.query(SuppressionList).filter(SuppressionList.phone == lead.phone).first()
        if suppressed:
            msg.status = "cancelado"
            msg.error_message = f"Lead está na lista de supressão: {suppressed.reason}"
            lead.status = "nao_contatar"
            lead.is_eligible = False
            self.db.commit()
            return {"status": "cancelled", "reason": msg.error_message}

        # 3. Verifica se o envio anterior da sequência (se houver) foi enviado com sucesso
        if msg.part_number > 1:
            prev_msg = self.db.query(Message).filter(
                Message.sequence_id == msg.sequence_id,
                Message.part_number == msg.part_number - 1
            ).first()
            if not prev_msg or prev_msg.status not in ("enviado", "entregue", "lido"):
                return {"status": "skipped", "message": f"Aguardando envio da parte {msg.part_number - 1}"}

        # 4. Verifica regra de limite e janela de horário
        is_first_contact = (msg.part_number == 1)
        can_send, reason = self.can_send_contact_today(is_new_contact=is_first_contact)
        if not can_send:
            logger.info(f"Envio da mensagem {msg.id} postergado: {reason}")
            # Se for por limite diário ou janela fechada, reajusta para a próxima janela
            next_window = get_next_allowed_window_start()
            msg.scheduled_for = next_window.replace(tzinfo=None)
            self.db.commit()
            return {"status": "postponed", "reason": reason, "rescheduled_for": str(msg.scheduled_for)}

        # 5. Se for o primeiro contato, valida se ainda há cota diária disponível
        if is_first_contact:
            can_send_contact, reason_contact = self.can_send_contact_today(is_new_contact=True)
            if not can_send_contact:
                next_window = get_next_allowed_window_start()
                msg.scheduled_for = next_window.replace(tzinfo=None)
                self.db.commit()
                return {"status": "postponed", "reason": reason_contact}

        # 6. Dispara via Evolution API
        try:
            res_evo = self.evolution_client.send_text_message(
                phone=lead.phone,
                text=msg.final_content
            )

            # Se o primeiro contato foi enviado com sucesso, agora sim consome a cota diária
            if is_first_contact:
                try:
                    self.increment_daily_usage_if_first_contact(lead.id)
                except Exception as usage_err:
                    logger.warning(f"Aviso ao contabilizar uso diário: {usage_err}")

            # Extrai ID da mensagem da resposta da Evolution
            evo_id = (
                res_evo.get("key", {}).get("id") or
                res_evo.get("messageId") or
                res_evo.get("id")
            )
            msg.evolution_message_id = evo_id
            msg.status = "enviado"
            msg.sent_at = datetime.utcnow()
            msg.error_message = None

            # Atualiza status do lead e campaign_lead
            if lead.status == "mensagens_geradas" or lead.status == "novo":
                lead.status = "contatado"

            cl = self.db.query(CampaignLead).filter(
                CampaignLead.campaign_id == campaign.id,
                CampaignLead.lead_id == lead.id
            ).first()
            if cl:
                cl.status = "enviado"

            # Registra na conversa
            conv = self.db.query(Conversation).filter(Conversation.lead_id == lead.id).first()
            if not conv:
                conv = Conversation(
                    lead_id=lead.id,
                    phone=lead.phone,
                    status="aberta",
                    last_message_at=datetime.utcnow(),
                    unread_count=0
                )
                self.db.add(conv)
                self.db.flush()
            else:
                conv.last_message_at = datetime.utcnow()

            event = ConversationEvent(
                conversation_id=conv.id,
                direction="outgoing",
                message_content=msg.final_content,
                evolution_message_id=evo_id,
                raw_payload=res_evo,
                status="sent"
            )
            self.db.add(event)
            self.db.commit()

            return {
                "status": "success",
                "message_id": msg.id,
                "lead_id": lead.id,
                "part": msg.part_number,
                "evolution_message_id": evo_id
            }

        except Exception as e:
            self.db.rollback()
            try:
                fresh_msg = self.db.query(Message).filter(Message.id == message_id).first()
                if fresh_msg:
                    fresh_msg.status = "falhou"
                    fresh_msg.error_message = str(e)
                    # Se o erro indicar que o número não possui WhatsApp, marca lead como sem_whatsapp
                    err_str = str(e).lower()
                    if "exists\":false" in err_str or "not registered" in err_str:
                        fresh_lead = self.db.query(Lead).filter(Lead.id == fresh_msg.lead_id).first()
                        if fresh_lead:
                            fresh_lead.status = "sem_whatsapp"
                            fresh_lead.is_eligible = False
                    self.db.commit()
            except Exception as inner_err:
                logger.error(f"Erro ao salvar status de falha: {inner_err}")
            logger.error(f"Erro ao enviar mensagem {message_id}: {e}")
            return {"status": "error", "error": str(e)}

import csv
import io
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.lead import Lead
from app.models.campaign import Campaign
from app.models.campaign_lead import CampaignLead
from app.models.message import Message
from app.models.generated_sequence import GeneratedSequence
from app.models.conversation import Conversation
from app.schemas.report import (
    ReportsSummary,
    PerformanceByCampaign,
    PerformanceBySegment,
    PerformanceByAIProvider
)

router = APIRouter()

@router.get("", response_model=ReportsSummary)
def get_reports_summary(db: Session = Depends(get_db)):
    total_extracted = db.query(Lead).count()
    total_eligible = db.query(Lead).filter(Lead.is_eligible == True).count()
    total_contacts_sent = db.query(Lead).filter(Lead.status.in_(["contatado", "respondeu", "interessado", "sem_interesse"])).count()
    total_messages = db.query(Message).filter(Message.status.in_(["enviado", "entregue", "lido"])).count()
    total_responses = db.query(Lead).filter(Lead.status.in_(["respondeu", "interessado", "sem_interesse"])).count()
    total_interested = db.query(Lead).filter(Lead.status == "interessado").count()
    total_errors = db.query(Message).filter(Message.status == "falhou").count()

    response_rate = round((total_responses / total_contacts_sent * 100), 2) if total_contacts_sent > 0 else 0.0
    interest_rate = round((total_interested / total_responses * 100), 2) if total_responses > 0 else 0.0

    # Campanhas
    campaigns_data = []
    campaigns = db.query(Campaign).all()
    for c in campaigns:
        leads_count = db.query(CampaignLead).filter(CampaignLead.campaign_id == c.id).count()
        sent_count = db.query(Message).filter(Message.campaign_id == c.id, Message.status.in_(["enviado", "entregue", "lido"])).count()
        reply_count = db.query(CampaignLead).filter(CampaignLead.campaign_id == c.id, CampaignLead.status == "respondeu").count()
        rep_rate = round((reply_count / leads_count * 100), 2) if leads_count > 0 else 0.0
        
        inter_count = db.query(CampaignLead).join(Lead).filter(CampaignLead.campaign_id == c.id, Lead.status == "interessado").count()
        inter_rate = round((inter_count / reply_count * 100), 2) if reply_count > 0 else 0.0

        campaigns_data.append(PerformanceByCampaign(
            campaign_name=c.name,
            leads_count=leads_count,
            sent_count=sent_count,
            reply_count=reply_count,
            reply_rate=rep_rate,
            interested_count=inter_count,
            interested_rate=inter_rate
        ))

    # Segmentos
    segments_data = []
    segment_rows = db.query(Lead.segment, func.count(Lead.id)).filter(Lead.segment != None).group_by(Lead.segment).all()
    for seg, count in segment_rows:
        sent_c = db.query(Lead).filter(Lead.segment == seg, Lead.status.in_(["contatado", "respondeu", "interessado"])).count()
        rep_c = db.query(Lead).filter(Lead.segment == seg, Lead.status.in_(["respondeu", "interessado"])).count()
        r_rate = round((rep_c / sent_c * 100), 2) if sent_c > 0 else 0.0

        segments_data.append(PerformanceBySegment(
            segment=seg or "Geral",
            leads_count=count,
            sent_count=sent_c,
            reply_count=rep_c,
            reply_rate=r_rate
        ))

    # Provedores IA
    ai_data = []
    for prov in ["openai", "groq", "gemini"]:
        seq_count = db.query(GeneratedSequence).filter(GeneratedSequence.ai_provider_used == prov).count()
        if seq_count > 0:
            rep_count = db.query(GeneratedSequence).join(Lead).filter(
                GeneratedSequence.ai_provider_used == prov,
                Lead.status.in_(["respondeu", "interessado"])
            ).count()
            r_rate = round((rep_count / seq_count * 100), 2) if seq_count > 0 else 0.0
            ai_data.append(PerformanceByAIProvider(
                ai_provider=prov.upper(),
                sequences_generated=seq_count,
                reply_count=rep_count,
                reply_rate=r_rate
            ))

    return ReportsSummary(
        total_extracted=total_extracted,
        total_eligible=total_eligible,
        total_contacts_sent=total_contacts_sent,
        total_messages=total_messages,
        total_responses=total_responses,
        total_interested=total_interested,
        response_rate=response_rate,
        interest_rate=interest_rate,
        total_errors=total_errors,
        campaigns=campaigns_data,
        segments=segments_data,
        ai_providers=ai_data
    )

@router.get("/export-csv")
def export_leads_csv(db: Session = Depends(get_db)):
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow([
        "ID", "Empresa", "Telefone", "Cidade", "Estado", "Segmento",
        "Website", "Avaliação", "Status", "Elegível", "Data Cadastro"
    ])

    leads = db.query(Lead).order_by(Lead.id.desc()).all()
    for l in leads:
        writer.writerow([
            l.id,
            l.company_name,
            l.phone or "",
            l.city or "",
            l.state or "",
            l.segment or "",
            l.website or "",
            l.rating or "",
            l.status,
            "Sim" if l.is_eligible else "Não",
            l.created_at.strftime("%d/%m/%Y %H:%M")
        ])

    return Response(
        content=output.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=prospect_ai_leads_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv"}
    )

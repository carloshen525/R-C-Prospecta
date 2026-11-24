from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.extraction_job import ExtractionJob
from app.schemas.extraction import ExtractionJobCreate, ExtractionJobResponse, ExtractionImportRequest
from app.services.lead_acquisition.lead_service import LeadAcquisitionService
from app.core.logging import logger

router = APIRouter()

def execute_job_in_background(job_id: int):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        service = LeadAcquisitionService(db=db)
        service.execute_extraction(job_id)
    except Exception as e:
        logger.error(f"Erro no background job de extração {job_id}: {e}")
    finally:
        db.close()

@router.post("", response_model=ExtractionJobResponse)
def create_extraction_job(
    job_in: ExtractionJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    job = ExtractionJob(
        segment=job_in.segment,
        city=job_in.city,
        state=job_in.state,
        country=job_in.country,
        desired_qty=job_in.desired_qty,
        has_phone_filter=job_in.has_phone_filter,
        has_website_filter=job_in.has_website_filter,
        source=job_in.source or "google_scraper",
        auto_import=job_in.auto_import or False,
        campaign_id=job_in.campaign_id,
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Tenta despachar para o Celery; se Celery não estiver rodando no host local, usa BackgroundTasks
    try:
        from app.tasks.extraction_tasks import run_extraction_job
        run_extraction_job.delay(job.id)
    except Exception as celery_err:
        logger.warning(f"Celery não disponível para dispatch imediato ({celery_err}). Usando FastAPI BackgroundTasks.")
        background_tasks.add_task(execute_job_in_background, job.id)

    return job

def _auto_recover_job_if_possible(job: ExtractionJob, db: Session):
    """Auto-recupera jobs que concluíram a busca mas tiveram queda de conexão no momento do commit"""
    if job and job.status == "failed" and job.error_log and "'status': 'completed'" in job.error_log and not job.extracted_items:
        try:
            import re, ast
            m = re.search(r"'extracted_items':\s*Json\((\[.*?\])\)", job.error_log, re.DOTALL)
            if m:
                items = ast.literal_eval(m.group(1))
                job.extracted_items = items
                job.found_count = len(items)
                job.processed_count = len(items)
                job.status = "completed"
                job.error_log = None
                db.commit()
                db.refresh(job)
        except Exception as rec_err:
            logger.debug(f"Falha na auto-recuperação do job {job.id}: {rec_err}")

@router.get("", response_model=List[ExtractionJobResponse])
def list_extraction_jobs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    jobs = db.query(ExtractionJob).order_by(ExtractionJob.created_at.desc()).offset(skip).limit(limit).all()
    for j in jobs:
        _auto_recover_job_if_possible(j, db)
    return jobs

@router.get("/{job_id}", response_model=ExtractionJobResponse)
def get_extraction_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Tarefa de extração não encontrada")
    _auto_recover_job_if_possible(job, db)
    return job

@router.post("/{job_id}/import")
def import_selected_leads(
    job_id: int,
    req: ExtractionImportRequest,
    db: Session = Depends(get_db)
):
    """Importa seletivamente os estabelecimentos aprovados pelo usuário para a tabela de leads e campanhas"""
    service = LeadAcquisitionService(db=db)
    try:
        res = service.import_selected_leads(
            job_id=job_id,
            selected_indices=req.selected_indices,
            campaign_id=req.campaign_id
        )
        return {
            "success": True,
            "imported_count": res["imported_count"],
            "total_saved": res["total_saved"],
            "message": f"{res['imported_count']} leads importados com sucesso para a base!"
        }
    except Exception as e:
        logger.error(f"Erro ao importar leads do job {job_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

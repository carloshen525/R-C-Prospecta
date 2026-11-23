from app.celery_app import celery
from app.database import SessionLocal
from app.services.lead_acquisition.lead_service import LeadAcquisitionService
from app.core.logging import logger

@celery.task(name="app.tasks.extraction_tasks.run_extraction_job", bind=True)
def run_extraction_job(self, job_id: int):
    logger.info(f"Iniciando Celery task de extração para job_id={job_id}")
    db = SessionLocal()
    try:
        service = LeadAcquisitionService(db=db)
        job = service.execute_extraction(job_id)
        logger.info(f"Extração concluída para job {job_id}: {job.saved_count} salvos, {job.duplicate_count} duplicados.")
        return {
            "job_id": job.id,
            "status": job.status,
            "saved_count": job.saved_count,
            "duplicate_count": job.duplicate_count
        }
    except Exception as e:
        logger.error(f"Erro na Celery task de extração: {e}")
        raise
    finally:
        db.close()

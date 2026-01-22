from celery import shared_task
from django.conf import settings
import os
from .models import CommercialProposal
import logging
from core.services.exchange_rate_service import ExchangeRateService
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

@shared_task
def generate_pdf_task(template_id):
    """Generates PDF for a given ProposalTemplate."""
    from .models import ProposalTemplate
    from .services import ExportService
    from weasyprint import HTML
    import uuid
    
    try:
        template = ProposalTemplate.objects.get(pk=template_id)
        service = ExportService(template)
        html_content = service.generate_pdf_html()
        
        # Generate filename
        safe_number = str(template.proposal.outcoming_number).replace('/', '_').replace(' ', '_')
        filename = f"proposal_{safe_number}_{uuid.uuid4().hex[:8]}.pdf"
        save_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)
        
        # Actually generate PDF
        HTML(string=html_content, base_url=str(settings.BASE_DIR)).write_pdf(filepath)
        
        url = f"{settings.MEDIA_URL}exports/{filename}"
        return {'status': 'SUCCESS', 'url': url}
        
    except Exception as e:
        logger.error(f"PDF generation failed for template {template_id}: {e}", exc_info=True)
        import traceback
        return {'status': 'FAILURE', 'error': str(e), 'trace': traceback.format_exc()}

@shared_task
def generate_docx_task(template_id):
    """Generates DOCX for a given ProposalTemplate."""
    from .models import ProposalTemplate
    from .services import ExportService
    import uuid
    import io
    
    try:
        template = ProposalTemplate.objects.get(pk=template_id)
        service = ExportService(template)
        stream = service.generate_docx()
        
        # Generate filename
        safe_number = str(template.proposal.outcoming_number).replace('/', '_').replace(' ', '_')
        filename = f"proposal_{safe_number}_{uuid.uuid4().hex[:8]}.docx"
        save_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(stream.getbuffer())
        
        url = f"{settings.MEDIA_URL}exports/{filename}"
        return {'status': 'SUCCESS', 'url': url}
        
    except Exception as e:
        logger.error(f"DOCX generation failed for template {template_id}: {e}", exc_info=True)
        import traceback
        return {'status': 'FAILURE', 'error': str(e), 'trace': traceback.format_exc()}


@shared_task
def sync_exchange_rates_task():
    """
    Sync exchange rates from NBK and prune old entries (older than 31 days).
    Runs via Celery Beat.
    """
    stats = ExchangeRateService.fetch_and_sync_rates()
    deleted = ExchangeRateService.prune_old_rates(days=31)
    logger.info(f"Exchange rates sync: {stats}, pruned: {deleted}")
    return {'stats': stats, 'pruned': deleted}

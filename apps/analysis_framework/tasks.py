import logging

from celery import shared_task
from django.utils import timezone

from utils.common import redis_lock, get_temp_file
from utils.files import generate_file_for_upload

from .models import AnalysisFramework
from analysis_framework.export import export_af_to_csv

logger = logging.getLogger(__name__)


@shared_task
@redis_lock('af_export__{0}')
def export_af_to_csv_task(af_id):
    try:
        af = AnalysisFramework.objects.get(id=af_id)
        with get_temp_file(suffix='.csv', mode='w+') as file:
            export_af_to_csv(af, file)
            time_str = timezone.now().strftime('%Y-%m-%d%z')
            file.seek(0)
            af.export.save(
                f'AF_Export_{af.id}_{time_str}.csv',
                generate_file_for_upload(file),
            )
    except Exception:
        logger.error(f'Failed to export AF: {af_id}', exc_info=True)
        return False
    return True

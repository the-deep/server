from django.db.models import Q
from django.conf import settings

from utils.common import parse_number

from lead.models import LeadPreviewImage
from entry.models import Entry
from gallery.models import File

"""
python3 manage.py bulk_migrate entry_images_v2
"""

FILE_API_PREFIX = '{protocol}://{domain}{url}'.format(
    protocol=settings.HTTP_PROTOCOL,
    domain=settings.DJANGO_API_HOST,
    url='/file/',
)
S3_URL_PREFIX = f'https://{settings.AWS_STORAGE_BUCKET_NAME_MEDIA}.s3.amazonaws.com/{settings.MEDIAFILES_LOCATION}/'


def _get_file_from_file_url(entry, string):
    try:
        fileid = parse_number(string.rstrip('/').split('/')[-1])
    except IndexError:
        return
    return fileid and File.objects.filter(id=fileid).first()


def _get_file_from_s3_url(entry, string):
    try:
        file_path = '/'.join(string.split('?')[0].split('/')[4:])
    except IndexError:
        return
    # NOTE: For lead-preview generate gallery files
    if file_path.startswith('lead-preview/'):
        lead_preview = LeadPreviewImage.objects.filter(file=file_path).first()
        if lead_preview and lead_preview.file.storage.exists(lead_preview.file):
            return lead_preview.clone_as_deep_file(entry.created_by)
        return
    return file_path and File.objects.filter(file=file_path).first()


def migrate_entry(entry):
    """
    Migrate to deep gallery image from s3 and file api URL.
    """
    image_raw = entry.image_raw
    file = None

    if image_raw.find(FILE_API_PREFIX) == 0:
        file = _get_file_from_file_url(entry, image_raw)
    elif image_raw.find(S3_URL_PREFIX) == 0:
        file = _get_file_from_s3_url(entry, image_raw)

    if file:
        entry.image = file
        entry.save()
        return True


def migrate(*args, **kwargs):
    qs = Entry.objects.filter(
        Q(image_raw__isnull=False),
        ~Q(image_raw=''),
        image__isnull=True,
    )
    total = qs.count()
    success = 0
    index = 1
    print('File string saved:', qs.filter(image_raw__startswith=FILE_API_PREFIX).count())
    print('S3 string saved (lead images):', qs.filter(image_raw__startswith=S3_URL_PREFIX).count())

    for entry in qs.iterator():
        print(f'Processing {index} of {total}', end='\r')
        if migrate_entry(entry):
            success += 1
        index += 1
    print('Summary:')
    print(f'\t-Total: {total}')
    success and print(f'\t-Success: {success}')
    (total - success) and print(f'\t-Failed: {total - success}')

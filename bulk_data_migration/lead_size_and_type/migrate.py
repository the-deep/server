from utils.extractor.file_document import FileDocument
from utils.extractor.web_document import WebDocument
from lead.models import Lead


def update_lead(lead):
    # if lead.size_in_bytes or lead.mime_type:
    #     return

    size = None
    mime_type = None
    if lead.text:
        size = len(lead.text)
    elif lead.attachment:
        fd = FileDocument(
            lead.attachment.file,
            lead.attachment.file.name,
        )
        size = lead.attachment.file.size
        mime_type = fd.mime_type or lead.attachment.mime_type
    elif lead.url:
        wd = WebDocument(lead.url)
        size = wd.size
        mime_type = wd.mime_type

    Lead.objects.filter(id=lead.id).update(
        size_in_bytes=size,
        mime_type=mime_type,
    )


def migrate():
    leads = Lead.objects.all()
    total_count = leads.count()
    for i, lead in enumerate(leads):
        print('Updating lead {} out of {}'.format(i + 1, total_count))
        update_lead(lead)

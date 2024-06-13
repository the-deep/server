from entry.models import Attribute, EntryAttachment
from gallery.models import File
from lead.models import LeadPreviewAttachment
from utils.image import decode_base64_if_possible

from .widgets.utils import set_filter_data, set_export_data
from .widgets.store import widget_store


def update_entry_attribute(attribute):
    entry = attribute.entry
    widget = attribute.widget
    data = attribute.data or {}
    if not entry or not widget:
        return

    widget_module = widget_store.get(widget.widget_id)
    if widget_module:
        update_info = widget_module.update_attribute(
            widget,
            data,
            widget.properties or {},
        )

        filter_data_list = update_info.get('filter_data')
        export_data = update_info.get('export_data')

        if filter_data_list:
            for filter_data in filter_data_list:
                set_filter_data(
                    entry,
                    widget,
                    **filter_data,
                )

        if export_data:
            set_export_data(
                entry,
                widget,
                **export_data,
            )


def update_attributes(**attr_filters):
    attributes = Attribute.objects.filter(**attr_filters)

    for attribute in attributes:
        update_entry_attribute(attribute)


def base64_to_deep_image(image, lead, user):
    if not image:
        return

    decoded_file, header = decode_base64_if_possible(image)
    if isinstance(decoded_file, str):
        return image

    mime_type = ''
    if header:
        mime_type = header[len('data:'):]

    file = File.objects.create(
        title=decoded_file.name,
        mime_type=mime_type,
        created_by=user,
        modified_by=user,
    )
    file.file.save(decoded_file.name, decoded_file)
    file.projects.add(lead.project)
    return file


def leadattachment_to_entryattachment(lead_attachment: LeadPreviewAttachment):
    lead_attachment_file_name = str(lead_attachment.file).split('/')[-1]
    lead_attachment_file_preview_name = str(lead_attachment.file_preview).split('/')[-1]
    entry_attachment = EntryAttachment.objects.create(
        lead_attachment_id=lead_attachment.id,
        entry_file_type=lead_attachment.type  # lead attachement type and entry attachment gave same enum
    )
    if lead_attachment.type == LeadPreviewAttachment.AttachmentFileType.IMAGE:
        entry_attachment.file.save(
            lead_attachment_file_name,
            lead_attachment.file,
        )
        entry_attachment.file_preview = entry_attachment.file
    else:
        entry_attachment.file.save(
            lead_attachment_file_name,
            lead_attachment.file
        )
        entry_attachment.file_preview.save(
            lead_attachment_file_preview_name,
            lead_attachment.file_preview
        )
    entry_attachment.save()
    return entry_attachment

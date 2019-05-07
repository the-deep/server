# DEEP GALLERY CONFIGS ###
# List of mime types supported in deep
# NOTE: also change in frontend

PDF_MIME_TYPES = ['application/pdf']
DOCX_MIME_TYPES = [
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/wps-office.docx',
]
MSWORD_MIME_TYPES = [
    'application/msword', 'application/wps-office.doc',
]
POWERPOINT_MIME_TYPES = [
    'application/vnd.openxmlformats-officedocument.presentationml.presentation', # noqa
    'application/vnd.ms-powerpoint',
]
SHEET_MIME_TYPES = [
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
]
ODS_MIME_TYPES = ['application/vnd.oasis.opendocument.spreadsheet']
IMAGE_MIME_TYPES = ['image/png', 'image/jpeg', 'image/fig', 'image/gif']

CHART_IMAGE_MIME = {
    'png': 'image/png',
    'svg': 'image/svg+xml',
}

# Overall Supported Mime Types
DEEP_SUPPORTED_MIME_TYPES = [
    'application/rtf', 'text/plain', 'font/otf', 'text/csv',
    'application/json', 'application/xml',
] + (
    DOCX_MIME_TYPES + MSWORD_MIME_TYPES + PDF_MIME_TYPES +
    POWERPOINT_MIME_TYPES + SHEET_MIME_TYPES + ODS_MIME_TYPES +
    IMAGE_MIME_TYPES
)

DEEP_SUPPORTED_EXTENSIONS = [
    'docx', 'xlsx', 'pdf', 'pptx',
    'json', 'png', 'jpg', 'jpeg', 'csv', 'txt',
    'geojson', 'zip', 'ods', 'doc',
]

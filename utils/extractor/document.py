from utils.extractor import extractors

HTML = 'html'
PDF = 'pdf'
DOCX = 'docx'
PPTX = 'pptx'

EXTRACTORS = {
    HTML: extractors.HtmlExtractor,
    PDF: extractors.PdfExtractor,
    DOCX: extractors.DocxExtractor,
    PPTX: extractors.PptxExtractor,
}

MIME_TYPES = {
    HTML: 'text/html',
    PDF: 'application/pdf',
    DOCX: 'application/vnd.openxmlformats-officedocument'
          '.wordprocessingml.document',
    PPTX: 'application/vnd.openxmlformats-officedocument'
          '.presentationml.presentation',
}


class Document:
    """
    A wrapper for document

    Helps extract any type of file
    """
    def __init__(self, doc, type, mime_type=None):
        self.type = type
        self.doc = doc
        self.mime_type = mime_type or MIME_TYPES[type]

    def extract(self):
        """
        Extracts text and images from the document

        Returns a tuple of text as string and images as list
        """
        extractor = EXTRACTORS.get(self.type)
        if extractor:
            return {
                'mime_type': self.mime_type,
                **extractor(self.doc).extract(),
            }
        return {
            'text': '',
            'images': [],
            'mime_type': self.mime_type,
        }

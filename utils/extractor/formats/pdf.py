from io import BytesIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager, resolve1
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser


def process(doc):
    fp = doc
    fp.seek(0)

    with BytesIO() as retstr:
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        with TextConverter(
            rsrcmgr,
            retstr,
            codec="utf-8",
            laparams=laparams,
        ) as device:
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            maxpages = 0
            caching = True
            pagenos = set()
            for page in PDFPage.get_pages(
                fp,
                pagenos,
                maxpages=maxpages,
                caching=caching,
                check_extractable=True,
            ):
                interpreter.process_page(page)
            content = retstr.getvalue().decode()
    pages_count = get_pages_in_pdf(doc)
    return content, None, pages_count


def get_pages_in_pdf(file):
    document = PDFDocument(PDFParser(file))
    return resolve1(document.catalog["Pages"])["Count"]

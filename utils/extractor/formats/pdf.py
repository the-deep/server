from io import BytesIO
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage


def process(doc):
    fp = doc
    fp.seek(0)

    with BytesIO() as retstr:
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        with TextConverter(
                rsrcmgr, retstr, codec='utf-8', laparams=laparams,
        ) as device:
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            maxpages = 0
            caching = True
            pagenos = set()
            for page in PDFPage.get_pages(
                    fp, pagenos, maxpages=maxpages,
                    caching=caching, check_extractable=True,
            ):
                interpreter.process_page(page)
            content = retstr.getvalue().decode()
    return content, None

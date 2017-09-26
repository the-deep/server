from pdfminer.converter import TextConverter  # , HTMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, process_pdf
import tempfile


def process(doc):
    fp = doc
    fp.seek(0)
    outfp = tempfile.TemporaryFile("w+", encoding='utf-8')

    rmgr = PDFResourceManager()
    params = LAParams()
    device = TextConverter(rmgr, outfp, laparams=params)
    process_pdf(rmgr, device, fp, None, 0)

    fp.close()

    outfp.seek(0)
    content = outfp.read()
    outfp.close()

    return content, None

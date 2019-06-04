import random
import os
import re
import string
from django.conf import settings
from subprocess import call

from utils.common import LogTime

from .xlsx import extract as xlsx_extract


@LogTime()
def extract(book):
    tmp_filepath = '/tmp/{}'.format(
        ''.join(random.sample(string.ascii_lowercase, 10)) + '.xls'
    )

    with open(tmp_filepath, 'wb') as tmpxls:
        tmpxls.write(book.file.file.read())
        tmpxls.flush()

    call([
        'libreoffice', '--headless', '--convert-to', 'xlsx',
        tmp_filepath, '--outdir', settings.TEMP_DIR,
    ])

    xlsx_filename = os.path.join(
        settings.TEMP_DIR,
        re.sub(r'xls$', 'xlsx', os.path.basename(tmp_filepath))
    )

    response = xlsx_extract(book, filename=xlsx_filename)

    # Clean up converted xlsx file
    call(['rm', '-f', xlsx_filename, tmp_filepath])
    return response

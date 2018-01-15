from readability.readability import Document
import re
import requests
import tempfile
from lxml.html import fragment_fromstring

from django.conf import settings

from utils.common import write_file


def process(doc):
    html_body = Document(doc)
    summary = html_body.summary()
    title = html_body.short_title()
    images = []

    for img in html_body.reverse_tags(html_body.html, 'img'):
        try:
            fp = tempfile.NamedTemporaryFile(dir=settings.BASE_DIR,
                                             delete=False)
            r = requests.get(img.get('src'), stream=True)
            write_file(r, fp)
            images.append(fp)
        except Exception:
            pass

    html = '<h1>' + title + '</h1>' + summary

    regex = re.compile('\n*', flags=re.IGNORECASE)
    html = '<div>{}</div>'.format(regex.sub('', html))

    text = '\n'.join(fragment_fromstring(html).itertext()).strip()
    return text, images

from readability.readability import Document
import re
import requests
import tempfile

from django.conf import settings

from utils.common import write_file


def process(doc):
    html_body = Document(doc)
    summary = html_body.summary()
    title = html_body.short_title()
    images = []

    for img in html_body.reverse_tags(html_body.html, 'img'):
        try:
            fp = tempfile.NamedTemporaryFile(dir=settings.BASE_DIR)
            r = requests.get(img.get('src'), stream=True)
            write_file(r, fp)
            images.append(fp)
        except:
            pass

    html = "<h1>" + title + "</h1>" + summary

    regex = re.compile('\n*', flags=re.IGNORECASE)
    html = regex.sub('', html)
    return html, images

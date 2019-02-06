from readability.readability import Document
from urllib.parse import urljoin

import logging
import traceback
import re
import requests
import tempfile
import base64
from bs4 import BeautifulSoup

from django.conf import settings

from utils.common import write_file

logger = logging.getLogger(__name__)


def _replace_with_newlines(element):
    text = ''
    for elem in element.recursiveChildGenerator():
        if isinstance(elem, str):
            text += elem.strip()
        elif elem.name == 'br':
            text += '\n\n'
    return text.strip()


def _get_plain_text(soup):
    plain_text = ''
    for line in soup.findAll('p'):
        line = _replace_with_newlines(line)
        plain_text += line
        plain_text += '\n\n'
    return plain_text.strip()


def process(doc, url):
    html_body = Document(doc)
    summary = html_body.summary()
    title = html_body.short_title()
    images = []

    for img in html_body.reverse_tags(html_body.html, 'img'):
        try:
            fp = tempfile.NamedTemporaryFile(dir=settings.BASE_DIR)
            img_src = urljoin(url, img.get('src'))
            if re.search(r'http[s]?://', img_src):
                r = requests.get(img_src, stream=True)
                write_file(r, fp)
            else:
                image = base64.b64decode(img_src.split(',')[1])
                fp.write(image)
            images.append(fp)
        except Exception:
            logger.error(traceback.format_exc())

    html = '<h1>' + title + '</h1>' + summary

    regex = re.compile('\n*', flags=re.IGNORECASE)
    html = '<p>{}</p>'.format(regex.sub('', html))

    soup = BeautifulSoup(html, 'lxml')
    text = _get_plain_text(soup)
    return text, images, 1

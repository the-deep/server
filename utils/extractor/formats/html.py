import re
import requests
import tempfile
import os

from bs4 import BeautifulSoup
from readability.readability import Document

from django.conf import settings
from utils.common import write_file


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
        except Exception:
            pass

    html = '<h1>' + title + '</h1>' + summary

    regex = re.compile('\n*', flags=re.IGNORECASE)
    html = '<p>{}</p>'.format(regex.sub('', html))

    soup = BeautifulSoup(html, 'lxml')
    text = _get_plain_text(soup)

    return {
        'text': text,
        'images': images,
        'size': len(doc),
    }

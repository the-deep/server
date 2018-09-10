from xml.sax.saxutils import escape
from datetime import timedelta

import os
import time
import random
import string


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)' + \
    ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'

DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
}


def write_file(r, fp):
    for chunk in r.iter_content(chunk_size=1024):
        if chunk:
            fp.write(chunk)
    return fp


def get_or_write_file(path, text):
    try:
        extracted = open(path, 'r')
    except FileNotFoundError:
        with open(path, 'w') as fp:
            fp.write(text)
        extracted = open(path, 'r')
    return extracted


def makedirs(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass


def is_valid_xml_char_ordinal(c):
    codepoint = ord(c)
    # conditions ordered by presumed frequency
    return (
        0x20 <= codepoint <= 0xD7FF or
        codepoint in (0x9, 0xA, 0xD) or
        0xE000 <= codepoint <= 0xFFFD or
        0x10000 <= codepoint <= 0x10FFFF
    )


def get_valid_xml_string(string):
    if string:
        s = escape(string)
        return ''.join(c for c in s
                       if is_valid_xml_char_ordinal(c))
    return ''


def format_date(date):
    if date:
        return date.strftime('%d-%m-%Y')
    else:
        return None


def generate_filename(title, extension):
    return '{} DEEP {}.{}'.format(
        time.strftime('%Y%m%d'),
        title,
        extension,
    )


def generate_timeseries(entities, min_date, max_date):
    entities = entities.order_by('created_at')
    timeseries = []

    oldest_date = min_date
    latest_date = max_date

    current_date = oldest_date
    while current_date <= latest_date:
        subset = entities.filter(
            created_at__date=current_date
        )
        current_date = current_date + timedelta(days=1)
        timeseries.append({
            'date': current_date,
            'count': subset.count()
        })

    return timeseries


def identity(x):
    return x


def underscore_to_title(x):
    return ' '.join([y.title() for y in x.split('_')])


def random_key(length=16):
    candidates = string.ascii_lowercase + string.digits
    winners = [random.choice(candidates) for _ in range(length)]
    return ''.join(winners)

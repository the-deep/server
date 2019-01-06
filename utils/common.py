from xml.sax.saxutils import escape
from datetime import timedelta, datetime
from django.conf import settings

from collections import Counter
from functools import reduce
import os
import time
import random
import string
import tempfile
import requests

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


def get_file_from_url(url):
    file = tempfile.NamedTemporaryFile(dir=settings.BASE_DIR)
    response = requests.get(url, stream=True, headers=DEFAULT_HEADERS)
    response.raise_for_status()
    write_file(response, file)
    file.seek(0)
    return file


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
    return date and date.strftime('%d-%m-%Y')


def parse_date(date_str):
    return date_str and datetime.strptime(date_str, '%d-%m-%Y')


def parse_time(time_str):
    return time_str and datetime.strptime(time_str, '%H:%M').time()


def parse_number(num_str):
    if not num_str:
        return None
    num = float(num_str)
    if num == round(num):
        return int(num)
    return num


def generate_filename(title, extension):
    return '{} DEEP {}.{}'.format(
        time.strftime('%Y%m%d'),
        title,
        extension,
    )


def generate_timeseries(data, min_date, max_date):
    timeseries = []
    data_map = {datum['date']: datum['count'] for datum in data}

    oldest_date = min_date
    latest_date = max_date

    current_date = oldest_date
    while current_date <= latest_date:
        timeseries.append({
            'date': current_date,
            'count': data_map.get(current_date.date(), 0)
        })
        current_date = current_date + timedelta(days=1)
    return timeseries


def identity(x):
    return x


def underscore_to_title(x):
    return ' '.join([y.title() for y in x.split('_')])


def random_key(length=16):
    candidates = string.ascii_lowercase + string.digits
    winners = [random.choice(candidates) for _ in range(length)]
    return ''.join(winners)


def get_max_occurence_and_count(items):
    """Return: (max_occuring_item, count)"""
    if not items:
        return 0, None
    count = Counter(items)
    return reduce(
        lambda a, x: x if x[1] > a[1] else a,
        count.items(),  # [(item, count)...]
        (items[0], -1)  # Initial accumulator
    )


def excel_column_name(column_number):
    """
    Returns columns name corresponding to column number
    Example: 1 -> A, 27 -> AA, 28 -> AB
    NOTE: column_number is 1 indexed
    """
    col_num = column_number - 1  # For modulus operation

    if column_number < 27:
        return chr(65 + col_num)

    q = int(col_num / 26)
    r = col_num % 26

    return excel_column_name(q) + chr(65 + r)

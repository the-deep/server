# -*- coding: utf-8 -*-
import hashlib
from xml.sax.saxutils import escape as xml_escape
import matplotlib as mp
from datetime import timedelta, datetime
from django.conf import settings
from redis_store import redis

import plotly.io as pio
import plotly.graph_objs as ploty_go
from collections import Counter
from functools import reduce
import os
import re
import time
import random
import string
import tempfile
import requests
import logging

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)' + \
    ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'

DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
}

logger = logging.getLogger(__name__)


def is_valid_regex(string):
    try:
        re.compile(string)
        return True
    except re.error:
        return False


def write_file(r, fp):
    for chunk in r.iter_content(chunk_size=1024):
        if chunk:
            fp.write(chunk)
    return fp


def get_temp_file(dir='/tmp/', suffix=None):
    if suffix:
        return tempfile.NamedTemporaryFile(dir=dir, suffix=suffix)
    return tempfile.NamedTemporaryFile(dir=dir)


def get_file_from_url(url):
    file = tempfile.NamedTemporaryFile(dir=settings.TEMP_DIR)
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


def replace_ns(nsmap, tag):
    for k, v in nsmap.items():
        k = k or ''
        tag = tag.replace('{{{}}}'.format(v), '{}:'.format(k))
    return tag


def get_ns_tag(nsmap, tag):
    for k, v in nsmap.items():
        k = k or ''
        tag = tag.replace('{}:'.format(k), '{{{}}}'.format(v))
    return tag


def is_valid_xml_char_ordinal(c):
    codepoint = ord(c)
    # conditions ordered by presumed frequency
    return (
        0x20 <= codepoint <= 0xD7FF or
        codepoint in (0x9, 0xA, 0xD) or
        0xE000 <= codepoint <= 0xFFFD or
        0x10000 <= codepoint <= 0x10FFFF
    )


def get_valid_xml_string(string, escape=True):
    if string:
        s = xml_escape(string) if escape else string
        return ''.join(c for c in s
                       if is_valid_xml_char_ordinal(c))
    return ''


def format_date(date):
    return date and date.strftime('%d-%m-%Y')


def parse_date(date_str):
    try:
        return date_str and datetime.strptime(date_str, '%d-%m-%Y')
    except ValueError:
        return None


def parse_time(time_str):
    try:
        return time_str and datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        return None


def parse_number(num_str):
    try:
        num = float(num_str)
    except (ValueError, TypeError):
        return None
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


class LogTime:
    logger = logging.getLogger('profiling')

    def __init__(
            self, block_name='', log_args=True,
            args_accessor=identity, kwargs_accessor=identity
    ):
        self.log_args = log_args
        self.block_name = block_name
        self.args_accessor = args_accessor
        self.kwargs_accessor = kwargs_accessor

    def __enter__(self):
        if settings.PROFILE:
            self.start = time.time()

    def __exit__(self, *args, **kwds):
        if not settings.PROFILE:
            return
        end = time.time()
        LogTime.logger.info("BLOCK: {} TIME {}s.".format(
            self.block_name, end - self.start))

    def __call__(self, func_to_be_tracked):
        def wrapper(*args, **kwargs):
            if not settings.PROFILE:
                return func_to_be_tracked(*args, **kwargs)

            start = time.time()
            ret = func_to_be_tracked(*args, **kwargs)
            end = time.time()

            fname = func_to_be_tracked.__name__

            str_args = 'args: {}'.format(
                self.args_accessor(args)
            )[:100] if self.log_args else ''

            str_kwargs = 'kwargs: {}'.format(
                self.kwargs_accessor(kwargs)
            )[:100] if self.log_args else ''

            log_message = "FUNCTION[{}]: '{}({}, {})' : TIME {}s.".format(
                self.block_name, fname, str_args, str_kwargs, end - start)

            LogTime.logger.info(log_message)

            return ret
        wrapper.__name__ = func_to_be_tracked.__name__
        wrapper.__module__ = func_to_be_tracked.__module__
        return wrapper


confidence_z_map = {
    80: 1.28,
    85: 1.44,
    90: 1.65,
    95: 1.96,
    99: 2.58,
}


def calculate_sample_size(pop_size, confidence_percent=90, prob=0.8):
    z = confidence_z_map.get(confidence_percent, 1.5)
    e = 0.05  # Error Interval
    z_p_pmin1 = z * z * prob * (1 - prob)
    z_by_e_sq = z_p_pmin1 / e**2
    return z_by_e_sq / (1 + z_by_e_sq / pop_size)


def create_plot_image(func):
    """
    Return tmp file image with func render logic
    """
    def func_wrapper(*args, **kwargs):
        size = kwargs.pop('chart_size', (8, 4))
        if isinstance(kwargs.get('format', 'png'), list):
            images_format = kwargs.pop('format')
        else:
            images_format = [kwargs.pop('format', 'png')]
        func(*args, **kwargs)
        figure = mp.pyplot.gcf()

        if size:
            figure.set_size_inches(size)
        mp.pyplot.draw()
        mp.pyplot.gca().spines['top'].set_visible(False)
        mp.pyplot.gca().spines['right'].set_visible(False)
        images = []
        for image_format in images_format:
            fp = get_temp_file(suffix='.{}'.format(image_format))
            figure.savefig(fp, bbox_inches='tight', format=image_format, alpha=True, dpi=300)
            mp.pyplot.close(figure)
            fp.seek(0)
            images.append({'image': fp, 'format': image_format})
        return images
    return func_wrapper


def create_plotly_image(func):
    """
    Return tmp file image with func render logic
    """
    def func_wrapper(*args, **kwargs):
        width, height = kwargs.pop('chart_size', (5, 4))
        if isinstance(kwargs.get('format', 'png'), list):
            images_format = kwargs.pop('format', 'png')
        else:
            images_format = [kwargs.pop('format', 'png')]
        x_label = kwargs.pop('x_label')
        y_label = kwargs.pop('y_label')
        x_params = kwargs.pop('x_params', {})
        y_params = kwargs.pop('y_params', {})
        data, layout = func(*args, **kwargs)
        if layout is None:
            layout = ploty_go.Layout(**{
                'title': x_label,
                'yaxis': {
                    **create_plotly_image.axis_config,
                    **y_params,
                    'title': y_label,
                },
                'xaxis': {
                    **create_plotly_image.axis_config,
                    **x_params,
                    'ticks': 'outside',
                },
            })
        fig = ploty_go.Figure(data=data, layout=layout)
        images = []
        for image_format in images_format:
            img_bytes = pio.to_image(fig, format=image_format, width=width, height=height, scale=2)
            fp = get_temp_file(suffix='.{}'.format(image_format))
            fp.write(img_bytes)
            fp.seek(0)
            images.append({'image': fp, 'format': image_format})
        return images
    return func_wrapper


create_plotly_image.axis_config = {
    'automargin': True,
    'tickfont': dict(size=8),
    'separatethousands': True,
}
create_plotly_image.marker = dict(
    color='teal',
    line=dict(
        color='white',
        width=0.5,
    )
)


def get_redis_lock_ttl(lock):
    try:
        return timedelta(seconds=redis.get_connection().ttl(lock.name))
    except Exception:
        pass


def redis_lock(lock_key, timeout=60 * 60 * 4):
    """
    Default Lock lifetime 4 hours
    """
    def _dec(func):
        def _caller(*args, **kwargs):
            key = lock_key.format(*args, **kwargs)
            lock = redis.get_lock(key, timeout)
            have_lock = lock.acquire(blocking=False)
            if not have_lock:
                logger.warning(f'Unable to get lock for {key}(ttl: {get_redis_lock_ttl(lock)})')
                return False
            try:
                return_value = func(*args, **kwargs) or True
            except Exception:
                logger.error('{}.{}'.format(func.__module__, func.__name__), exc_info=True)
                return_value = False
            lock.release()
            return return_value
        _caller.__name__ = func.__name__
        _caller.__module__ = func.__module__
        return _caller
    return _dec


def make_colormap(seq):
    """Return a LinearSegmentedColormap
    seq: a sequence of floats and RGB-tuples. The floats should be increasing
    and in the interval (0,1).
    """
    seq = [(None,) * 3, 0.0] + list(seq) + [1.0, (None,) * 3]
    cdict = {'red': [], 'green': [], 'blue': []}
    for i, item in enumerate(seq):
        if isinstance(item, float):
            r1, g1, b1 = seq[i - 1]
            r2, g2, b2 = seq[i + 1]
            cdict['red'].append([item, r1, r2])
            cdict['green'].append([item, g1, g2])
            cdict['blue'].append([item, b1, b2])
    return mp.colors.LinearSegmentedColormap('CustomMap', cdict)


def excel_to_python_date_format(excel_format):
    # TODO: support all formats
    # First replace excel's locale identifiers such as [$-409] by empty string
    python_format = re.sub('(\[\\$-\d+\])', '', excel_format.upper()).\
        replace('\\', '').\
        replace('YYYY', '%Y').\
        replace('YY', '%y').\
        replace('MMMM', '%m').\
        replace('MMM', '%m').\
        replace('MM', '%m').\
        replace('M', '%m').\
        replace('DD', '%d').\
        replace('D', '%d').\
        replace('HH', '%H').\
        replace('H', '%H').\
        replace('SS', '%S')
    return python_format


def format_date_or_iso(date, format):
    try:
        return date.strftime(format)
    except Exception:
        return date.date().isoformat()


def combine_dicts(list_dicts):
    combined = {}
    for x in list_dicts:
        combined.update(x)
    return combined


def calculate_md5(file):
    file.seek(0)
    hash_md5 = hashlib.md5()
    while True:
        chunk = file.read(4096)
        if not chunk:
            break
        hash_md5.update(chunk)
    return hash_md5.hexdigest()


def camelcase_to_titlecase(label):
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', label)


def kebabcase_to_titlecase(kebab_str):
    return ' '.join([x.title() for x in kebab_str.split('-')])


def is_valid_number(value):
    # Value can be string/number. Check if value represents a number
    try:
        int(value)
    except (TypeError, ValueError):
        return False

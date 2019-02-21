from xml.sax.saxutils import escape
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
from django.conf import settings
from redis_store import redis

from collections import Counter
from functools import reduce
import matplotlib.colors as mcolors
import os
import time
import random
import string
import tempfile
import requests
import logging
import traceback

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)' + \
    ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'

DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
}

logger = logging.getLogger(__name__)


def write_file(r, fp):
    for chunk in r.iter_content(chunk_size=1024):
        if chunk:
            fp.write(chunk)
    return fp


def get_temp_file(dir='/tmp/'):
    return tempfile.NamedTemporaryFile(dir=dir)


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
        func(*args, **kwargs)
        figure = plt.gcf()
        if size:
            figure.set_size_inches(size)
        plt.draw()
        fp = get_temp_file()
        figure.savefig(fp, bbox_inches='tight', alpha=True, dpi=300)
        plt.close(figure)
        return fp
    return func_wrapper


def redis_lock(func):
    def func_wrapper(*args, **kwargs):
        key = '{}::{}'.format(
            func.__name__,
            '__'.join([str(arg) for arg in args]),
        )
        lock = redis.get_lock(key, 60 * 60 * 24)  # Lock lifetime 24 hours
        have_lock = lock.acquire(blocking=False)
        if not have_lock:
            return False
        try:
            return_value = func(*args, **kwargs) or True
        except Exception:
            logger.error(
                '********** {} **********\n{}'.format(
                    func.__name__,
                    traceback.format_exc(),
                ),
            )
            return_value = False
        lock.release()
        return return_value
    func_wrapper.__name__ = func.__name__
    return func_wrapper


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
    return mcolors.LinearSegmentedColormap('CustomMap', cdict)

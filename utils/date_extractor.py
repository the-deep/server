from dateutil.parser import parse
import re


def str_to_date(string):
    try:
        return parse(string)
    except Exception:
        return None


# Simple url check, though very less chance of working
def _extract_from_url(url):
    regex = r'([\./\-_]{0,1}(19|20)\d{2})[\./\-_]{0,1}(([0-3]{0,1}[0-9][\./\-_])|(\w{3,5}[\./\-_]))([0-3]{0,1}[0-9][\./\-]{0,1})?' # noqa
    m = re.search(regex, url)
    if m:
        return str_to_date(m.group(0))
    return None


# Some common meta names and properties that may denote date
DATE_META_NAMES = [
    'date',
    'pubdate',
    'publishdate',
    'timestamp',
    'dc.date.issued',
    'sailthru.date',
    'article.published',
    'published-date',
    'article.created',
    'article_date_original',
    'cxenseparse:recs:publishtime',
    'date_published',
    'datepublished',
    'datecreated',
    'article:published_time',
    'bt:pubdate',
]


def _extract_from_meta(page):
    meta_date = None
    for meta in page.findAll('meta'):
        meta_name = meta.get('name', '').lower()
        item_prop = meta.get('itemprop', '').lower()
        meta_property = meta.get('property', '').lower()
        http_equiv = meta.get('http-equiv', '').lower()

        if (
                meta_name in DATE_META_NAMES or
                item_prop in DATE_META_NAMES or
                meta_property in DATE_META_NAMES or
                http_equiv == 'date'
        ):
            meta_date = str_to_date(meta['content'].strip())
            break

    return meta_date


# From https://github.com/Webhose/article-date-extractor
# Most probably can be optimized
def _extract_from_tags(page):
    for time in page.findAll('time'):
        datetime = time.get('datetime', '')
        if len(datetime) > 0:
            return str_to_date(datetime)

        datetime = time.get('class', '')
        if len(datetime) > 0 and datetime[0].lower() == 'timestamp':
            return str_to_date(time.string)

    tag = page.find('span', {'itemprop': 'datePublished'})
    if tag is not None:
        date_text = tag.get('content')
        if date_text is None:
            date_text = tag.text

        if date_text:
            return str_to_date(date_text)

    regex = 'pubdate|timestamp|article_date|articledate|date'
    for tag in page.find_all(['span', 'p', 'div'],
                             class_=re.compile(regex, re.IGNORECASE)):
        date_text = tag.string
        if date_text is None:
            date_text = tag.text

        possible_date = str_to_date(date_text)
        if possible_date:
            return possible_date

    return None


def extract_date(url, page):
    """
    Extract date from given url and given page data
    where the page is a BeautifulSoup object
    """
    if not page:
        date = _extract_from_url(url)
    else:
        date = _extract_from_meta(page)
        if date is None:
            date = _extract_from_tags(page)
        if date is None:
            date = _extract_from_url(url)

    return date and date.date()

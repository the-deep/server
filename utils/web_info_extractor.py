from bs4 import BeautifulSoup
from readability.readability import Document
from urllib.parse import urlparse
from .date_extractor import extract_date

import requests
import tldextract


class WebInfoExtractor:
    def __init__(self, url):
        self.url = url

        html = requests.get(url).text
        self.readable = Document(html)
        self.page = BeautifulSoup(html, 'lxml')

    def get_title(self):
        return self.readable.short_title()

    def get_date(self):
        return extract_date(self.url, self.page)

    def get_country(self):
        country = self.page.select('.primary-country .country a')
        if country:
            return country[0].text.strip()

        country = self.page.select('.country')
        if country:
            return country[0].text.strip()

        return None

    def get_source(self):
        source = self.page.select('.field-source')
        if source:
            return source[0].text.strip()

        return tldextract.extract(self.url).domain

    def get_website(self):
        return urlparse(self.url).netloc

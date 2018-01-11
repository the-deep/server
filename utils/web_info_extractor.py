from bs4 import BeautifulSoup
from urllib.parse import urlparse

import articleDateExtractor
import requests
import tldextract


class WebInfoExtractor:
    def __init__(self, url):
        self.url = url

        html = requests.get(url).text
        self.page = BeautifulSoup(html, 'lxml')

    def get_date(self):
        return articleDateExtractor.extractArticlePublishedDate(
            self.url
        )

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

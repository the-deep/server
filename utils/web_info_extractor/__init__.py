from urllib.parse import urlparse

from .default import DefaultWebInfoExtractor
from .redhum import RedhumWebInfoExtractor


EXTRACTORS = {
    'redhum.org': RedhumWebInfoExtractor,
}


def get_web_info_extractor(url):
    website = urlparse(url).netloc
    return EXTRACTORS.get(website, DefaultWebInfoExtractor)(url)

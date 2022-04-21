from unified_connector.models import ConnectorSource
from .relief_web_mock_data import (
    RELIEF_WEB_MOCK_DATA_PAGE_1_RAW,
    RELIEF_WEB_MOCK_DATA_PAGE_2_RAW,
    RELIEF_WEB_MOCK_EXCEPTED_LEADS
)
from .unhcr_mock_data import (
    UNHCR_MOCK_DATA_PAGE_1_RAW,
    UNHCR_MOCK_DATA_PAGE_2_RAW,
    UNHCR_WEB_MOCK_EXCEPTED_LEADS
)

CONNECTOR_SOURCE_MOCK_DATA = {
    ConnectorSource.Source.UNHCR: (
        (UNHCR_MOCK_DATA_PAGE_1_RAW, UNHCR_MOCK_DATA_PAGE_2_RAW), UNHCR_WEB_MOCK_EXCEPTED_LEADS
    ),
    ConnectorSource.Source.RELIEF_WEB: (
        (RELIEF_WEB_MOCK_DATA_PAGE_1_RAW, RELIEF_WEB_MOCK_DATA_PAGE_2_RAW), RELIEF_WEB_MOCK_EXCEPTED_LEADS
    ),
}


class ConnectorSourceResponseMock():
    def __init__(self, source_type):
        self.raw_pages_data, self.expected_data = CONNECTOR_SOURCE_MOCK_DATA[source_type]
        self.page = -1

    def get_content_side_effect(self, url, params):
        # NOTE: We aren't checking connector_mock_data length
        # here since it should be configured properly in the raw data.
        # Preventing to go to another page
        self.page += 1
        return self.raw_pages_data[self.page]

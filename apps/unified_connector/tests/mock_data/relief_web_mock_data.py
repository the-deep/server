import datetime

RELIEF_WEB_MOCK_DATA_PAGE_1_RAW = """
    {
      "time": 11,
      "href": "https://api.reliefweb.int/v1/reports?appname=thedeep.io",
      "links": {
          "self": {
              "href": "https://api.reliefweb.int/v1/reports?appname=thedeep.io"
          },
          "next": {
              "href": "https://api.reliefweb.int/v1/reports?offset=10&limit=10"
          }
      },
      "took": 4,
      "totalCount": 4,
      "count": 10,
      "data": [
        {
          "id": "3670885",
          "fields": {
            "date": { "original": "2020-09-17T00:00:00+00:00" },
            "url_alias": "https://reliefweb.int/report/nepal/nepal-makes-progress-human-capital-development",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/1220",
                "longname": "The World Bank Group",
                "spanish_name": "Banco Mundial",
                "name": "World Bank",
                "id": 1220,
                "type": { "name": "International Organization", "id": 272 },
                "shortname": "World Bank",
                "homepage": "http://www.worldbank.org"
              }
            ],
            "title": "Nepal makes progress in human capital development"
          },
          "href": "https://api.reliefweb.int/v1/reports/3670885"
        },
        {
          "id": "3670541",
          "fields": {
            "date": { "original": "2020-09-16T00:00:00+00:00" },
            "file": [
              {
                "filename": "roap_covid_response_sitrep_18.pdf",
                "description": "",
                "mimetype": "application/pdf",
                "id": "1535625",
                "filesize": "1684789",
                "url": "https://reliefweb.int/sites/reliefweb.int/files/resources/roap_covid_response_sitrep_18.pdf"
              }
            ],
            "url_alias": "https://reliefweb.int/report/afghanistan/covid-19-response-iom-regional",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/1255",
                "longname": "International Organization for Migration",
                "spanish_name": "Organización Internacional para las Migraciones",
                "name": "International Organization for Migration",
                "id": 1255,
                "type": { "name": "International Organization", "id": 272 },
                "shortname": "IOM",
                "disclaimer": "Copyright © IOM. All rights reserved.",
                "homepage": "http://www.iom.int/"
              }
            ],
            "title": "COVID-19 Response: IOM Regional Office for Asia Pacific Situation Report 18 - September 16, 2020"
          },
          "href": "https://api.reliefweb.int/v1/reports/3670541"
        },
        {
          "id": "3670672",
          "fields": {
            "date": { "original": "2020-09-16T00:00:00+00:00" },
            "url_alias": "https://reliefweb.int/report/nepal/nepal-earthquake-national-seismological",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/620",
                "longname": "European Commission's Directorate-General for European Civil Protection",
                "spanish_name": "Dirección General de Protección Civil y Operaciones de Ayuda Humanitaria Europeas",
                "name": "European Commission's Directorate-General for European Civil Protection",
                "id": 620,
                "type": { "name": "International Organization", "id": 272 },
                "shortname": "ECHO",
                "homepage": "http://ec.europa.eu/echo"
              }
            ],
            "title": "Nepal – Earthquake (National Seismological Centre, Media) (ECHO Daily Flash of 16 September)"
          },
          "href": "https://api.reliefweb.int/v1/reports/3670672"
        },
        {
          "id": "3670318",
          "fields": {
            "date": { "original": "2020-09-15T00:00:00+00:00" },
            "file": [
              {
                "filename": "ROAP_Snapshot_200915.pdf",
                "description": "",
                "mimetype": "application/pdf",
                "id": "1535520",
                "filesize": "2232027",
                "url": "https://reliefweb.int/sites/reliefweb.int/files/resources/ROAP_Snapshot_200915.pdf"
              }
            ],
            "url_alias": "https://reliefweb.int/report/myanmar/asia-and-pacific-weekly-regional",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/1503",
                "longname": "United Nations Office for the Coordination of Humanitarian Affairs",
                "spanish_name": "Oficina de Coordinación de Asuntos Humanitarios",
                "name": "UN Office for the Coordination of Humanitarian Affairs",
                "id": 1503,
                "type": { "name": "International Organization", "id": 272 },
                "shortname": "OCHA",
                "disclaimer": "To learn more about OCHA's activities, please visit https://www.unocha.org/.",
                "homepage": "http://www.unocha.org/"
              }
            ],
            "title": "Asia and the Pacific: Weekly Regional Humanitarian Snapshot (8 - 14 September 2020)"
          },
          "href": "https://api.reliefweb.int/v1/reports/3670318"
        }
      ]
    }
"""

RELIEF_WEB_MOCK_DATA_PAGE_2_RAW = """
    {
      "time": 11,
      "href": "https://api.reliefweb.int/v1/reports?appname=thedeep.io",
      "links": {
          "self": {
              "href": "https://api.reliefweb.int/v1/reports?appname=thedeep.io"
          }
      },
      "took": 4,
      "totalCount": 4,
      "count": 10,
      "data": [
        {
          "id": "3670885",
          "fields": {
            "date": { "original": "2020-09-17T00:00:00+00:00" },
            "url_alias": "https://reliefweb.int/report/nepal/nepal-makes-progress-human-capital-development",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/1220",
                "longname": "The World Bank Group",
                "spanish_name": "Banco Mundial",
                "name": "World Bank",
                "id": 1220,
                "type": { "name": "International Organization", "id": 272 },
                "shortname": "World Bank",
                "homepage": "http://www.worldbank.org"
              }
            ],
            "title": "Nepal makes progress in human capital development"
          },
          "href": "https://api.reliefweb.int/v1/reports/3670885"
        },
        {
          "id": "3670541",
          "fields": {
            "date": { "original": "2020-09-16T00:00:00+00:00" },
            "file": [
              {
                "filename": "roap_covid_response_sitrep_18.pdf",
                "description": "",
                "mimetype": "application/pdf",
                "id": "1535625",
                "filesize": "1684789",
                "url": "https://reliefweb.int/sites/reliefweb.int/files/resources/roap_covid_response_sitrep_18.pdf"
              }
            ],
            "url_alias": "https://reliefweb.int/report/afghanistan/covid-19-response-iom-regional",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/1255",
                "longname": "International Organization for Migration",
                "spanish_name": "Organización Internacional para las Migraciones",
                "name": "International Organization for Migration",
                "id": 1255,
                "type": { "name": "International Organization", "id": 272 },
                "shortname": "IOM",
                "disclaimer": "Copyright © IOM. All rights reserved.",
                "homepage": "http://www.iom.int/"
              }
            ],
            "title": "COVID-19 Response: IOM Regional Office for Asia Pacific Situation Report 18 - September 16, 2020"
          },
          "href": "https://api.reliefweb.int/v1/reports/3670541"
        },
        {
          "id": "3670672",
          "fields": {
            "date": { "original": "2020-09-16T00:00:00+00:00" },
            "url_alias": "https://reliefweb.int/report/nepal/nepal-earthquake-national-seismological",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/620",
                "longname": "European Commission's Directorate-General for European Civil Protection",
                "spanish_name": "Dirección General de Protección Civil y Operaciones de Ayuda Humanitaria Europeas",
                "name": "European Commission's Directorate-General for European Civil Protection",
                "id": 620,
                "type": { "name": "International Organization", "id": 272 },
                "shortname": "ECHO",
                "homepage": "http://ec.europa.eu/echo"
              }
            ],
            "title": "Nepal – Earthquake (National Seismological Centre, Media) (ECHO Daily Flash of 16 September)"
          },
          "href": "https://api.reliefweb.int/v1/reports/3670672"
        },
        {
          "id": "3670318",
          "fields": {
            "date": { "original": "2020-09-15T00:00:00+00:00" },
            "file": [
              {
                "filename": "ROAP_Snapshot_200915.pdf",
                "description": "",
                "mimetype": "application/pdf",
                "id": "1535520",
                "filesize": "2232027",
                "url": "https://reliefweb.int/sites/reliefweb.int/files/resources/ROAP_Snapshot_200915.pdf"
              }
            ],
            "url_alias": "https://reliefweb.int/report/myanmar/asia-and-pacific-weekly-regional",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/1503",
                "longname": "United Nations Office for the Coordination of Humanitarian Affairs",
                "spanish_name": "Oficina de Coordinación de Asuntos Humanitarios",
                "name": "UN Office for the Coordination of Humanitarian Affairs",
                "id": 1503,
                "type": { "name": "International Organization", "id": 272 },
                "shortname": "OCHA",
                "disclaimer": "To learn more about OCHA's activities, please visit https://www.unocha.org/.",
                "homepage": "http://www.unocha.org/"
              }
            ],
            "title": "Asia and the Pacific: Weekly Regional Humanitarian Snapshot (8 - 14 September 2020)"
          },
          "href": "https://api.reliefweb.int/v1/reports/3670318"
        }
      ]
    }
"""

RELIEF_WEB_MOCK_EXCEPTED_LEADS = [
    {
        "id": "3670885",
        "title": "Nepal makes progress in human capital development",
        "published_on": datetime.date(2020, 9, 17),
        "url": "https://reliefweb.int/report/nepal/nepal-makes-progress-human-capital-development",
        "source_raw": "reliefweb",
        "source_type": "website",
        "author_raw": "World Bank",
    },
    {
        "id": "3670541",
        "title": "COVID-19 Response: IOM Regional Office for Asia Pacific Situation Report 18 - September 16, 2020",
        "published_on": datetime.date(2020, 9, 16),
        "url": "https://reliefweb.int/sites/reliefweb.int/files/resources/roap_covid_response_sitrep_18.pdf",
        "source_raw": "reliefweb",
        "source_type": "website",
        "author_raw": "International Organization for Migration",
    },
    {
        "id": "3670672",
        "title": "Nepal – Earthquake (National Seismological Centre, Media) (ECHO Daily Flash of 16 September)",
        "published_on": datetime.date(2020, 9, 16),
        "url": "https://reliefweb.int/report/nepal/nepal-earthquake-national-seismological",
        "source_raw": "reliefweb",
        "source_type": "website",
        "author_raw": "European Commission's Directorate-General for European Civil Protection",
    },
    {
        "id": "3670318",
        "title": "Asia and the Pacific: Weekly Regional Humanitarian Snapshot (8 - 14 September 2020)",
        "published_on": datetime.date(2020, 9, 15),
        "url": "https://reliefweb.int/sites/reliefweb.int/files/resources/ROAP_Snapshot_200915.pdf",
        "source_raw": "reliefweb",
        "source_type": "website",
        "author_raw": "UN Office for the Coordination of Humanitarian Affairs",
    },
    {
        "id": "3670885",
        "title": "Nepal makes progress in human capital development",
        "published_on": datetime.date(2020, 9, 17),
        "url": "https://reliefweb.int/report/nepal/nepal-makes-progress-human-capital-development",
        "source_raw": "reliefweb",
        "source_type": "website",
        "author_raw": "World Bank",
    },
    {
        "id": "3670541",
        "title": "COVID-19 Response: IOM Regional Office for Asia Pacific Situation Report 18 - September 16, 2020",
        "published_on": datetime.date(2020, 9, 16),
        "url": "https://reliefweb.int/sites/reliefweb.int/files/resources/roap_covid_response_sitrep_18.pdf",
        "source_raw": "reliefweb",
        "source_type": "website",
        "author_raw": "International Organization for Migration",
    },
    {
        "id": "3670672",
        "title": "Nepal – Earthquake (National Seismological Centre, Media) (ECHO Daily Flash of 16 September)",
        "published_on": datetime.date(2020, 9, 16),
        "url": "https://reliefweb.int/report/nepal/nepal-earthquake-national-seismological",
        "source_raw": "reliefweb",
        "source_type": "website",
        "author_raw": "European Commission's Directorate-General for European Civil Protection",
    },
    {
        "id": "3670318",
        "title": "Asia and the Pacific: Weekly Regional Humanitarian Snapshot (8 - 14 September 2020)",
        "published_on": datetime.date(2020, 9, 15),
        "url": "https://reliefweb.int/sites/reliefweb.int/files/resources/ROAP_Snapshot_200915.pdf",
        "source_raw": "reliefweb",
        "source_type": "website",
        "author_raw": "UN Office for the Coordination of Humanitarian Affairs",
    },
]

from connector.sources import (
    atom_feed,
    relief_web,
    rss_feed,
    emm,
    # acaps_briefing_notes,
    # unhcr_portal,
    # pdna,
    # research_center,
    # wpf,
    # humanitarian_response,
)

# -----------------------------------------------  RELIEF_WEB -----------------------------------------------
# SOURCE https://api.reliefweb.int/v1/reports?from=2020-09-10&country=NPL
RELIEF_WEB_MOCK_DATA = '''
    {
      "time": 11,
      "href": "https://api.reliefweb.int/v1/reports?appname=thedeep.io",
      "links": { "self": { "href": "https://api.reliefweb.int/v1/reports?appname=thedeep.io" },
        "next": { "href": "https://api.reliefweb.int/v1/reports?appname=thedeep.io&offset=10&limit=10" }
      },
      "took": 4,
      "totalCount": 14,
      "count": 10,
      "data": [
        {
          "id": "3670885",
          "score": 1,
          "fields": {
            "date": { "original": "2020-09-17T00:00:00+00:00" },
            "url_alias": "https://reliefweb.int/report/nepal/nepal-makes-progress-human-capital-development-thoughh-pandemic-threatens-gains-past",
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
            "title": "Nepal makes progress in human capital development though pandemic threatens gains of the past decade"
          },
          "href": "https://api.reliefweb.int/v1/reports/3670885"
        },
        {
          "id": "3670541",
          "score": 1,
          "fields": {
            "date": { "original": "2020-09-16T00:00:00+00:00" },
            "file": [
              {
                "preview": {
                  "url-thumb": "https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535625-roap_covid_response_sitrep_18.png",
                  "url-small": "https://reliefweb.int/sites/reliefweb.int/files/styles/attachment-small/public/resources-pdf-previews/1535625-roap_covid_response_sitrep_18.png",
                  "url-large": "https://reliefweb.int/sites/reliefweb.int/files/styles/attachment-large/public/resources-pdf-previews/1535625-roap_covid_response_sitrep_18.png",
                  "url": "https://reliefweb.int/sites/reliefweb.int/files/resources-pdf-previews/1535625-roap_covid_response_sitrep_18.png"
                },
                "filename": "roap_covid_response_sitrep_18.pdf",
                "description": "",
                "mimetype": "application/pdf",
                "id": "1535625",
                "filesize": "1684789",
                "url": "https://reliefweb.int/sites/reliefweb.int/files/resources/roap_covid_response_sitrep_18.pdf"
              }
            ],
            "url_alias": "https://reliefweb.int/report/afghanistan/covid-19-response-iom-regional-office-asia-pacific-situation-report-18-september",
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
          "score": 1,
          "fields": {
            "date": { "original": "2020-09-16T00:00:00+00:00" },
            "url_alias": "https://reliefweb.int/report/nepal/nepal-earthquake-national-seismological-centre-media-echo-daily-flash-16-september",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/620",
                "longname": "European Commission's Directorate-General for European Civil Protection and Humanitarian Aid Operations",
                "spanish_name": "Dirección General de Protección Civil y Operaciones de Ayuda Humanitaria Europeas",
                "name": "European Commission's Directorate-General for European Civil Protection and Humanitarian Aid Operations",
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
          "score": 1,
          "fields": {
            "date": { "original": "2020-09-15T00:00:00+00:00" },
            "file": [
              {
                "preview": {
                  "url-thumb": "https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535520-ROAP_Snapshot_200915.png",
                  "url-small": "https://reliefweb.int/sites/reliefweb.int/files/styles/attachment-small/public/resources-pdf-previews/1535520-ROAP_Snapshot_200915.png",
                  "url-large": "https://reliefweb.int/sites/reliefweb.int/files/styles/attachment-large/public/resources-pdf-previews/1535520-ROAP_Snapshot_200915.png",
                  "url": "https://reliefweb.int/sites/reliefweb.int/files/resources-pdf-previews/1535520-ROAP_Snapshot_200915.png"
                },
                "filename": "ROAP_Snapshot_200915.pdf",
                "description": "",
                "mimetype": "application/pdf",
                "id": "1535520",
                "filesize": "2232027",
                "url": "https://reliefweb.int/sites/reliefweb.int/files/resources/ROAP_Snapshot_200915.pdf"
              }
            ],
            "url_alias": "https://reliefweb.int/report/myanmar/asia-and-pacific-weekly-regional-humanitarian-snapshot-8-14-september-2020",
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
        },
        {
          "id": "3670292",
          "score": 1,
          "fields": {
            "date": { "original": "2020-09-15T00:00:00+00:00" },
            "url_alias": "https://reliefweb.int/report/nepal/feature-lessons-pandemic-nepal-learning-transform-its-agricultural-sector",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/8035",
                "longname": "Climate and Development Knowledge Network",
                "name": "Climate and Development Knowledge Network",
                "id": 8035,
                "type": { "name": "Other", "id": 275 },
                "shortname": "CDKN",
                "homepage": "http://www.cdkn.org/"
              }
            ],
            "title": "FEATURE: Lessons from the pandemic – Nepal is learning to transform its agricultural sector"
          },
          "href": "https://api.reliefweb.int/v1/reports/3670292"
        },
        {
          "id": "3670180",
          "score": 1,
          "fields": {
            "date": { "original": "2020-09-15T00:00:00+00:00" },
            "file": [
              {
                "preview": {
                  "url-thumb": "https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535487-pacific_logistics_cluster_airport_restrictions_information_200915.png",
                  "url-small": "https://reliefweb.int/sites/reliefweb.int/files/styles/attachment-small/public/resources-pdf-previews/1535487-pacific_logistics_cluster_airport_restrictions_information_200915.png",
                  "url-large": "https://reliefweb.int/sites/reliefweb.int/files/styles/attachment-large/public/resources-pdf-previews/1535487-pacific_logistics_cluster_airport_restrictions_information_200915.png",
                  "url": "https://reliefweb.int/sites/reliefweb.int/files/resources-pdf-previews/1535487-pacific_logistics_cluster_airport_restrictions_information_200915.png"
                },
                "filename": "pacific_logistics_cluster_airport_restrictions_information_200915.pdf",
                "description": "",
                "mimetype": "application/pdf",
                "id": "1535487",
                "filesize": "216256",
                "url": "https://reliefweb.int/sites/reliefweb.int/files/resources/pacific_logistics_cluster_airport_restrictions_information_200915.pdf"
              }
            ],
            "url_alias": "https://reliefweb.int/report/australia/pacific-airport-restrictions-information-updated-15-september-2020-0",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/1741",
                "longname": "United Nations World Food Programme",
                "spanish_name": "Programa Mundial de Alimentos",
                "name": "World Food Programme",
                "id": 1741,
                "type": { "name": "International Organization", "id": 272 },
                "shortname": "WFP",
                "homepage": "http://www.wfp.org"
              },
              {
                "href": "https://api.reliefweb.int/v1/sources/3594",
                "name": "Logistics Cluster",
                "id": 3594,
                "type": { "name": "International Organization", "id": 272 },
                "shortname": "Logistics Cluster",
                "homepage": "http://www.logcluster.org/"
              }
            ],
            "title": "Pacific - Airport Restrictions Information (Updated 15 September 2020)"
          },
          "href": "https://api.reliefweb.int/v1/reports/3670180"
        },
        {
          "id": "3670141",
          "score": 1,
          "fields": {
            "date": { "original": "2020-09-14T00:00:00+00:00" },
            "url_alias": "https://reliefweb.int/report/united-states-america/cws-condemns-tps-termination-which-could-lead-family-separation",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/515",
                "longname": "Church World Service",
                "name": "Church World Service",
                "id": 515,
                "type": { "name": "Non-governmental Organization", "id": 274 },
                "shortname": "CWS",
                "homepage": "http://cwsglobal.org/"
              }
            ],
            "title": "CWS Condemns TPS Termination, Which Could lead to Family Separation & Deportation of Hundreds of Thousands in the United States"
          },
          "href": "https://api.reliefweb.int/v1/reports/3670141"
        },
        {
          "id": "3670037",
          "score": 1,
          "fields": {
            "date": { "original": "2020-09-14T00:00:00+00:00" },
            "file": [
              {
                "preview": {
                  "url-thumb": "https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535427-DCA%20COVID-19%20and%20Flood%20Response_SITREP%20%23XXIV_Final%20.png",
                  "url-small": "https://reliefweb.int/sites/reliefweb.int/files/styles/attachment-small/public/resources-pdf-previews/1535427-DCA%20COVID-19%20and%20Flood%20Response_SITREP%20%23XXIV_Final%20.png",
                  "url-large": "https://reliefweb.int/sites/reliefweb.int/files/styles/attachment-large/public/resources-pdf-previews/1535427-DCA%20COVID-19%20and%20Flood%20Response_SITREP%20%23XXIV_Final%20.png",
                  "url": "https://reliefweb.int/sites/reliefweb.int/files/resources-pdf-previews/1535427-DCA%20COVID-19%20and%20Flood%20Response_SITREP%20%23XXIV_Final%20.png"
                },
                "filename": "DCA COVID-19 and Flood Response_SITREP #XXIV_Final .pdf",
                "description": "",
                "mimetype": "application/pdf",
                "id": "1535427",
                "filesize": "1712074",
                "url": "https://reliefweb.int/sites/reliefweb.int/files/resources/DCA%20COVID-19%20and%20Flood%20Response_SITREP%20%23XXIV_Final%20.pdf"
              }
            ],
            "url_alias": "https://reliefweb.int/report/nepal/covid19-nepal-covid-19-and-flood-response-situation-report-noxxiv-14-september-2020",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/759",
                "longname": "DanChurchAid",
                "name": "DanChurchAid",
                "id": 759,
                "type": { "name": "Non-governmental Organization", "id": 274 },
                "shortname": "DCA",
                "homepage": "https://www.danchurchaid.org"
              }
            ],
            "title": "Covid19: Nepal Covid 19 and Flood Response Situation Report No.XXIV, as of 14 September 2020"
          },
          "href": "https://api.reliefweb.int/v1/reports/3670037"
        },
        {
          "id": "3669991",
          "score": 1,
          "fields": {
            "date": { "original": "2020-09-14T00:00:00+00:00" },
            "url_alias": "https://reliefweb.int/report/nepal/nepal-landslides-echo-daily-flash-14-september-2020",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/620",
                "longname": "European Commission's Directorate-General for European Civil Protection and Humanitarian Aid Operations",
                "spanish_name": "Dirección General de Protección Civil y Operaciones de Ayuda Humanitaria Europeas",
                "name": "European Commission's Directorate-General for European Civil Protection and Humanitarian Aid Operations",
                "id": 620,
                "type": { "name": "International Organization", "id": 272 },
                "shortname": "ECHO",
                "homepage": "http://ec.europa.eu/echo"
              }
            ],
            "title": "Nepal - Landslides (ECHO Daily Flash of 14 September 2020)"
          },
          "href": "https://api.reliefweb.int/v1/reports/3669991"
        },
        {
          "id": "3669938",
          "score": 1,
          "fields": {
            "date": { "original": "2020-09-14T00:00:00+00:00" }, "file": [
              {
                "preview": {
                  "url-thumb": "https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535369-WFP-0000118958.png",
                  "url-small": "https://reliefweb.int/sites/reliefweb.int/files/styles/attachment-small/public/resources-pdf-previews/1535369-WFP-0000118958.png",
                  "url-large": "https://reliefweb.int/sites/reliefweb.int/files/styles/attachment-large/public/resources-pdf-previews/1535369-WFP-0000118958.png",
                  "url": "https://reliefweb.int/sites/reliefweb.int/files/resources-pdf-previews/1535369-WFP-0000118958.png"
                },
                "filename": "WFP-0000118958.pdf",
                "description": "",
                "mimetype": "application/pdf",
                "id": "1535369",
                "filesize": "687873",
                "url": "https://reliefweb.int/sites/reliefweb.int/files/resources/WFP-0000118958.pdf"
              }
            ],
            "url_alias": "https://reliefweb.int/report/nepal/nepal-covid-19-mvam-market-update-4-27-31-july-2020",
            "source": [
              {
                "href": "https://api.reliefweb.int/v1/sources/551",
                "longname": "Government of Nepal",
                "name": "Government of Nepal",
                "id": 551,
                "type": { "name": "Government", "id": 271 },
                "shortname": "Govt. Nepal",
                "homepage": "http://www.nepalgov.gov.np/"
              },
              {
                "href": "https://api.reliefweb.int/v1/sources/1741",
                "longname": "United Nations World Food Programme",
                "spanish_name": "Programa Mundial de Alimentos",
                "name": "World Food Programme",
                "id": 1741,
                "type": { "name": "International Organization", "id": 272 },
                "shortname": "WFP",
                "homepage": "http://www.wfp.org"
              }
            ],
            "title": "Nepal: COVID-19 mVAM Market Update #4 (27 - 31 July 2020)"
          },
          "href": "https://api.reliefweb.int/v1/reports/3669938"
        }
      ]
    }
'''
RELIEF_WEB_MOCK_DATA_LAMBDA_RESPONSE_EXISTING_SOURCES = [
    {"url": "https://reliefweb.int/report/nepal/feature-lessons-pandemic-nepal-learning-transform-its-agricultural-sector", "status": "success"},
    {"url": "https://reliefweb.int/sites/reliefweb.int/files/resources/pacific_logistics_cluster_airport_restrictions_information_200915.pdf", "status": "success"},
    {"url": "https://reliefweb.int/report/united-states-america/cws-condemns-tps-termination-which-could-lead-family-separation", "status": "success"},
]
RELIEF_WEB_MOCK_DATA_LAMBDA_RESPONSE_NEW_SOURCES = [
    {"url": "https://reliefweb.int/report/nepal/nepal-makes-progress-human-capital-development-thoughh-pandemic-threatens-gains-past", "status": "success"},
    {"url": "https://reliefweb.int/sites/reliefweb.int/files/resources/roap_covid_response_sitrep_18.pdf", "status": "success"},
    {"url": "https://reliefweb.int/report/nepal/nepal-earthquake-national-seismological-centre-media-echo-daily-flash-16-september", "status": "success"},
    {"url": "https://reliefweb.int/sites/reliefweb.int/files/resources/ROAP_Snapshot_200915.pdf", "status": "failure"},
    {"url": "https://reliefweb.int/sites/reliefweb.int/files/resources/DCA%20COVID-19%20and%20Flood%20Response_SITREP%20%23XXIV_Final%20.pdf", "status": "success"},
    {"url": "https://reliefweb.int/report/nepal/nepal-landslides-echo-daily-flash-14-september-2020", "status": "success"},
    {"url": "https://reliefweb.int/sites/reliefweb.int/files/resources/WFP-0000118958.pdf", "status": "success"},
]

# -----------------------------------------------  ATOM FEED -----------------------------------------------
ATOM_FEED_MOCK_DATA = '''
    <?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom" xmlns:idx="urn:atom-extension:indexing" xmlns:media="http://search.yahoo.com/mrss/" idx:index="no">
        <!--
    Content-type: Preventing XSRF in IE.
    -->
        <generator uri="http://cloud.feedly.com">feedly cloud</generator>
        <id>tag:feedly.com,2013:cloud/feed/https://feedly.com/f/RgQDCHTXsLH8ZTuoy7N2ALOg</id>
        <link rel="self" type="application/rss+xml" href="https://feedly.com/f/RgQDCHTXsLH8ZTuoy7N2ALOg?count=5"/>
        <link rel="next" type="application/rss+xml" href="https://feedly.com/f/RgQDCHTXsLH8ZTuoy7N2ALOg?count=5&amp;continuation=17497c9a7cc:36480c:ce98bd6a"/>
        <title>ROSA / ROSA's Mozambique Board</title>
        <updated>2020-09-16T20:44:10Z</updated>
        <entry>
            <id>tag:feedly.com,2013:cloud/entry/tCS+2m1OpGdjXiXxCw+JFMvBfkRWtIxNSz4wk+LTxZw=_17498a8e23d:453c96:9bed6622</id>
            <title type="html">Mozambique video of killing fake, says defence minister</title>
            <published>2020-09-16T20:43:58Z</published>
            <updated>2020-09-16T20:44:10Z</updated>
            <link rel="alternate" href="https://www.bbc.com/news/world-africa-54179776" type="text/html"/>
            <summary type="html">The footage shows a naked women being beaten then shot dead by men wearing army uniforms.</summary>
            <content type="html">&lt;div&gt;&lt;div&gt;&lt;div&gt;&lt;article&gt;&lt;header&gt;&lt;h1 tabindex="-1"&gt;Mozambique video of killing fake, says defence minister&lt;/h1&gt;&lt;/header&gt;&lt;div&gt;&lt;figure&gt;&lt;div&gt;&lt;span&gt;&lt;span&gt;&lt;/span&gt;&lt;div class="feedlyNoScript"&gt;&lt;img alt="Grab of the killing footage" src="https://c.files.bbci.co.uk/141B5/production/_114375328_mozpng.png"&gt;&lt;/div&gt;&lt;/span&gt;&lt;span&gt;&lt;span&gt;image copyright&lt;/span&gt;Twitter/ @ZenaidaMachado&lt;/span&gt;&lt;/div&gt;&lt;figcaption&gt;&lt;span&gt;image caption&lt;/span&gt;Human rights activists circulated the video on social media&lt;/figcaption&gt;&lt;/figure&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;&lt;b&gt;Mozambique's Defence Minister Jaime Neto has said that a video showing people dressed in army uniforms beating and killing a naked woman was doctored. &lt;/b&gt;&lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;The culprits had been identified and would be punished, he added.&lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;The video caused outrage after it was circulated on social media. The defence ministry promised to investigate. &lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;The video was said to have been filmed in the gas-rich Cabo Delgado province, where government troops are battling militant Islamists.&lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;The militants are known as al-Shabab, and have pledged allegiance to the Islamic State militant group.&lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;They have carried out a series of attacks on villages and towns in the area over the past three years, leaving more than 1,500 people dead and at least 250,000 homeless.&lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;Government forces have been accused of human rights abuses while trying to put down the insurgency.&lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;Several rights groups shared the two-minute-long clip of the alleged killing of the woman on Monday. &lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;In the video, a group of men wearing army uniform surround a woman, one hits her in the head and body with a stick several times before others shoot. &lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;The defence ministry condemned the footage as &amp;quot;horrifying&amp;quot; and said it would carry out an investigation to establish whether it was authentic. &lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;figure&gt;&lt;figcaption&gt;&lt;span&gt;media caption&lt;/span&gt;The Islamic State has been behind the growing wave of violence in northern Mozambique.&lt;/figcaption&gt;&lt;/figure&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;Speaking on a local television station on Wednesday, Mr Neto said the video had been edited by &amp;quot;malicious people&amp;quot; to denigrate the image of the military. &lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;He did not give further details, but said the people responsible for creating the video would be paraded in front of the public and punished. &lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;Troops would continue with operations to restore peace in the region, Mr Neto added. &lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;Last week, Amnesty International said it had analysed and verified videos showing attempted beheadings, torture and other ill treatment of prisoners, the dismemberment of alleged fighters and possible extrajudicial executions.&lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;But the government denied the allegations, saying the insurgents were known to &amp;quot;impersonate soldiers&amp;quot;. &lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;Cabo Delgado is home to one of Africa's biggest liquefied natural gas projects.&lt;/p&gt;&lt;/div&gt;&lt;div&gt;&lt;p&gt;Exxon Mobil is a major investor in the development of natural gas projects worth $60bn (£45bn) off the region's coast. &lt;/p&gt;&lt;/div&gt;&lt;/article&gt;&lt;/div&gt;&lt;/div&gt;&lt;/div&gt;</content>
            <author>
                <name></name>
            </author>
            <media:content medium="image" url="https://ichef.bbci.co.uk/news/1024/branded_news/141B5/production/_114375328_mozpng.png"/>
        </entry>
        <entry>
            <id>tag:feedly.com,2013:cloud/entry/tCS+2m1OpGdjXiXxCw+JFMvBfkRWtIxNSz4wk+LTxZw=_17498a83a7d:478db4:1c396234</id>
            <title type="html">Amnesty International calls for investigation into video showing execution of woman in Mozambique</title>
            <published>2020-09-16T20:43:15Z</published>
            <updated>2020-09-16T20:43:52Z</updated>
            <link rel="alternate" href="https://www.cnn.com/2020/09/16/africa/amnesty-mozambique-video-killing-investigation-intl/index.html" type="text/html"/>
            <summary type="html">Amnesty International has called for an immediate investigation into the apparent extrajudicial killing of a woman in Mozambique that was shared widely in a horrifying video on social media earlier this week. </summary>
            <content type="html">&lt;div&gt;&lt;div&gt;&lt;div&gt;&lt;p&gt;In the nearly two-minute-long video, men wearing military uniforms are seen chasing down a naked woman, surrounding and verbally harassing her along a rural road. One of the men repeatedly beats her with a stick before another man shoots her at close range. &lt;/p&gt;&lt;p&gt;She is then repeatedly shot by the men while lying on the road before one of the men shouts &amp;quot;Stop, stop, enough, it's done.&amp;quot; &lt;/p&gt;&lt;div&gt;&lt;p&gt;The video ends as the men turn and walk away, with one of them announcing, &amp;quot;They've killed the al-Shabaab,&amp;quot; the local name given to the growing insurgency in the far north of the country. &lt;/p&gt;&lt;p&gt;It has no known links to the Somali terrorist group of the same name. The uniformed man looks directly into camera and raises his two fingers before the recording stops. &lt;/p&gt;&lt;p&gt; &lt;/p&gt;&lt;p&gt;&amp;quot;The horrendous video is yet another gruesome example of the gross human rights violations taking place in Cabo Delgado by the Mozambican forces,&amp;quot; said Deprose Muchena, Amnesty International's Director for East and Southern Africa.&lt;/p&gt;&lt;p&gt; &lt;/p&gt;&lt;p&gt;In its own analysis of the video, the human rights group says that the men were wearing the uniform of the Mozambican military. Amnesty says four different gunmen shot the woman a total of 36 times with AK-47s and PKM-style machine guns. Its investigation concluded that the incident took place near Awasse in the country's northernmost province Cabo Delgado. &lt;/p&gt;&lt;p&gt; &lt;/p&gt;&lt;p&gt;&amp;quot;The incident is consistent with our recent findings of appalling human rights violations and crimes under international law happening in the area,&amp;quot; said Muchena. &lt;/p&gt;&lt;p&gt; &lt;/p&gt;&lt;p&gt;CNN could not independently the authenticity of the video, the date and location it was filmed, nor the identity of the gunmen. &lt;/p&gt;&lt;p&gt; &lt;/p&gt;&lt;p&gt;Mozambique's Minister of Interior Amade Miquidade denied the accusations of atrocities, though did not address the video specifically, on national television Tuesday, saying that insurgents frequently wear army uniforms. &lt;/p&gt;&lt;p&gt; &lt;/p&gt;&lt;p&gt;&amp;quot;When they want to produce their propaganda against the security and defense forces, against the Mozambican state, they remove those signs/characters that identify them and make videos to promote an image of atrocity practiced by those who defend the people,&amp;quot; he said. &lt;/p&gt;&lt;p&gt; &lt;/p&gt;&lt;p&gt;Cabo Delgado is home to a $60 billion natural gas development that is heavily guarded by Mozambican military and private security. &lt;/p&gt;&lt;p&gt; &lt;/p&gt;&lt;p&gt;Loosely aligned with ISIS, the insurgents have undertaken increasingly sophisticated attacks in recent months, overrunning large parts of Mocimba de Praia, a strategic port north of the regional capital Pemba in August. Unlike in previous attacks, government forces have struggled to fully retake the territory. &lt;/p&gt;&lt;p&gt; &lt;/p&gt;&lt;p&gt;The insurgents have been accused by the government and human rights groups of their own violent abuses -- including beheadings, looting, and indiscriminate killing of civilians. &lt;/p&gt;&lt;p&gt; &lt;/p&gt;&lt;p&gt;And the interior minister highlighted those alleged abuses on Tuesday. &lt;/p&gt;&lt;p&gt; &lt;/p&gt;&lt;p&gt;&amp;quot;Once more, our country continues to be the object of aggression by the terrorists, namely in the province of Cabo Delgado, where they've enforced cruel, inhuman, atrocious acts against our population,&amp;quot; said Miquidade.&lt;/p&gt;&lt;p&gt; &lt;/p&gt;&lt;p&gt;Security analysts and human rights workers say that insurgents operating in the area do sometimes wear Mozambican military uniforms. But the uniformed men in the video showing the woman's killing speak Portuguese, generally more common to Mozambicans from the South. &lt;/p&gt;&lt;/div&gt;&lt;p&gt;CNN's David McKenzie and Brent Swails reported from Johannesburg and Vasco Cotovio reported from London.&lt;/p&gt;&lt;/div&gt;&lt;/div&gt;&lt;/div&gt;</content>
            <author>
                <name>David McKenzie, Brent Swails and Vasco Cotovio, CNN</name>
            </author>
            <media:content medium="image" url="https://cdn.cnn.com/cnnnext/dam/assets/200916120007-amnesty-mozambique-video-killing-investigation-intl-super-tease.jpg"/>
        </entry>
        <entry>
            <id>tag:feedly.com,2013:cloud/entry/tCS+2m1OpGdjXiXxCw+JFMvBfkRWtIxNSz4wk+LTxZw=_174989be204:4965e5:c6875822</id>
            <title type="html">Mocimboa da Praia é o distrito epicentro de recrutamento de jovens pelos Terroristas</title>
            <published>2020-09-16T20:29:46Z</published>
            <updated>2020-09-16T20:30:01Z</updated>
            <link rel="alternate" href="https://cjimoz.org/news/mocimboa-da-praia-e-o-distrito-epicentro-de-recrutamento-de-jovens-pelos-terroristas/" type="text/html"/>
            <summary type="html">Por CJI O Centro de Jornalismo Investigativo de  Moçambique (CJI Moçambique) apurou que o distrito de  Mocimboa da Praia é o epicentro de recrutamento de jovens para as fileiras dos Terroristas que…</summary>
            <content type="html">&lt;div&gt;&lt;div&gt;&lt;div&gt;&lt;div&gt;&lt;p&gt;Por CJI&lt;/p&gt;
    &lt;p&gt;O Centro de Jornalismo Investigativo de  Moçambique (CJI Moçambique) apurou que o distrito de  Mocimboa da Praia é o epicentro de recrutamento de jovens para as fileiras dos Terroristas que actuam em Cabo Delgado há mais de 2 anos. Tendo como ponto de partida o aprofundamento &lt;a href="https://cjimoz.org/news/bonomado-machude-omar-ou-ibn-omar-o-mocambicano-nas-lides-terroristas-na-carnificina-de-cabo-delgado/"&gt;do comandante dos ataques Ibn Omar, ou seja Bonomade Machude Omar ou Leão da Floresta como é conhecido por seus colegas Al Shabaab, este que é o cabecilha procurado pelas autoridades desde o início desta guerra&lt;/a&gt;. Os ataques dos alegados Jihadistas do Al Shabaab, que vêm atacando a Provincia de Cabo Delgado no Norte de Moçambique ,desde 5 de Outubro de  2017, já féz várias vítimas humanas deixando assim muitas crianças órfãs, mulheres e homens viúvos sem contar com a destruição de casas, escolas, hospitais, machambas, mercados e outras infraestruturas do governo e individuais.Acompanhe atentamente a conversa abaixo, entre residentes de Mocimboa da Praia e a equipa de reportagem do CJI.&lt;/p&gt;
    &lt;p&gt;&lt;img alt src="https://cjimoz.org/news/wp-content/uploads/2020/09/costa-mocimboa-123-400x267.jpg"&gt;&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol&gt;&lt;li&gt;Conheces Bonomade Machude Omar?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt;Não conheço.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="2"&gt;&lt;li&gt;Viste o video dos insurgentes? Aquela reunião que foi realizada em Mocimboa da Praia entre população e os terrorristas?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt;Sim vi…&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="3"&gt;&lt;li&gt;Então refiro-me ao jovem que foi orador daquele encontro. Conhces?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt;Aquele eu conheço, o Ibin Omar. Sim o conheço. Todos aqueles são daqui  Mocimboa da Praia, a maior parte nesse caso. Mas não são daqui da vila sede de Mocimboa da Praia. Mas eu os conheço a todos. Aqueles jovens simplesmente aparecem aqui na vila fazem os seus desmandos e saem para a suas zonas. Embora existem um e outro membros residentes aqui na vila, e não se mostram como membros integrantes, más nas noites temos visto a sairem mascarados para la na base deles.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="4"&gt;&lt;li&gt;Onde fica essa base? Conheces?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt;Não conheço a base, más todos sabemos que eles têm feito seus encontros la na zona do Milamba e Nanduadua, daí vão as matas. Aqui chamamos Milamba de base deles porquê têm aceitação  do povo daquele bairro.la encontram-se a vontade.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="5"&gt;&lt;li&gt;Onde é que vivem a maioria deles?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;A maioria vivem no bairro do Milamba e Nanduadua, como disse a posterior. Esses dois bairros principalmente o Milamba é praticamente governado por eles, aquilo já é  deles. Esse bairro é muito deles…nós chegamos lá uma vez à outra, durante o dia, mesmo assim questionam se estamos a ir lá para tirar informações e dar ao governo. Por isso vamos com pouca frequência. Eles são assustadores.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="6"&gt;&lt;li&gt;E se eu for para la, eles vão me pegar, ou simplesmente vão fazer-me muitas questoes para saberem o que quero nessas zonas? Afinal sou jornalista e quero entrevista-los…&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Sera difícil falar com eles, só posso ti mostrar assim de longe que aquele mais aquele fazem parte do grupo. Ir lá contigo não posso porque tenho medo. Ainda quero viver!&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="7"&gt;&lt;li&gt;Tens algum contacto deles? Quero ligar para eles marcando uma entrevista…&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Eu não tenho contacto deles, os saudo para desfarçar, tenho de sorrir um pouco com eles, conversar por uns 5 minutos e prontos ,regressar á casa. E se você for lá, bonita assim não sei, não quero viver com peso na consciência por ter ti entregue nas mãos dos bandidos. Vou te mostrar alguns assim e longe para simplesmente os veres, e não fales com ninguém, não saude quem não ti saudou, e usa roupas islamicas tire as calsas de jeans.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="8"&gt;&lt;li&gt;E vão partir meu BI?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Não leve BI, leve seu credencial de Jornalista. Se és do jornal Notícia, rádio Moçambique e TVM você não volta, porque são do governo e não  gostam do governo.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="9"&gt;&lt;li&gt;Sou jornalista do CJI Moçambique e vim fazer meu trabalho,&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Se for assim tudo bem, podemos ir a vontade. Deixa que eu fale primeiro e não pergunte muita coisa. Eu ainda quero viver.kkkkkk, esses jovens assustam sra jornalista.Trata-se de um bairro onde sairam muitos jovens e juntaram-se com eles lá nas matas.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="10"&gt;&lt;li&gt;As pessoas sabem disso?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Sabem sim, todos têm conhecimento de que fulano e fulano estão no mato e são membros do terroristas do Estado Islamico. Alguns fazem ida e volta outros desde que saíram antes dos ataques ainda não regressaram às  suas casas .&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="11"&gt;&lt;li&gt;Tem certeza que todos conhecem os Al Shabaab de Mocimboa da Praia?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Tenho certeza absoluta. Nós conhecemos a todos, sejam da vila assim como os dos bairros Milamba e Nanduadua.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="12"&gt;&lt;li&gt;Os chefes dos bairros sabem disso? Qual e o posicionamento deles?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt;Sabem disso, conhecem as pessoas, mas têm  muito medo dos Al Shabaab. Se eles mostrarem muita preocupação podem perder a vida. Sabe senhora jornalista, os chefes dos bairros, quarteiroes, vivem ao redor dos Al Shabaab, estão mesmo lá na zona deles, vivem com constantes  ameaças. Por isso que  ficam calados.e olha que nem têm a coragem de dizer que vivem ameaçados e podem vir a desmentir isso. Estão todos dominados pelos Al Shabaab.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="13"&gt;&lt;li&gt;O Governo provincial e distrital têm conhecimento disso? Vocês como moradores já apresentaram este assunto as autoridades?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;O governo conhece este assunto. Sabem que nos bairros Milamba e Nanduadua 90% dos jovens, para nao dizer todos jovens estão filiados aos terrorristas Jihadistas denominados por Al Shabaab. Sabem que eles têm feito ataques e matam pessoas. Também conhecem os jovens que fazem isso.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="14"&gt;&lt;li&gt;O que fazem para combater este problema nesses bairros?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Senhora jornalista, não posso responder em nome do governo, porque eu como residente em Mocimboa da Praia nao vejo nada. A maioria do governo distrital fugiram daqui, policias e militares têm tido muitas baixas com grupo, e ambos compartilham as fardas. Como confiar no governo assim? Se eles é que dão as fardas para nós morrermos.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="15"&gt;&lt;li&gt;O que os Al Shabaab fazem nessas zonas onde consideram deles?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Eles fazem patrulha durante a noite, principalmente no bairro Milamba. Procuram saber se tens documentos, revistam as carteiras, quando acham seu documento eles rasgam ou partem. Eles dizem que ”são essas coisas de KAFIRI que  eles não querem”.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="16"&gt;&lt;li&gt;As pessoas não devem ter documentos?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Sim. Para eles, as pessoas  não devemos ter documentos.Isso são coisas de politicos mentirosos, descrentes, pessoas infiéis.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="17"&gt;&lt;li&gt;O Governo sabe disso?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Sim, o governo sabe. Tem esse conhecimento porque comunicamos as autoridades locais, e como morradores daqui eles sabem disso, e eles vêm as coisas á acontecerem.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="18"&gt;&lt;li&gt;As FDS, têm feito patrulha?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Os nossos militares fazem  patrulha, mà s não chegam nessas zonas, das poucas vezes que lá chegam tem sido durante o dia, porque de noite eles têm medo. Nunca passam por aquelas bandas durante a noite, sabem que Milamba é dos Al Shabaab.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="19"&gt;&lt;li&gt;Como é a convivência entre a população e os jovens filiados ao terrorismo?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Como assim? Se eles também  são população…eles apoiam esses actos, gostam dos Al Shabaabs. Durante a noite eles andam a vontade e sabem que  são protegidos pelos  terroristas. Ali estão os filhos, maridos, sobrinhos, visinhos, e têm a mesma crença. Estão convencidos de que esse é o certo.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="20"&gt;&lt;li&gt;Voltemos ao assunto da tal patrulha feita pelos Al Shabaab no bairro Milamba, que tipo de equipamentos usam na sua actividade?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Eles usam a farda militar das nossas forças, usam armas de fogo, catanas e facas. Alguns deles usam mascaras. Eles andam com aquelas fardas da FADM com muito estilo, e muitos fazem confusão com os nossos militares. Por isso que existem informações a dizer que os militares, fizeram patrulhas numa zona daí levaram bens da população, enquanto não são  eles.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="21"&gt;&lt;li&gt;Como é a quarentena nesses bairros onde a liderança esta nas mãos dos bandidos?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Não  hà  quarentena. Eles disseram a população que esse decreto do Presidente da Republica de Moçambique Filipe Jacinto Nyusy,  não serve para aquelas comunidades, Nyusy não  nos dá ordens e nem decretos, aqui não existe isso. Entretanto, disseram as comunidades que a actividades continuam naturalmente, excepto as aulas uma vez que eles não se importam com escola não sentem falta da mesma, e muitos profesores estão ausentes naquele distrito. As  mesquitas e mercados funcionam naturalmente. Todos vão as mesquitas porque é uma ordem de Al Shabaab nao ficar em casa.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="22"&gt;&lt;li&gt;É verdade que estão a ser obrigados a rezar 3 vezes ao dia para além de 5?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Sim é verdade, aqui apenas rezamos 3 vezes porque assim fomos intruidos pelos Al Shabaab que comandam aqui em Mocimboa da Praia principalmente bairro Milamba.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="23"&gt;&lt;li&gt;O Governo sabe disso?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Obviamente que sabe.  As mesquitas continuam aberta normalmente e não há quem não saiba disso.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="24"&gt;&lt;li&gt;Eles ganham dinheiro?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Sim ganham, têm regressado das matas com valores para casa das familias.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="25"&gt;&lt;li&gt;Eles dizem quem lhes da dinheiro?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt;Não dizem, até agora tentamos investigar quem manipula os nossos filhos e até então sem sucesso. Conhecemos os chefes que estão no mato. O grande patrão, não conhecemos o patrocinador deles. Estamos a ver assim mesmo. Desde 2017 e não sabemos mais nada.  Mesmo esses que estão no mato não são todos que conhecem o grande chefe.simplesmente foram recrutados por peixes pequenos que não confiam neles por isso não sabem quem os paga.parece que há um juramento lá no treinamento deles.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Naquele dia da reunião com a população muitos dirigiram-se a casa das suas famílias, uns tinham os tido como mortos, desaparecidos, naquele dia mostraram-se. Houve muita emoção, eles  diziam:” papá e mamã não chorem, eu estou nessa guerra, e vamos vencer”.Diziam eles. Deixaram dinheiro e alguns produtos alimentares em casa dos familiares.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Lá no bairro Milamba, todos dias ha voluntarios para as matas.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="26"&gt;&lt;li&gt;Como assim voluntários?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Sim pessoas que querem estar naquele grupo por vontade própria. Pedem aos membros intergrantes para se juntarem ao grupo e logo são aceites. Por isso que eles cada dia que passa o nùmero de Al Shaabab tende á aumentar.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="27"&gt;&lt;li&gt;Isso está cumplicado ainda. As famílias aceitam o dinheiro na maior tranquilidade?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Sim, porque não! A senhora jornalista sabe que dinheiro fala todas as linguas, aqueles bandidos compraram telefones e abriram mpesa para mandar dinheiro as suas familias, eles estando no mato.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="28"&gt;&lt;li&gt;Tens algum número dessas famílias que recebem via mpesa, dinheiro deses bandidos?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Nao tenho,  não quero correr o risco de pedir número de familiares deles e ser desconfiado. Mas todos sabemos disso.Ouvimos e ficamos quietos. Quando estamos a ver, fingimos que não vimos nada e dessa forma evitamos ter problemas. Temos muito medo deles.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="29"&gt;&lt;li&gt;Não tem vindo estrangeiros por aqui, falar com os Al Shabaab?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Aparecem, aqui hà  muitos estrangeiros. Temos visto aqueles tanzanianos, nigerianos e uns que parecem da Somália. Essa equipa é muito grande e têm muita forca para combater.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;p&gt;&lt;img alt src="https://cjimoz.org/news/wp-content/uploads/2020/09/hospital-mocimboa-203-400x267.jpg"&gt;&lt;/p&gt;
    &lt;p&gt;Depois desta pequena conversa com naturais e residentes em Mocimboa, província de Cabo delgado, a equipa de reportagem do Centro de Jornalismo Investigativo de Moçambique entrou em contacto com uma fonte no Niassa, com colaboração de jornalista de alguns colegas de uma rádio comunitária naquele ponte do país. Trata-se de um membro, aliás, o primeiro membro recrutado para o grupo de bandidos armados que actuam em Cabo Delgado. Este que foi recrutado em Niassa no ano de 2007, como conta na primeira pessoa à nossa equipa.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="30"&gt;&lt;li&gt;Conte-nos a sua história, a sua relação com os primeiros Al Shabaab a entrarem em Mocambique.&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Estava com eles desde 2007, fui levado para ser empregado doméstico, mas caso particular nas lojas. Sempre que aparecesse um Somalis, eu era mandatado para dar dinheiro a eles e de seguida eles abriam suas baracas, por causa da confiança que tinham comigo, eles disseram que pretenciam matar pessoas, foram sinceros comigo quando disseram que eles são Al Shabaab, disseram que não pretendiam casar ou formar familias aqui em Moçambique o que lhes interessava era apenas matar pessoas impura, descrentes do Islamismo. Passaram em Niassa, Nampula, Cabo Delgado, em muitos distritos onde eles passaram a recrutar pessoas e eu andava com eles até fora do país fomos juntos e sempre diziam a mesma coisa e enfatizavam ainda que as  pessoas de Cabo Delgado são muito burras, não sabem nada, lá há muita riqueza, os naturais não estão a saber fazer o devido uso, nòs queremos essas riquezas. Tive medo de ir a polícia denuncia-los, iriam matar-me, e toda minha familia também. Na minha familia uma vez que não sabiam de nada, sempre que eu viajasse regressava da mesma maneira, ja estava a ficar abatido, magro de tanto pensar e diziam que estou doente, outrora diziam que sou burro porque não sei aproveitar as oportunidades de crescer na vida. Se estou vivo ate hoje, dou graças a Deus porque tem me guardado até hoje.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="31"&gt;&lt;li&gt;Onde està a base deles?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;A base deles está em Cabo Delgado, esse lado de Megomano, para quem vai ao rio Rovuma, eles entraram apartir de Tanzania e claro, há Tanzanianos, Congoleses, Ugandeses, Senegalenses envolvios. Eles têm uma aldeia por eles formada no meio dessas matas. Quando tu entras naquele lugar até parece que estas numa aldeia grande, enquanto é base dos Al Shabaab. É la onde deixam todas as pessoas por eles raptadas, sejam crianças raptadas, mulheres e jovens.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="32"&gt;&lt;li&gt;Que mecanismos usaram para recrutar pessoas?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Para recrutarem pessoas eles abriram muitas mesquitas, outros simplesmente filiaram-se nas mesquitas, foram rezando por um bom tempo depois começaram a criar grupinhos nas mesquitas, criaram intimidades,depois foram  induzindo com doutrinas radicais e extremistas do Alcorão, assim foram recrutarando para o Al Shabaab, e agora estão aí a atacar.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="33"&gt;&lt;li&gt;Como é que voce sabe diso?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt;Eu escutava tudo, era empregado doméstico, de confiança deles, afinal, fui o guia deles e o primeiro a ser recrutado como empregado.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="34"&gt;&lt;li&gt;Onde estão localizadas as suas lojas?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Aqui em Niassa estão localizados no mercado Central, lá  têm suas lojas, toda essa rua até proximo ao hotel Singea, nesse lado existe um que fez um armazem onde vende-se ferros, chapas de zinco, cimento, o proprietário disso também fáz parte desse grupo de Al Shabaab. Là  em Mandimba também existem. Olha, são muitos membros do Al Shabaab, estão la em Chowe, Caia, mandaram fazer take ways, ate no rio save. E eles fazem da seguinte forma, são rotativos, trabalham 2 anos saem e vem outros. Tudo para sustentar a guerra.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="35"&gt;&lt;li&gt;Porque a guerra em Moçambique? Porque Cabo Delgado?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Estão a lutar para ter o nosso dinheiro, pedras preciosas, ouro, pescoços, gargantas, ossos humanos, órgaos genitais humanos, vendem para ter dinheiro para eles sustentarem a guerra em Mocambique e outros países. Eles querem as riquezas naturais de Mocambique para eles como fazem em todos paises. E para eles comerem também-&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="36"&gt;&lt;li&gt;Como assim pedras preciosas? Pode exclarecer um pouco sobre isso?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt;Naquele grupo de garimpeiros ilegais eles estavam aí nesse grupo, quando o governo os expulsou tudo foi a baixo. Sabe, eles mandaram muitos Moçambicanos ao estrangeiro para estudar o Alcorão com intuito de ter extremistas nacionais. Muitos deles de Cabo Delgado e Nampula e Niassa. Nessas zonas há muitos Muçulmanos que dão muito prestigio aos tanzanianos e Nigerianos e quenianos. E foi através desses que houve muita aderencia ao Al Shabaab, é muito proximo da Tanzania principalmente porque aquelas zonas é de Muçulmanos e muitos falam Suahili e admiram a vizinha Tanzania. E as teorias do Shek Aboud Rogo eram mesmo uma entrada perfeita para recrutarem jovens ingenuose religiosos.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="37"&gt;&lt;li&gt;E verdade que eles têm curandeiros nos seus actos para não serem encontrados pelas autoridades?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Têm curandeiros muito potentes de Moçambique la para Palma, e outros de Tanzania e Quenia. De tudo que eles fazempassam primeiro por curandeiros, dizem para que tudo corra do jeito que eles querem.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;ol start="38"&gt;&lt;li&gt;Ja viste alguem do governo moçambicano com esse grupo?&lt;/li&gt;
    &lt;/ol&gt;&lt;p&gt;Sabe senhora jornalista, eles não entrariam no nosso país sem alguém abrir as portas. Vou mostrar-te as bases com muita calma. Mas saiba que são pessoas muito perigosas e têm  aliados de poder aqui em Moçambique.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;p&gt;Os Somalis de que me refiro têm algumas bombas de combustiveis que eles acabam de compar aqui em Niassa e sustentam a guerra em Cabo Delgado. Aqui em Niassa é uma das logisticas dos Al Shabaab. Veja essas bombas de gasolina:Global Petróleo, Sky Petróleo, e Mera. Onde uma esta em Cuamba e as outras 5 na cidade de Lichinga, a ultima bomba deles compraram de Sul Africanos apouco tempo, estão localizadas no bairro Sanjala, e neste momento em construção.&lt;/p&gt;
    &lt;/div&gt;
    &lt;/div&gt;&lt;/div&gt;&lt;/div&gt;</content>
            <author>
                <name></name>
            </author>
            <media:content medium="image" url="https://cjimoz.org/news/wp-content/uploads/2020/09/costa-mocimboa-123.jpg"/>
        </entry>
        <entry>
            <id>tag:feedly.com,2013:cloud/entry/tCS+2m1OpGdjXiXxCw+JFMvBfkRWtIxNSz4wk+LTxZw=_17497cf3034:35844c:af405028</id>
            <title type="html">Cerca de 700 jovens prestaram juramento hoje na Manhiça para o curso militar que arrancou em abril. Iniciou com mais de 800, mas outros desistiram. A cerimónia do encerramento foi secreta. Cerca de 200 deverão ir a #CaboDelgado enquanto outros às especialidades (artilharia etc).. pic.twitter.com/0QmZ2rWF6g&amp;mdash; Alexandre (@AllexandreMZ) September 14, 2020
    </title>
            <published>2020-09-16T16:46:12Z</published>
            <updated>2020-09-16T16:46:20Z</updated>
            <link rel="alternate" href="https://twitter.com/AllexandreMZ/status/1305555590001946624" type="text/html"/>
            <content type="html">&lt;div&gt;&lt;blockquote class="twitter-tweet"&gt;&lt;p lang="pt" dir="ltr"&gt;Cerca de 700 jovens prestaram juramento hoje na Manhiça para o curso militar que arrancou em abril. Iniciou com mais de 800, mas outros desistiram. A cerimónia do encerramento foi secreta. Cerca de 200 deverão ir a &lt;a href="https://twitter.com/hashtag/CaboDelgado?src=hash&amp;ref_src=twsrc%5Etfw"&gt;#CaboDelgado&lt;/a&gt; enquanto outros às especialidades (artilharia etc).. &lt;a href="https://t.co/0QmZ2rWF6g"&gt;pic.twitter.com/0QmZ2rWF6g&lt;/a&gt;&lt;/p&gt;— Alexandre (@AllexandreMZ) &lt;a href="https://twitter.com/AllexandreMZ/status/1305555590001946624?ref_src=twsrc%5Etfw"&gt;September 14, 2020&lt;/a&gt;&lt;/blockquote&gt;
    &lt;/div&gt;</content>
            <author>
                <name>Alexandre</name>
            </author>
        </entry>
        <entry>
            <id>tag:feedly.com,2013:cloud/entry/tCS+2m1OpGdjXiXxCw+JFMvBfkRWtIxNSz4wk+LTxZw=_17497c9699c:36480c:7eb3ca0e</id>
            <title type="html">Mozambique: Defence Minister claims makers of videos identified</title>
            <published>2020-09-16T16:39:53Z</published>
            <updated>2020-09-16T16:40:09Z</updated>
            <link rel="alternate" href="https://clubofmozambique.com/news/mozambique-defence-minister-claims-makers-of-videos-identified-171630/" type="text/html"/>
            <summary type="html">Mozambican Defence Minister Jaime Neto claimed on Wednesday that some of those involved in producing videos which supposedly show the Mozambican defence and security forces committing atrocities have been identified, and he promised that action will be taken against them.
    Neto was speaking the da</summary>
            <content type="html">&lt;div&gt;&lt;div&gt;&lt;div&gt;&lt;figcaption&gt;&lt;p&gt;Mozambican Defence Minister Jaime Neto claimed on Wednesday that some of those involved in producing videos which supposedly show the Mozambican defence and security forces committing atrocities have been identified, and he promised that action will be taken against them.&lt;/p&gt;
    &lt;p&gt;Neto was speaking the day after Interior Minister Amade Miquidade had announced that the government is investigating the origin of the videos. He said the government wants to find “where the nucleus is that is making these videos”.&lt;/p&gt;
    &lt;p&gt;Several videos have circulated in recent days claiming to show Mozambican troops committing torture, summary execution and other human rights abuses. The human rights organisation Amnesty International publicised some of them, and called for an investigation.&lt;/p&gt;
    &lt;p&gt;Several Mozambican organisations, including the National Human Rights Commission (CNDH), and the Mozambican Bar Association (OAM), have also called for a full inquiry.&lt;/p&gt;
    &lt;p&gt;The government, however, believes the videos are fakes, shot in order to denigrate the defence and security forces.&lt;/p&gt;
    &lt;p&gt;Speaking after he had launched a week of commemorations of the anniversary of the start of the independence war, on 25 September 1964, Neto said investigations into the videos are under way.&lt;/p&gt;
    &lt;p&gt;“Some Mozambicans make and assemble these images and send them abroad”, he accused. “We know who they are. We shall expose them one day, and we shall pick them up because they are attacking the Mozambican nation”.&lt;/p&gt;
    &lt;p&gt;Neto said the main challenge the defence and security forces face is to resist the attacks by islamist terrorists in the northern province of Cabo Delgado. Since the first terrorist raids, in October 2017, hundreds of people have died, and around 200,000 have been displaced from their homes.&lt;/p&gt;
    &lt;p&gt;“The challenge we face is to combat and eliminate terrorism”, said Neto. “The men and women on the battle field are making all manner of sacrifices to overcome the challenges. We are under attack from forces whose intentions we do not know, but we are determined to defeat terrorism”.&lt;/p&gt;
    &lt;p&gt; &lt;/p&gt;
    &lt;strong&gt;Source: &lt;/strong&gt;AIM    &lt;/figcaption&gt;&lt;/div&gt;&lt;/div&gt;&lt;/div&gt;</content>
            <author>
                <name>mozambique</name>
            </author>
            <media:content medium="image" url="https://clubofmozambique.com/wp-content/uploads/2020/09/jaimeneto.tvm_.jpg"/>
        </entry>
    </feed>
'''
ATOM_FEED_MOCK_DATA_LAMBDA_RESPONSE_EXISTING_SOURCES = [
    {"url": "https://www.bbc.com/news/world-africa-54179776", "status": "success"},
    {"url": "https://www.cnn.com/2020/09/16/africa/amnesty-mozambique-video-killing-investigation-intl/index.html", "status": "success"},
    {"url": "https://cjimoz.org/news/mocimboa-da-praia-e-o-distrito-epicentro-de-recrutamento-de-jovens-pelos-terroristas/", "status": "success"},
    {"url": "https://twitter.com/AllexandreMZ/status/1305555590001946624", "status": "failure"},
    {"url": "https://clubofmozambique.com/news/mozambique-defence-minister-claims-makers-of-videos-identified-171630/", "status": "success"},
]

# -----------------------------------------------  RSS FEED -----------------------------------------------
RSS_FEED_MOCK_DATA = '''<?xml version="1.0" encoding="utf-8" ?>
<rss version="2.0"
    xmlns:atom="http://www.w3.org/2005/Atom"
    xmlns:media="http://search.yahoo.com/mrss/">
    <channel>
        <title>ReliefWeb - Updates</title>
        <description>ReliefWeb - Updates</description>
        <link>https://reliefweb.int</link>
        <atom:link rel="self" href="https://reliefweb.int/updates/rss.xml?legacy-river=country/ukr" />
        <image>
            <url>https://reliefweb.int/profiles/reliefweb/themes/kobe/images/ReliefWeb_RSS_logo.png</url>
            <title>ReliefWeb - Updates</title>
            <link>https://reliefweb.int</link>
            <width>256</width>
            <height>256</height>
        </image>
        <language>en</language>
        <copyright>You should respect the intellectual property rights of the original source. Please contact the source directly if you want to re-use their content.</copyright>
        <pubDate>Thu, 17 Sep 2020 07:24:25 +0000</pubDate>
        <lastBuildDate>Thu, 17 Sep 2020 07:24:25 +0000</lastBuildDate>
        <item>
            <title>Ukraine: DRC / DDG Legal Alert: Issue 55 - August 2020 [EN/RU/UK]</title>
            <link>https://reliefweb.int/report/ukraine/ukraine-drc-ddg-legal-alert-issue-55-august-2020-enruuk</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/ukraine-drc-ddg-legal-alert-issue-55-august-2020-enruuk</guid>
            <pubDate>Thu, 17 Sep 2020 07:24:25 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Sources: Danish Refugee Council, Danish Demining Group</div><p><img src="https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535808-08_2020_drc-ddg_legal_alert_eng.png" alt=""></p><p>Please refer to the attached files.</p><p><strong>1. COVID-19 Legislative Measures: A Shift from Easing Quarantine Measures to Reinforcing Them</strong></p><p>In August 2020, the Ukrainian government switched from easing the quarantine measures to once again reinforcing them. In relation to the humanitarian context, the main updates include:</p><ul><li><p>Adaptive2 quarantine is prolonged until 31 October 2020. Range of the restrictive measures depends on the regional quarantine regime (green, yellow, orange or red) which is decided on the basis of certain indicators by the regional Commissions on Technogenic and Environmental Safety and Emergency Situations. Latest information on the quarantine regime in particular regions is available on the governmental website;</p></li><li><p>Self-isolation/Observation after crossing EECPs or the state border: On 27 August 2020, the Cabinet issued Resolution No. 757 renewing the requirement for self-isolation (if not possible &ndash; observation) for individuals crossing EECPs in NGCA and Crimea in the direction of GCA (exceptions are provided for children under 12 years old, staff of international and diplomatic organisations, if negative COVID-test is obtained, and in some other cases). In regards to EECPs in Luhansk and Donetsk regions, however, the situation did not change as despite the cancellation of the self-isolation requirement in July 2020, the JFO Commander continued to enforce it.3 The self-isolation requirement is also applied to the citizens arriving back to Ukraine from the countries included to the high-risk list &ndash; however, the requirement does not apply if the person is tested negative for COVID.</p></li><li><p>Movement through EECPs with Crimea has been restricted from 9 August through 27 August with the exception of allowing movement of Ukrainian citizens mainly based on their residency registration.Other grounds for movement include &lsquo;humanitarian cases&rsquo; (on a case by case basis with the approval of the Head of the State Border Service), movement of staff members of diplomatic and humanitarian missions, and movement of school graduates applying to Ukrainian universities. Movement to mainland Ukraine is mostly conditioned on undergoing a 14-day-long self-isolation;</p></li><li><p>Movement of non-nationals to Ukraine is once again banned, effective from 28 August 2020 &ndash; with certain exceptions. For instance, entry is allowed for non-nationals who are parents/children/spouse of Ukrainian citizens, possess valid Ukrainian work or residency permits, or work for diplomatic or consulate institutions or accredited international missions (including their family members). Entry is also allowed for non-nationals studying in Ukraine or serving in the Armed Forces, persons arriving for short-term transit purpose, experts invited to Ukraine by national enterprises or the state bodies, cargo drivers, and refugees</p></li></ul>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>Danish Refugee Council</category>
            <category>Danish Demining Group</category>
            <category>Health</category>
            <category>Protection and Human Rights</category>
            <category>News and Press Release</category>
            <category>Epidemic</category>
            <author>Danish Refugee Council</author>
            <author>Danish Demining Group</author>
            <enclosure
        url="https://reliefweb.int/sites/reliefweb.int/files/resources/08_2020_drc-ddg_legal_alert_eng.pdf"
        length="380131"
        type="application/pdf"
      />
        </item>
        <item>
            <title>OSCE Special Monitoring Mission to Ukraine (SMM) Daily Report 221/2020 issued on 16 September 2020</title>
            <link>https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2212020-issued-16-september</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2212020-issued-16-september</guid>
            <pubDate>Wed, 16 Sep 2020 19:05:27 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: Organization for Security and Co-operation in Europe</div><p><img src="https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535774-2020-09-16%20SMM%20Daily%20Report.png" alt=""></p><p>Please refer to the attached file.</p><p><strong>Based on information from the Monitoring Teams as of 19:30 15 September 2020. All times are in Eastern European Summer Time.</strong></p><p><strong><em>Summary</em></strong></p><ul><li><p>The SMM recorded no ceasefire violations in either Donetsk or Luhansk region. In the previous reporting period, it recorded four ceasefire violations in Donetsk and none in Luhansk region.</p></li><li><p>The SMM followed up on reports of a man injured by an explosive object while working in a field in Metalist, Luhansk region.</p></li><li><p>The Mission saw that the power supply to its camera system in Berezove, Donetsk region was disconnected.</p></li><li><p>The Mission continued monitoring the disengagement areas near Stanytsia Luhanska, Zolote and Petrivske. During evening hours, an SMM long-range unmanned aerial vehicle spotted people inside the latter two areas.</p></li><li><p>The Mission facilitated and monitored adherence to localised ceasefires to enable repairs to and the operation of critical civilian infrastructure.</p></li><li><p>The Mission continued following up on the situation of civilians amid the COVID-19 pandemic, including at an entry-exit checkpoint and the corresponding checkpoint of the armed formations in Luhansk region.</p></li><li><p>The SMM monitored a peaceful public gathering in Kyiv in relation to a recent decision made in the Trilateral Contact Group.</p></li><li><p>The SMM&rsquo;s freedom of movement continued to be restricted, including at checkpoints of the armed formations near Korsun and Kreminets, Donetsk region.</p></li></ul>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>Organization for Security and Co-operation in Europe</category>
            <category>Mine Action</category>
            <category>Peacekeeping and Peacebuilding</category>
            <category>Protection and Human Rights</category>
            <category>Situation Report</category>
            <category>Epidemic</category>
            <author>Organization for Security and Co-operation in Europe</author>
            <enclosure
        url="https://reliefweb.int/sites/reliefweb.int/files/resources/2020-09-16%20SMM%20Daily%20Report.pdf"
        length="345744"
        type="application/pdf"
      />
        </item>
        <item>
            <title>Ukraine: Crossing the Contact Line, August 2020 Snapshot [EN/UK]</title>
            <link>https://reliefweb.int/report/ukraine/crossing-contact-line-august-2020-snapshot-enuk</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/crossing-contact-line-august-2020-snapshot-enuk</guid>
            <pubDate>Wed, 16 Sep 2020 09:12:06 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Sources: UN High Commissioner for Refugees, Right to Protection</div><p><img src="https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535661-08_2020_r2p_eecp_report_eng.png" alt=""></p><p>Please refer to the attached Infographic.</p><p>The report is based on the results of a survey conducted by the NGO R2P at the five EECPs to enter the non-government controlled areas (NGCA) and administered on a regular basis since June 2017. The survey is a part of the monitoring of violations of rights of conflict-affected populations within the framework of the project &lsquo;Advocacy, Protection, and Legal Assistance to IDPs&rsquo; implemented by R2P, with the support of UNHCR. The purpose of the survey is to explore reasons and concerns of those traveling from the NGCA to the GCA, as well as conditions and risks associated with crossing the line of contact through EECPs. The information collected in the survey helps identify protection needs, gaps, and trends, and provides an evidentiary basis for advocacy efforts.</p>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>UN High Commissioner for Refugees</category>
            <category>Right to Protection</category>
            <category>Education</category>
            <category>Health</category>
            <category>Protection and Human Rights</category>
            <category>Infographic</category>
            <author>UN High Commissioner for Refugees</author>
            <author>Right to Protection</author>
            <enclosure
        url="https://reliefweb.int/sites/reliefweb.int/files/resources/08_2020_r2p_eecp_report_eng.pdf"
        length="311571"
        type="application/pdf"
      />
        </item>
        <item>
            <title>Ukraine: EU and UNDP supply protective respirators to medical workers in Donetsk Oblast</title>
            <link>https://reliefweb.int/report/ukraine/eu-and-undp-supply-protective-respirators-medical-workers-donetsk-oblast</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/eu-and-undp-supply-protective-respirators-medical-workers-donetsk-oblast</guid>
            <pubDate>Wed, 16 Sep 2020 01:16:56 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: UN Development Programme</div><p><strong>15,000 protective respirators will help medical workers in Donetsk Oblast respond effectively and safely to the COVID-19 pandemic</strong></p><p>Kramatorsk, Donetsk Oblast, September 15, 2020 &ndash; The European Union and the United Nations Development Programme (UNDP) in Ukraine have donated a batch of 15,000 N95 valveless respirators to four medical facilities in Donetsk Oblast to help them respond effectively and safely to the COVID-19 pandemic.</p><p>The personal protective equipment was purchased at a cost of U.S. $50,476 under the UN Recovery and Peacebuilding Programme with financial support from the European Union. This was made possible thanks to the joint efforts of the EU and UN, and the ongoing partnership with European partners to help medical workers combat the pandemic and increase the resilience of medical facilities in eastern Ukraine.</p><p>The N95 respirator is designed to block up to 95% of the smallest aerosol particles and filter out viruses and bacteria. This respirator provides better protection than a surgical mask or homemade protective equipment, as it can filter both large and small air particles.  </p><p>The coordinator of the Local Governance and Decentralisation Reform Component of the UN Recovery and Peacebuilding Programme, Olena Ruditch, noted that the rapid increase in the incidence of COVID-19 is leading to overload in many hospitals in the country, including eastern Ukraine.  </p><p>&ldquo;The proper protection of medical staff is essential to reduce the increase of infectious cases among medics, so we make every effort to ensure that medical institutions in Donetsk and Luhansk oblasts are provided with such protection,&rdquo; Ms. Ruditch added.  </p><p>N95 respirators are designed for single use. However, unlike conventional medical masks, they fit tightly over the face and protect healthcare workers from infectious drops that they may inhale when in contact with patients, or when transporting patients to the medical facilities, or during diagnosis, and while providing subsequent treatment.
Ihor Kiiashko, Head of the Regional Centre for Emergency Care and Disaster Medicine, thanked the international partners for their systematic support in overcoming the consequences of the COVID-19 pandemic and building the capacity of medical institutions.  </p><p>&ldquo;Every day, the Emergency Medical Care and Disaster Medicine Centre receives dozens of calls from patients with fever, including a large percentage of people with COVID-19,&rdquo; Mr. Kiiashko added. &ldquo;The staff of the centre accompanies patients during hospitalization to medical institutions, risking their own health on a daily basis, and the new respirators will help to significantly reduce this danger.&rdquo;</p><p>Four hospitals in the Donetsk Oblast received N95 valveless respirators, namely: Bakhmut Intensive Care Hospital, Kostiantynivka Infectious Diseases Hospital, Myrnohrad Infectious Diseases Hospital and the Emergency Medical Care and Disaster Medicine Centre in Kramatorsk.
A batch of N95 respirators will soon be provided to medical institutions in Luhansk Oblast as well.</p><p><strong>Background</strong></p><p>The United Nations Recovery and Peacebuilding Programme (UN RPP) is being implemented by four United Nations agencies: the United Nations Development Programme (UNDP), the UN Entity for Gender Equality and the Empowerment of Women (UN Women), the United Nations Population Fund (UNFPA) and the Food and Agriculture Organization of the United Nations (FAO).</p><p>Thirteen international partners support the Programme: the European Union (EU), the European Investment Bank (EIB), the U.S. Embassy in Ukraine, and the governments of Canada, Denmark, Germany, Japan, the Netherlands, Norway, Poland, Sweden, Switzerland and the UK.</p><p><strong>Media enquiries</strong></p><p>Maksym Kytsiuk, Communications Associate, the UN Recovery and Peacebuilding Programme, maksym.kytsiuk@undp.org, +380 63 576 1839</p>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>UN Development Programme</category>
            <category>Contributions</category>
            <category>Health</category>
            <category>News and Press Release</category>
            <category>Epidemic</category>
            <author>UN Development Programme</author>
        </item>
        <item>
            <title>OSCE Special Monitoring Mission to Ukraine (SMM) Daily Report 220/2020 issued on 15 September 2020</title>
            <link>https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2202020-issued-15-september</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2202020-issued-15-september</guid>
            <pubDate>Tue, 15 Sep 2020 19:08:14 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: Organization for Security and Co-operation in Europe</div><p><img src="https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535587-2020-09-15%20SMM%20Daily%20Report.png" alt=""></p><p>Please refer to the attached file.</p><p><strong>Summary</strong></p><ul><li><p>The SMM recorded four ceasefire violations in Donetsk region and none in Luhansk region. In the previous 24 hours, it recorded none in Donetsk region and seven in Luhansk region.</p></li><li><p>The Mission continued monitoring the disengagement areas near Stanytsia Luhanska, Zolote and Petrivske. During evening hours, an SMM long-range unmanned aerial vehicle spotted people inside the latter two areas.</p></li><li><p>The Mission facilitated and monitored adherence to localised ceasefires to enable repairs to and the operation of critical civilian infrastructure.</p></li><li><p>The SMM visited two border crossing points in non-government-controlled areas of Luhansk region.</p></li><li><p>The Mission continued following up on the situation of civilians amid the COVID-19 pandemic, including at entry-exit checkpoints and corresponding checkpoints of the armed formations in both Donetsk and Luhansk regions.</p></li><li><p>The SMM&rsquo;s freedom of movement continued to be restricted, including at border crossing points outside government control near Izvaryne and Sievernyi, Luhansk region, and at a checkpoint of the armed formations near Olenivka, Donetsk region.*</p></li></ul>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>Organization for Security and Co-operation in Europe</category>
            <category>Mine Action</category>
            <category>Peacekeeping and Peacebuilding</category>
            <category>Situation Report</category>
            <category>Epidemic</category>
            <author>Organization for Security and Co-operation in Europe</author>
            <enclosure
        url="https://reliefweb.int/sites/reliefweb.int/files/resources/2020-09-15%20SMM%20Daily%20Report.pdf"
        length="820045"
        type="application/pdf"
      />
        </item>
        <item>
            <title>UNICEF Ukraine COVID-19 Flash Report on impact on children: 15 September 2020</title>
            <link>https://reliefweb.int/report/ukraine/unicef-ukraine-covid-19-flash-report-impact-children-15-september-2020</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/unicef-ukraine-covid-19-flash-report-impact-children-15-september-2020</guid>
            <pubDate>Tue, 15 Sep 2020 18:03:39 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: UN Children&#039;s Fund</div><p><img src="https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535583-UNICEF%20Ukraine%20COVID-19%20Flash%20Report%20on%20impact%20on%20children%20-%2015%20September%202020.png" alt=""></p><p>Please refer to the attached file.</p><p><strong>Key Highlights and Advocacy Points</strong></p><ul><li><p>On 1 September, over 95 per cent of the 5 million school-aged children in 14,175 schools resumed their education. UNICEF <a href="https://www.unicef.org/ukraine/en/press-releases/back-school-campaign">is supporting</a> the Ministry of Education and Science (MoES) with an informational campaign to ensure children&rsquo;s safety as they return to school during the pandemic.</p></li><li><p>UNICEF <a href="https://www.unicef.org/ukraine/en/press-releases/unicef-calls-strengthen-protection-schools-eastern-ukraine">is calling on</a> the Government of Ukraine to accelerate implementation of the Safe Schools Declaration. Children and teachers in 3,500 educational facilities are continuing to face daily violence as the conflict in eastern Ukraine enters its seventh year.</p></li><li><p>With the continuing COVID-19 pandemic, UNICEF is expanding awareness communication on basic preventive behaviors, including wearing face masks and social distancing.</p></li><li><p>Following the recent decision to replace &lsquo;baby boxes&rsquo; with monetary support, UNICEF <a href="https://www.unicef.org/ukraine/en/press-releases/unicef-ukraine-calls-government-revamp-baby-box-universal-programme-newborn-children">is encouraging</a> the Government to keep the Baby Box Initiative as critical childcare support for families with children. UNICEF research shows that 80 per cent of parents prefer to receive in-kind support.</p></li><li><p>UNICEF is concerned about the amendments to the National Strategy for Reforming the Institutional Care System that would result in boarding schools being excluded from the de-institutionalization strategy.</p></li></ul><p><strong>Overview of Child Rights</strong></p><p><strong>Child Protection</strong></p><ul><li><p>On 21 August, the Prime Minister introduced a decree with amendments to the National Strategy for Reforming the Institutional Care System for 2017-2026 and to the Resolution &ldquo;On the Procedure for enrolling children for an around-the-clock stay in institutions providing institutional care and upbringing of children.&rdquo; These changes could result in boarding schools being excluded from the de-institutionalization strategy and therefore efforts to find family-based care for over 80-90,000 children would be limited.</p></li><li><p>Further, it is not considering the fact that earlier this year the MoES made a decision to close most of the boarding schools due to the COVID-19 quarantine measures and around 40,000 children were &ldquo;returned&rdquo; to their biological families without prior assessment of the family situation and often with a safety and protection risk to children. In addition, the majority of those children with special education needs due to disability had no further access to online education.</p></li><li><p>UNICEF and partners are continuing to monitor the situation of children in five regions who have been returned from institutions to their families as a result of quarantine restrictions introduced by the Government in response to COVID-19.</p></li><li><p>UNICEF online webinars for social workers and child protection specialists have received over 155,000 views on the social media channels of UNICEF and partners. These webinars provide useful guidance on child protection risks during the pandemic, including on the prevention of child institutionalization as well as the reintegration of children from institutional care back to their families and communities, inclusive education, child safety, and so on.</p></li><li><p>New informational content and materials were produced and distributed to 30,000 social workers on how to use personal protective equipment and talk with families about COVID-19.</p></li><li><p>Over 2,000 social workers and child protection professionals in five regions were provided with personal protective equipment for safe working with families and children.</p></li><li><p>UNICEF is continuing to support the national child rights hotline, which is providing to be in high demand for children, caregivers and parents. During the reporting period, 2,473 beneficiaries received phone consultations, including 80 per cent of girls and women and 52 persons with disabilities. Twenty-four per cent of the calls relate to mental health and psychosocial well-being. Calls related to violence against children remain high at the level of 25 per cent, while 10 per cent are linked to family relationships.</p></li><li><p>With UNICEF assistance, gender-based violence (GBV) mobile teams in eastern Ukraine have provided over 12,000 phone consultations to people in need since the COVID-19 pandemic began. In August alone, GBV teams delivered 3,178 online consultations to people living along the &lsquo;contact line&rsquo;. Nineteen of the calls were from families of children who had returned from boarding institutions and 88 were from persons with disabilities. More than half of all reported cases are related to violence, and 14 per cent are linked to COVID-19.</p></li></ul>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>UN Children&#039;s Fund</category>
            <category>Contributions</category>
            <category>Education</category>
            <category>Food and Nutrition</category>
            <category>Health</category>
            <category>Protection and Human Rights</category>
            <category>Water Sanitation Hygiene</category>
            <category>Situation Report</category>
            <category>Epidemic</category>
            <author>UN Children&#039;s Fund</author>
            <enclosure
        url="https://reliefweb.int/sites/reliefweb.int/files/resources/UNICEF%20Ukraine%20COVID-19%20Flash%20Report%20on%20impact%20on%20children%20-%2015%20September%202020.pdf"
        length="105315"
        type="application/pdf"
      />
        </item>
        <item>
            <title>European Union and WHO deliver over 100 oxygen concentrators for COVID-19 patients in Ukraine [EN/UK]</title>
            <link>https://reliefweb.int/report/ukraine/european-union-and-who-deliver-over-100-oxygen-concentrators-covid-19-patients</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/european-union-and-who-deliver-over-100-oxygen-concentrators-covid-19-patients</guid>
            <pubDate>Tue, 15 Sep 2020 16:00:36 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: World Health Organization</div><p><img src="https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535572-15%20Sept%202020%20Solidarity%20for%20Health%20Initiative_Oxygen%20concentrators%20delivery_Press%20release_UKR.png" alt=""></p><p>Please refer to the attached file.</p><p>The delivery of more than 100 oxygen concentrators, funded by the European Union and procured by WHO arrived in the country. The equipment enables more than 44 frontline hospitals to help patients recover from severe illness due to COVID-19. These supplies cover critical equipment needs of the most COVID-19 affected areas in Ukraine, including such regions as Lviv, Chernivtsi, Kharkiv, Ivano-Frankivsk, and Kyiv and Uman cities.</p><p>The equipment was procured by the WHO Regional Office for Europe, with funding from the EU, through the Solidarity for Health Initiative. The goods are valued at over EUR 78 000. </p><p>Oxygen concentrators are a non-invasive way of providing oxygen to patients hospitalized with COVID-19. Such supplemental oxygen is the first essential step for the treatment of severe COVID-19 patients with low blood oxygen levels and should be a primary focus for treatment. </p><p>After necessary administrative steps by authorities, the oxygen concentrators will be distributed by the WHO Country Office according to the needs of the healthcare facilities identified by the Ministry of Health of Ukraine.</p><p>All the equipment delivered has been checked to ensure it meets quality and safety standards.</p><p>&ldquo;The pandemic is not over. The spread of COVID-19 in Ukraine is alarming and requires coordinated action from all. Through the Solidarity for Health Initiative, the EU and the World Health Organisation are providing emergency assistance to respond to critical medical needs. Thanks to our partnership, we were able to purchase and deliver, despite the worldwide shortage, oxygen concentrators which are essential to treat severely ill COVID-19 patients in 44 hospitals across the entire country. It is now very important to proceed urgently with the clearance of these critical supplies in order to allow frontline hospitals to benefit from them. This is part of the European Union&rsquo;s #TeamEurope approach, in the context of which it is mobilising a COVID-response package of EUR 190 million for Ukraine.&ldquo; Ambassador Matti Maasikas, Head of European Union Delegation to Ukraine said. </p><p>&ldquo;In the context of the Coronavirus crisis, WHO is working to maximize the availability of critical medical supplies to the most vulnerable. We are focused on fulfilling urgent requests and really appreciate that with the Solidarity for Health Initiative project we are making a difference in Ukraine. Delivery of these oxygen concentrators will be crucial in treating the most severely affected patients in the areas with the highest numbers of confirmed cases of COVID-19&ldquo;, underlined WHO Representative in Ukraine Dr. Jarno Habicht.</p><p>&ldquo;In response to the COVID-19 pandemic it is very important not only to respond quickly to all challenges which the health system was facing at the beginning of the crisis, but also to ensure prompt and structured response for later. Increasing the capacity of frontline hospitals in the most COVID-19 affected areas in Ukraine to treat severe cases of COVID-19 is vital as it helps to reduce the burden on health systems and support people who are bravely fighting the virus &ldquo;, added Deputy Minister of Health (MoH) and Chief State Sanitary Doctor of Ukraine Dr. Viktor Liashko.</p><p>In the first phase of the project, a shipment of around one million units of personal protective equipment for 50 COVID-19 dedicated hospitals and essential supplies for 27 COVID-19 laboratories were procured and delivered.</p><p>The provision of these critical supplies is part of the European Union&rsquo;s response to the COVID-19 pandemic, currently affecting more than 216 countries and territories. The total COVID-19 response package from the EU for Ukraine is EUR 190 million. The funds are being used for emergency needs in healthcare, longer-term strengthening of the health sector, as well as socioeconomic recovery. Ukraine is also set to benefit from a special Macro-Financial Assistance worth EUR 1.2 billion.</p><p>The project builds upon the European Union&rsquo;s and WHO&rsquo;s ongoing support to Ukraine.</p><p><strong>Background information:</strong></p><p>&ldquo;Solidarity for Health Initiative&rdquo; is a joint effort of the European Union and WHO Regional Office for Europe in six countries of Eastern Europe and the Caucasus &ndash; Armenia, Azerbaijan, Belarus, Georgia, the Republic of Moldova, and Ukraine. The project is aimed to help prevent, detect and respond to the COVID-19 pandemic and strengthen the EU&rsquo;s Eastern Neighbourhood&rsquo;s capacity to respond to public health emergencies. The project is implemented by the WHO Regional Office for Europe and WHO country offices, in close coordination with EU Delegations, national authorities and development partners, including those in the United Nations system.</p><p>The role of the WHO Country Office in Ukraine is to support the country in creating and strengthening policies for sustainable health development. This includes providing technical guidance in public health-related issues, supporting the development of standards and guidelines, building up local relationships for efficient technical cooperation, and ensuring that public health measures are coordinated and in place during crises.</p><p>Currently, the Country Office in Ukraine is focusing its work on COVID-19 response and cooperation with the health authorities and other institutions involved in the country-level coordination, planning, and monitoring, case investigation, infection prevention and control. WHO has been supporting improving the national and regional capacities to diagnose COVID-19 via the national laboratory system, and also improving clinical standards and approaches in the country.</p><p>For additional information, please contact: Dolhova Tetiana, Communication Officer dolhovat@who.int</p>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>World Health Organization</category>
            <category>Health</category>
            <category>News and Press Release</category>
            <category>Epidemic</category>
            <author>World Health Organization</author>
            <enclosure
        url="https://reliefweb.int/sites/reliefweb.int/files/resources/15%20Sept%202020%20Solidarity%20for%20Health%20Initiative_Oxygen%20concentrators%20delivery_Press%20release_UKR.pdf"
        length="319107"
        type="application/pdf"
      />
        </item>
        <item>
            <title>Ukraine: Weekly Update from the OSCE Observer Mission at Russian Checkpoints Gukovo and Donetsk based on information as of 15 September 2020</title>
            <link>https://reliefweb.int/report/ukraine/weekly-update-osce-observer-mission-russian-checkpoints-gukovo-and-donetsk-based-271</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/weekly-update-osce-observer-mission-russian-checkpoints-gukovo-and-donetsk-based-271</guid>
            <pubDate>Tue, 15 Sep 2020 15:30:23 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: Organization for Security and Co-operation in Europe</div><p><strong>SUMMARY</strong></p><p><em>Kamensk-Shakhtinskiy, Russian Federation. The Observer Mission (OM) continues to operate 24/7 at both Border Crossing Points (BCPs). The overall number of border crossings by persons increased at both BCPs compared to the previous week.</em></p><p><strong>OPERATIONAL REMARKS</strong></p><p>The OM is currently operating with 22 permanent international Mission members, including the Chief Observer (CO) and one first responder<a href="https://www.osce.org/observer-mission-at-russian-checkpoints-gukovo-and-donetsk/463710#_ftn1">[1]</a>. The Mission is supported administratively by a staff member and the Chief of Fund Administration based in Vienna. In the framework of its vehicle replacement process with the OSCE SMM, on 14 September three new vehicles were delivered to the Mission&rsquo;s Office in Kamensk-Shakhtinskiy.</p><p><strong>Update on COVID-19 measures</strong></p><p>Activities have been impacted by COVID-19 and measures undertaken by the OM to ensure the safety and duty of care of its Mission members and compliance with measures set by the host country authorities. The Mission is continuing to keep the situation under review, in close contact with the OSCE Secretariat and the Chairmanship. Following the host country recommendations, the observers are adhering to social distancing. Due to the preventive measures taken by the central and regional authorities, the OM is faced with certain difficulties, but is still able to continue to fulfil its mandate without any limitations in its observation and reporting activities.</p><p><strong>OBSERVATIONS AT THE BORDER CROSSING POINTS</strong></p><p><strong>Persons crossing the border</strong></p><p>The profile of persons crossing the border can be categorized as follows:</p><ol><li>Adults travelling on foot or by car with little or no luggage.</li><li>Persons in military-style outfits.</li><li>Families (often including elderly persons and/or children) travelling on foot or by car with a significant amount of luggage.</li></ol><p>The average number of entries/exits increased from 9,544 to 10,017 per day at both BCPs compared to last week<a href="https://www.osce.org/observer-mission-at-russian-checkpoints-gukovo-and-donetsk/463710#_ftn2">[2]</a>.</p><p>During the reporting period, the majority of border crossings were to the Russian Federation, with an average net flow of 74 per day for both BCPs. The Donetsk BCP continued to experience much more traffic than the Gukovo BCP.</p><p>Responding to the COVID-19 situation, the host country has closed its borders for the majority of foreigners starting from 18 March. Among the exceptions of persons allowed to cross the border (which entered into force on 19 March), are Ukrainian citizens and stateless persons holding passports or identification documents proving permanent residence in certain areas of Luhansk and Donetsk regions of Ukraine. In addition, reportedly, due to the threat of the spread of COVID-19, starting from 10 April, the organized passenger transport commuting between the non-government-controlled areas of Luhansk region of Ukraine and the Russian Federation was temporarily suspended and restored from 25 June.</p><p><strong>Persons in military-style outfits</strong></p><p>During the reporting period, the number of persons in military style outfits crossing the border was eight, compared to ten last week. Six persons crossed into the Russian Federation while another two crossed into Ukraine. These individuals crossed the border on foot.</p><p><strong>Families with a significant amount of luggage</strong></p><p>The OTs continued to report on families, sometimes with elderly persons and/or children, crossing the border at both BCPs with a significant amount of luggage, or travelling in heavily loaded cars. During this reporting week, two families were observed crossing into the Russian Federation while another three families were observed crossing into Ukraine, compared to the previous reporting period when six families were observed crossing to the Russian Federation, while another two families crossed into Ukraine.</p><p><strong>Bus connections</strong></p><p>Regular local and long-distance bus connections continued to operate between Ukraine (mostly from/to the Luhansk region) and the Russian Federation. During the reporting period, the OTs observed a decrease in the overall number of buses crossing the border at both BCPs (328 compared to 353 observed during the previous week). There were 167 buses bound for the Russian Federation and 161 bound for Ukraine.</p><p>On some occasions, the OTs noticed the bus drivers removing the itinerary signs from the windshields of their buses, while some buses did not display their route at all. The majority of long-distance buses commuting between the Luhansk region and cities in the Russian Federation had Ukrainian licence plates issued in the Luhansk region. Among the bus connections observed by the OT, the following irregular route of destination was noted: Luhansk &ndash; Sevastopol.</p><p><strong>Trucks</strong></p><p>During the reporting period, the OTs observed an increase in the overall number of trucks crossing the border at both BCPs (957 compared to 842 during the previous reporting week); 498 at the Gukovo BCP and 459 at the Donetsk BCP, 537 of these trucks crossed into the Russian Federation and 420 crossed into Ukraine. Most of the trucks observed by the OTs had Ukrainian licence plates issued in the Luhansk region; however, on a daily basis, the OTs also noted trucks registered in the Russian Federation, Belarus, Lithuania, Poland, Ukraine and trucks with &ldquo;LPR&rdquo; plates.</p><p>The OTs also continued to observe tanker trucks crossing the border in both directions. During the reporting period, the OTs observed a slight decrease in the overall number of tanker trucks crossing the border at both BCPs (45 compared to 54 during the previous reporting week). These trucks were observed crossing the border at both BCPs. The trucks had the words &ldquo;Propane&rdquo; and &ldquo;Flammable&rdquo; written across the tanks in either Russian or Ukrainian. The majority of tanker trucks had hazard signs, indicating that they were transporting propane or a mix of propane and butane. All trucks underwent systematic inspection by the Russian Federation officials, which could include an X-ray check. Due to the unfavourable observation position at the Gukovo BCP, the OTs continued to be unable to observe any X-ray checks.</p><p>During the reporting period, the X-ray vehicle at the Donetsk BCP was not operating due to the ongoing construction activities; consequently, no X-ray checks were observed by the OTs.</p><p><strong>Minivans</strong></p><p>The OM continued to observe passenger and cargo minivans<a href="https://www.osce.org/observer-mission-at-russian-checkpoints-gukovo-and-donetsk/463710#_ftn3">[3]</a> crossing the border in both directions at both BCPs. The OTs observed minivans predominantly with Ukrainian licence plates issued in the Luhansk region; however, the OTs also saw minivans registered in the Russian Federation. During the reporting period, the OTs observed an increase in the overall number of minivans crossing the border at both BCPs (161 compared to 128 observed during the previous week); 78 crossed into the Russian Federation and another 83 into Ukraine.</p><p><strong>Trains</strong></p><p>The OTs continued to pick up the sound of trains on the railway tracks located approximately 150m south-west of the Gukovo BCP. During the reporting week, the OTs heard trains on 24  occasions; the OTs assessed that 12 trains were travelling to the Russian Federation and the remaining 12 trains were travelling to Ukraine (more details are provided in the sections &ldquo;trends and figures at a glance&rdquo; below).</p><p>Visual observation was not possible because of the line of trees located between the train tracks and the BCP.</p><p><strong>Other observations</strong></p><p>The majority of vehicles crossing the border had Ukrainian licence plates issued in the Luhansk region or Russian Federation licence plates. A significant number of vehicles with &ldquo;LPR&rdquo; plates were also observed crossing the border in both directions on a daily basis. The OTs also observed cars with licence plates registered in Georgia.</p><p>On 8 September at 15:05, the OT at the Donetsk BCP observed a group of 17 brand-new ambulance vehicles type UAZ, with no licence plates, entering the BCP from the Russian Federation and queuing at the customs control area. All vehicles underwent customs control procedures and left for Ukraine at 17:20.</p><p>On 9 September at 20:28, the OT at the Donetsk BCP observed a police minivan with Russian Federation licence plates and two police officers inside, entering the BCP from the Russian Federation and parking next to the main building. At 20:35, the police vehicle drove back to the Russian Federation.</p><p>On 14 September at 13:31, the OT at the Donetsk BCP observed an ambulance with Russian Federation licence plates, entering the BCP from the Russian Federation and parking next to the main building. The OT noticed three individuals on board &ndash; the driver and two medical personnel. At 13:56, the ambulance drove back to the Russian Federation. The OT was unable to notice any other details from its position.</p><p><strong>For trends and figures at a glance covering the period from 11 August to 15 September 2020, please see <a href="https://www.osce.org/files/2020-09-15%20OM%20Weekly%20Update.pdf">the attachment here</a></strong></p><p><a href="https://www.osce.org/observer-mission-at-russian-checkpoints-gukovo-and-donetsk/463710#_ftnref1">[1]</a> First responders are OSCE staff or Mission members deployed for a short period of time.</p><p><a href="https://www.osce.org/observer-mission-at-russian-checkpoints-gukovo-and-donetsk/463710#_ftnref2">[2]</a>Based on data received from the Regional Representation of the Ministry of Foreign Affairs of the Russian Federation.</p><p><a href="https://www.osce.org/observer-mission-at-russian-checkpoints-gukovo-and-donetsk/463710#_ftnref3">[3]</a> Cargo minivans: light commercial vehicles with a maximum authorized mass of more than 3.5 t and not more than 7.5 t; with or without a trailer with a maximum mass of less than 750 kg (small cargo vehicles which correspond to driving licence C1).</p>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>Organization for Security and Co-operation in Europe</category>
            <category>Health</category>
            <category>Protection and Human Rights</category>
            <category>News and Press Release</category>
            <category>Epidemic</category>
            <author>Organization for Security and Co-operation in Europe</author>
        </item>
        <item>
            <title>Ukraine Legislative Update: August 2020 [EN/UK]</title>
            <link>https://reliefweb.int/report/ukraine/ukraine-legislative-update-august-2020-enuk</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/ukraine-legislative-update-august-2020-enuk</guid>
            <pubDate>Tue, 15 Sep 2020 14:21:10 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: UN High Commissioner for Refugees</div><p><img src="https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535550-Ukraine%20Legislative%20Update%20-%20August%202020%20%5BEN%5D.png" alt=""></p><p>Please refer to the attached files.</p><p><strong>Adopted Legislation</strong></p><ul><li>Freedom of movement during the COVID-19 outbreak in Ukraine</li></ul><p><strong>Draft Legislation</strong></p><ul><li>Enhancing administrative liability for domestic and gender-based violence </li><li>Draft law on book-shaped passports for Ukrainian citizens</li></ul><p><strong>Other developments</strong></p><ul><li>Subventions to local budgets </li><li>Non-holding of local elections in amalgamated territorial communities of the Donetsk and Luhansk oblasts </li><li>Kyiv municipal affordable housing program</li></ul>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>UN High Commissioner for Refugees</category>
            <category>Health</category>
            <category>Protection and Human Rights</category>
            <category>Situation Report</category>
            <category>Epidemic</category>
            <author>UN High Commissioner for Refugees</author>
            <enclosure
        url="https://reliefweb.int/sites/reliefweb.int/files/resources/Ukraine%20Legislative%20Update%20-%20August%202020%20%5BEN%5D.pdf"
        length="181759"
        type="application/pdf"
      />
        </item>
        <item>
            <title>New Homes Planned for Ukraine’s Displaced</title>
            <link>https://reliefweb.int/report/ukraine/new-homes-planned-ukraine-s-displaced</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/new-homes-planned-ukraine-s-displaced</guid>
            <pubDate>Tue, 15 Sep 2020 11:16:36 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: International Organization for Migration</div><p><strong>Kyiv</strong> - On Tuesday (15/09), the International Organization for Migration (IOM) is announcing details of a new project to provide modern and affordable housing to over 1,500 people in Ukraine's conflict-affected east. These apartments and houses will be located in the towns of Kramatorsk (Donetsk Region) and Sievierodonetsk (Luhansk Region). They will shelter 500 families. </p><p>Over the six years of protracted displacement in the country, caused by the conflict which erupted in 2014, IOM has recorded thousands of cases of displaced individuals and families for whom safe housing remains a pressing need.  The latest IOM survey, conducted between April and June this year, revealed that only 11 per cent of internally displaced persons (IDPs) in Ukraine own their homes. </p><p>The EUR 22.1 million, five-year project, funded by the Government of Germany through <a href="https://www.kfw-entwicklungsbank.de/International-financing/KfW-Development-Bank/Tasks-and-goals/">KfW Development Bank</a>, envisages both new construction and renovation of existing housing units, work to be implemented by IOM in cooperation with the Government of Ukraine and municipal authorities. </p><p>The housing units will require affordable rent payments from the beneficiaries, who will also pay their own utility bills. High standards for construction---including energy efficiency and environment protection---will be featured. </p><p>Eighty per cent of the new residents will be IDPs and 20 per cent will be from the original population of Kramatorsk and Sievierodonetsk. The towns were selected for the project due to high influx of IDPs --50,000 and 40,000 respectively -- representing about one third of the pre-conflict population of each city. </p><p>"When we fled our home, a priest gave us a village house for free. But another 16 people already lived there. It was basically a hut with just one table, one oven and one bathtub. I was already pregnant with my second child, and we lived in the hallway, where there no place to put the second crib. So, we moved to a flat, the cheapest one we could find, which the wind blew right through," explained one displaced woman from Luhansk Region, eastern Ukraine, who shared her story in an anonymous IOM survey. </p><p>"If we want to work towards a dignified and prosperous future for conflict-affected communities, we must complement our relief and recovery support with interventions that stem from our deep understanding of the long-term impact of protracted displacement," said Anh Nguyen, Chief of Mission at IOM Ukraine. </p><p>"Not only will these new apartment buildings provide homes for the needy, the initiative also represents a significant boost to urban development of Kramatorsk and Sievierodonetsk and a positive socio-economic signal for the entire region," he added. </p><p>As many as 60 per cent of displaced people live in rented accommodation, and 17 per cent stay with relatives or host families. </p><p>IOM has been working in Ukraine since 1996 and has scaled up its response since 2014. It has assisted over 514,000 vulnerable IDPs and people in need in 24 regions of Ukraine, providing them with humanitarian aid, livelihood grants, and opportunities for community development and social cohesion. </p><p>For more information please contact Varvara Zhluktenko at IOM Ukraine, Tel: + 38 044 568 50 15, +38 067 447 97 92, Email: <em>vzhluktenko@iom.int</em></p>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>International Organization for Migration</category>
            <category>Protection and Human Rights</category>
            <category>Shelter and Non-Food Items</category>
            <category>News and Press Release</category>
            <author>International Organization for Migration</author>
        </item>
        <item>
            <title>OSCE Special Monitoring Mission to Ukraine (SMM) Daily Report 219/2020 issued on 14 September 2020</title>
            <link>https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2192020-issued-14-september</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2192020-issued-14-september</guid>
            <pubDate>Mon, 14 Sep 2020 17:07:53 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: Organization for Security and Co-operation in Europe</div><p><img src="https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535452-2020-09-14%20SMM%20Daily%20Report.png" alt=""></p><p>Please refer to the attached file.</p><p><strong>Based on information from the Monitoring Teams as of 19:30 13 September 2020. All times are in Eastern European Summer Time.</strong></p><p><strong>Summary</strong></p><p>&bull; Between the evenings of 11 and 12 September, the SMM recorded no ceasefire violations in Donetsk region and 12 in Luhansk region. In the previous reporting period, it recorded seven ceasefire violations in Donetsk region and one in Luhansk region.</p><p>&bull; Between the evenings of 12 and 13 September, the Mission recorded no ceasefire violations in Donetsk region and seven in Luhansk region.</p><p>&bull; The Mission continued monitoring the disengagement areas near Stanytsia Luhanska,<br>
Zolote and Petrivske. During evening hours, an SMM long-range unmanned aerial vehicle spotted people inside the latter two areas.</p><p>&bull; The SMM spotted a new trench and a trench extension in Donetsk region, assessed as belonging to the Ukrainian Armed Forces, as well as a new trench in Luhansk region and new trenches and upgrades to an existing position in Donetsk region, assessed as belonging to the armed formations.</p><p>&bull; The Mission facilitated and monitored adherence to localised ceasefires to enable repairs to and the operation of critical civilian infrastructure.</p><p>&bull; The SMM visited five border crossing points in non-government-controlled areas of Donetsk and Luhansk regions.</p><p>&bull; The Mission continued following up on the situation of civilians amid the COVID-19 pandemic, including at an entry-exit checkpoint and corresponding checkpoint of the armed formations in Luhansk region.</p><p>&bull; The Mission monitored a peaceful gathering in Lviv.</p><p>&bull; The SMM&rsquo;s freedom of movement continued to be restricted, including at border crossing points outside government control near Izvaryne and Voznesenivka (formerly Chervonopartyzansk) in Luhansk region and at checkpoints of the armed formations near Staromykhailivka and Novoazovsk in Donetsk region.</p>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>Organization for Security and Co-operation in Europe</category>
            <category>Mine Action</category>
            <category>Peacekeeping and Peacebuilding</category>
            <category>Situation Report</category>
            <category>Epidemic</category>
            <author>Organization for Security and Co-operation in Europe</author>
            <enclosure
        url="https://reliefweb.int/sites/reliefweb.int/files/resources/2020-09-14%20SMM%20Daily%20Report.pdf"
        length="970249"
        type="application/pdf"
      />
        </item>
        <item>
            <title>International recommendations and Ukrainian legislation on hygiene-related IPC at Health Facilities in Ukraine during the COVID-19 outbreak [EN/UK]</title>
            <link>https://reliefweb.int/report/ukraine/international-recommendations-and-ukrainian-legislation-hygiene-related-ipc-health</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/international-recommendations-and-ukrainian-legislation-hygiene-related-ipc-health</guid>
            <pubDate>Mon, 14 Sep 2020 14:18:23 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Sources: UN Children&#039;s Fund, WASH Cluster</div><p><img src="https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535424-2020-09-08_wash_and_ipc_in_health_faculities_in_ukraine_during_covid-19_eng.png" alt=""></p><p>Please refer to the attached files.</p><p><strong>Introduction</strong></p><p>An assessment of Health Hacilities in the eastern conflict area of Ukraine (REACH, April 2020) found that 60% of facilities put infectious waste into normal garbage disposal systems, including 6 of 18 designated COVID-19 hospitals on Donetsk and Luhansk Oblasts. It found that 72% of facilities reported limited access to hand sanitizer with 11% having no stock at all. 29% of facilities reported problems with their source of drinking water. 55% of health facilities did not have paper towels at all, including 12 out of 18 designated COVID-19 hospitals. When taken together, the data emphasizes that improvements to water sanitation and hygiene conditions at health facilities throughout Ukraine, could make a significant impact in improving Infection Prevention and Control (IPC) within health facilities. These guidelines aim to help international and local agencies to support local authorities in improving hygiene and IPC, at health facilities, by combining international recommendations and good practice with standards recommended in Ukrainian law. The document should be read in conjunction with &ldquo;Key Actions&rdquo; identified in the WASH and Infection Prevention and Control in Health Care Facilities, Guidance Note <a href="https://washcluster.net/covid-19/wash-and-infection-prevention-and-control-health-care-facilities-23-march-2020-eng-fr-sp">(UNICEF, 2020)</a></p>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>UN Children&#039;s Fund</category>
            <category>WASH Cluster</category>
            <category>Health</category>
            <category>Water Sanitation Hygiene</category>
            <category>Manual and Guideline</category>
            <category>Epidemic</category>
            <author>UN Children&#039;s Fund</author>
            <author>WASH Cluster</author>
            <enclosure
        url="https://reliefweb.int/sites/reliefweb.int/files/resources/2020-09-08_wash_and_ipc_in_health_faculities_in_ukraine_during_covid-19_eng.pdf"
        length="312629"
        type="application/pdf"
      />
        </item>
        <item>
            <title>OSCE Special Monitoring Mission to Ukraine (SMM) Daily Report 218/2020 issued on 12 September 2020</title>
            <link>https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2182020-issued-12-september</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2182020-issued-12-september</guid>
            <pubDate>Sat, 12 Sep 2020 20:27:33 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: Organization for Security and Co-operation in Europe</div><p><img src="https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535253-OSCE%20Special%20Monitoring%20Mission%20to%20Ukraine%20%28SMM%29%20Daily%20Report%20218-2020%20issued%20on%2012%20September%202020.png" alt=""></p><p>Please refer to the attached file.</p><p><strong>Based on information from the Monitoring Teams as of 19:30 11 September 2020. All times are in Eastern European Summer Time.</strong></p><p><strong>Summary</strong></p><ul><li>The SMM recorded seven ceasefire violations in Donetsk region and one in Luhansk region. In the previous reporting period, it recorded five ceasefire violations in Donetsk region and none in Luhansk region. </li><li>The Mission followed up on reports of four people injured on four separate occasions due to explosion of objects, all in non-government-controlled areas Luhansk region. </li><li>Small-arms fire was assessed as aimed at an SMM mini-unmanned aerial vehicle (UAV) flying in areas south-east of Hranitne, Donetsk region.</li><li>The Mission continued monitoring the disengagement areas near Stanytsia Luhanska, Zolote and Petrivske. During evening hours, an SMM long-range UAV spotted people inside the latter two areas. </li><li>The SMM saw for the first time one trench extension in Donetsk region, assessed belonging to Ukrainian Armed Forces, as well as two trench extensions in Luhansk region, assessed as belonging to the armed formations. </li><li>The SMM facilitated and monitored adherence to localised ceasefires to enable repairs to and the operation of critical civilian infrastructure. </li><li>The Mission visited a border crossing point and monitored areas close to the border with the Russian Federation in non-government-controlled areas of Donetsk region. </li><li>The Mission continued following up on the situation of civilians amid the COVID-19 outbreak, including at an entry-exit checkpoint in Luhansk region. </li><li>The SMM monitored public gatherings in Kyiv and Kharkiv related to a recent Trilateral Contact Group decision. </li><li>The SMM&rsquo;s freedom of movement continued to be restricted, including at the checkpoint of the armed formations near Olenivka, Donetsk region.</li></ul>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>Organization for Security and Co-operation in Europe</category>
            <category>Mine Action</category>
            <category>Peacekeeping and Peacebuilding</category>
            <category>Protection and Human Rights</category>
            <category>Situation Report</category>
            <category>Epidemic</category>
            <author>Organization for Security and Co-operation in Europe</author>
            <enclosure
        url="https://reliefweb.int/sites/reliefweb.int/files/resources/OSCE%20Special%20Monitoring%20Mission%20to%20Ukraine%20%28SMM%29%20Daily%20Report%20218-2020%20issued%20on%2012%20September%202020.pdf"
        length="822252"
        type="application/pdf"
      />
        </item>
        <item>
            <title>OSCE Special Monitoring Mission to Ukraine (SMM) Daily Report 217/2020 issued on 11 September 2020</title>
            <link>https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2172020-issued-11-september</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2172020-issued-11-september</guid>
            <pubDate>Fri, 11 Sep 2020 19:41:25 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: Organization for Security and Co-operation in Europe</div><p><img src="https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535196-2020-09-11%20Daily%20Report_ENG.png" alt=""></p><p>Please refer to the attached file.</p><p><strong>Summary</strong></p><p>&bull; The SMM recorded five ceasefire violations in Donetsk region and none in Luhansk region. In the previous reporting period, it recorded no ceasefire violations in either Donetsk or Luhansk region.</p><p>&bull; The Mission continued monitoring the disengagement areas near Stanytsia Luhanska, Zolote and Petrivske. During evening hours, an SMM long-range unmanned aerial vehicle (UAV) spotted people inside the disengagement area near Petrivske.</p><p>&bull; The SMM lost spatial control of its mini-UAV, due to signal interference, while flying over areas near Shumy, Donetsk region.</p><p>&bull; The Mission saw weapons in violation of withdrawal lines in government-controlled areas of Donetsk region and in non-government-controlled areas of Donetsk and Luhansk regions, including in training areas.</p><p>&bull; The SMM facilitated and monitored adherence to localised ceasefires to enable repairs to and the operation of critical civilian infrastructure.</p><p>&bull; The Mission continued following up on the situation of civilians amid the COVID-19 outbreak, including at the entry-exit checkpoints in Donetsk and Luhansk regions, and the corresponding checkpoint of the armed formations in Luhansk region.</p><p>&bull; The SMM monitored a peaceful gathering in Kyiv.</p><p>&bull; The SMM&rsquo;s freedom of movement continued to be restricted.*</p>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>Organization for Security and Co-operation in Europe</category>
            <category>Mine Action</category>
            <category>Peacekeeping and Peacebuilding</category>
            <category>Situation Report</category>
            <category>Epidemic</category>
            <author>Organization for Security and Co-operation in Europe</author>
            <enclosure
        url="https://reliefweb.int/sites/reliefweb.int/files/resources/2020-09-11%20Daily%20Report_ENG.pdf"
        length="786627"
        type="application/pdf"
      />
        </item>
        <item>
            <title>Ukraine: UNHCR delivered 92 tons of humanitarian aid to Luhansk</title>
            <link>https://reliefweb.int/report/ukraine/unhcr-delivered-92-tons-humanitarian-aid-luhansk</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/unhcr-delivered-92-tons-humanitarian-aid-luhansk</guid>
            <pubDate>Fri, 11 Sep 2020 09:50:41 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: UN High Commissioner for Refugees</div><p>The humanitarian cargo will provide much needed help and assistance to the conflict affected population</p><p>On September 10, the UNHCR humanitarian convoy arrived in Luhansk. This is the first such convoy of magnitude to be crossing after the quarantine measures, when almost all movement through the &ldquo;contact line&rdquo;, including restricting movement of humanitarian convoys, was stopped to control the spread of COVID-19.</p><p>The UNHCR convoy of 10 trucks contains timber and construction materials with a total weight of 92,000 kg, destined to the shelter activities for people affected by the conflict in Luhanska oblast.</p><p><em>&ldquo;This convoy carries construction materials destined to our shelter activities in Luhansk through Donetsk represents an example of effective cooperation among several parties.  The humanitarian cargo will provide much needed help and assistance to the civilian population affected by the conflict on both sides of the contact line.  We thank all stakeholders involved in the logistical arrangements, facilitation and transit of the convoy. We count on all parties to continue such successful collaboration on humanitarian matters in future&rdquo;, commented Giorgi Sanikidze, Head of UNHCR Sub Office in Sloviansk.</em></p><p>Since 2018, UNHCR has been the co-leading agency in Logistics Sectoral Working Group and facilitated all convoys to NGCA for UN agencies and international NGOs. During 2020, more than 600,000 kg of goods were delivered for displaced and conflict affected persons on the non-government controlled areas, including through the pedestrian Stanitsia Luhanska Entry-Exit Checkpoint.</p>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>UN High Commissioner for Refugees</category>
            <category>Shelter and Non-Food Items</category>
            <category>News and Press Release</category>
            <author>UN High Commissioner for Refugees</author>
        </item>
        <item>
            <title>The first generation of children raised during the conflict in eastern Ukraine begin their first school year: “My children have never seen a peaceful sky”</title>
            <link>https://reliefweb.int/report/ukraine/first-generation-children-raised-during-conflict-eastern-ukraine-begin-their-first</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/first-generation-children-raised-during-conflict-eastern-ukraine-begin-their-first</guid>
            <pubDate>Thu, 10 Sep 2020 17:16:27 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: International Committee of the Red Cross</div><p>On the International Day to Protect Education from Attack, the International Committee of the Red Cross (ICRC) presents accounts of children, born in the first year of the conflict in eastern Ukraine and of their parents about their respective expectations from the first year of school: &ldquo;My children have never seen a peaceful sky&rdquo;.
The children&rsquo;s everyday life, their daily roundabouts and school expectations are shown in 59 photos made in different towns and villages along the conflict&rsquo;s contact line in the Donbas.</p><p>Many schools, kindergartens and other educational institutions in eastern Ukraine have been affected by the armed conflict; some of them directly damaged by shelling and shooting. Even nowadays, more than six years into the conflict, educational institutions continue being directly affected by hostilities. For many children, the daily walk to school can be dangerous, and in some cases the education process in schools situated on the very line of contact is interrupted by armed hostilities.</p><p>Within the broader Access to Education Framework, the ICRC delegation in Ukraine is using a multidisciplinary approach to address the situation of people affected by the conflict in the Donbas, and tries to improve safety of schools and kindergartens, thus contributing to the creation of a child-friendly atmosphere and safe environment. The ICRC&rsquo;s Safer Access to Education program also aims to increase risk awareness among children, their teachers and parents, to improve evacuation procedures, and to reinforce their resilience.</p><p>Key activities include safe behavior development, providing a safe environment for children and the wider school community and helping them cope with the effects of the conflict: mine risk awareness sessions, psychosocial support and training sessions for teachers, distribution of educational and child development materials, anti-blast protective measures, repair/rehabilitation of educational infrastructure, enhancement of school kitchen facilities, creation of safe play spaces, provision of play and sports equipment, equipping of school basements/improvised shelters and provision of first aid training and kits.</p><p>Since 2015, this ICRC program has been extended to hundreds of educational institutions along the 450-km long conflict&rsquo;s contact line in the Donbas.</p><p><a href="http://ua.icrc.org/2020/09/08/the-first-generation-of-children-raised-during-the-conflict-in-eastern-ukraine-begin-their-first-school-year/">Click here for photo exhibition</a></p>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>International Committee of the Red Cross</category>
            <category>Education</category>
            <category>Mine Action</category>
            <category>Protection and Human Rights</category>
            <category>News and Press Release</category>
            <author>International Committee of the Red Cross</author>
        </item>
        <item>
            <title>OSCE Special Monitoring Mission to Ukraine (SMM) Daily Report 216/2020 issued on 10 September 2020</title>
            <link>https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2162020-issued-10-september</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2162020-issued-10-september</guid>
            <pubDate>Thu, 10 Sep 2020 14:55:14 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: Organization for Security and Co-operation in Europe</div><p><img src="https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1535026-OSCE%20Special%20Monitoring%20Mission%20to%20Ukraine%20%28SMM%29%20Daily%20Report%20216-2020%20issued%20on%2010%20September%202020.png" alt=""></p><p>Please refer to the attached file.</p><p><strong>Summary</strong></p><ul><li>The SMM recorded no ceasefire violations in both Donetsk and Luhansk regions. In the previous reporting period, it recorded one ceasefire violation in Donetsk region and none in Luhansk region.<br></li><li>The Mission continued monitoring the disengagement areas near Stanytsia Luhanska, Zolote and Petrivske. During evening and night hours, an SMM long-range unmanned aerial vehicle spotted people inside the latter two areas.</li><li>The Mission spotted a recent trench extension near Starohnativka, Donetsk region.</li><li>The SMM facilitated and monitored adherence to localised ceasefires to enable repairs to and the operation of critical civilian infrastructure.</li><li>The Mission continued following up on the situation of civilians amid the COVID-19 outbreak, including at the entry-exit checkpoint and the corresponding checkpoint of the armed formations in Luhansk region.</li><li>The SMM&rsquo;s freedom of movement continued to be restricted, including at a border crossing point outside government control near Dovzhanske, Luhansk region.</li></ul>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>Organization for Security and Co-operation in Europe</category>
            <category>Mine Action</category>
            <category>Peacekeeping and Peacebuilding</category>
            <category>Situation Report</category>
            <category>Epidemic</category>
            <author>Organization for Security and Co-operation in Europe</author>
            <enclosure
        url="https://reliefweb.int/sites/reliefweb.int/files/resources/OSCE%20Special%20Monitoring%20Mission%20to%20Ukraine%20%28SMM%29%20Daily%20Report%20216-2020%20issued%20on%2010%20September%202020.pdf"
        length="345092"
        type="application/pdf"
      />
        </item>
        <item>
            <title>OSCE Special Monitoring Mission to Ukraine (SMM) Daily Report 215/2020 issued on 9 September 2020</title>
            <link>https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2152020-issued-9-september</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2152020-issued-9-september</guid>
            <pubDate>Wed, 09 Sep 2020 20:05:27 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: Organization for Security and Co-operation in Europe</div><p><img src="https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1534896-OSCE%20Special%20Monitoring%20Mission%20to%20Ukraine%20%28SMM%29%20Daily%20Report%20215-2020%20issued%20on%209%20September%202020.png" alt=""></p><p>Please refer to the attached file.</p><p><strong>Summary</strong></p><ul><li>The SMM recorded one ceasefire violation in Donetsk region and none in Luhansk region. In the previous reporting period, the SMM recorded no ceasefire violations in Donetsk region and 50 in Luhansk region.</li><li>The Mission continued monitoring the disengagement areas near Stanytsia Luhanska, Zolote and Petrivske. During evening and night hours, an SMM long-range unmanned aerial vehicle spotted people inside the latter two areas.</li><li>The SMM facilitated and monitored adherence to localised ceasefires to enable repairs to and the operation of critical civilian infrastructure.</li><li>The Mission continued following up on the situation of civilians amid the COVID-19 outbreak, including at an entry-exit checkpoint in Luhansk region.<br></li><li>The SMM&rsquo;s freedom of movement continued to be restricted, including near non-government-controlled Korsun, Donetsk region and at a border crossing point outside government control near Leonove, Luhansk region.</li></ul>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>Organization for Security and Co-operation in Europe</category>
            <category>Mine Action</category>
            <category>Peacekeeping and Peacebuilding</category>
            <category>Situation Report</category>
            <category>Epidemic</category>
            <author>Organization for Security and Co-operation in Europe</author>
            <enclosure
        url="https://reliefweb.int/sites/reliefweb.int/files/resources/OSCE%20Special%20Monitoring%20Mission%20to%20Ukraine%20%28SMM%29%20Daily%20Report%20215-2020%20issued%20on%209%20September%202020.pdf"
        length="814930"
        type="application/pdf"
      />
        </item>
        <item>
            <title>Ukraine 2020 HRP Funding Snapshot As of 31 August 2020</title>
            <link>https://reliefweb.int/report/ukraine/ukraine-2020-hrp-funding-snapshot-31-august-2020</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/ukraine-2020-hrp-funding-snapshot-31-august-2020</guid>
            <pubDate>Wed, 09 Sep 2020 15:35:59 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: UN Office for the Coordination of Humanitarian Affairs</div><p><img src="https://reliefweb.int/sites/reliefweb.int/files/styles/m/public/resources-pdf-previews/1534856-funding_hrp_august_2020-20200909.png" alt=""></p><p>Please refer to the attached Infographic.</p>
                              ]]>
            </description>
            <category>Ukraine</category>
            <category>UN Office for the Coordination of Humanitarian Affairs</category>
            <category>Contributions</category>
            <category>Infographic</category>
            <author>UN Office for the Coordination of Humanitarian Affairs</author>
            <enclosure
        url="https://reliefweb.int/sites/reliefweb.int/files/resources/funding_hrp_august_2020-20200909.pdf"
        length="176362"
        type="application/pdf"
      />
        </item>
        <item>
            <title>Ukraine: Press Statement of Special Representative Grau after the extraordinary Meeting of Trilateral Contact Group on 9 September 2020</title>
            <link>https://reliefweb.int/report/ukraine/press-statement-special-representative-grau-after-extraordinary-meeting-trilateral-0</link>
            <guid isPermaLink="true">https://reliefweb.int/report/ukraine/press-statement-special-representative-grau-after-extraordinary-meeting-trilateral-0</guid>
            <pubDate>Wed, 09 Sep 2020 14:55:46 +0000</pubDate>
            <source url="https://reliefweb.int/updates/rss.xml">ReliefWeb - Updates</source>
            <description>
                <![CDATA[
                <div class="tag country">Country: Ukraine</div><div class="tag source">Source: Organization for Security and Co-operation in Europe</div><p>KYIV, 9 September  2020 &ndash; The Special Representative of the OSCE Chairperson-in-Office in Ukraine and in the Trilateral Contact Group (TCG), Ambassador Heidi Grau, made the following statement to the press after the extraordinary meeting of the TCG &lrm;held through video conferencing:</p><p>"Today's extraordinary meeting of the Trilateral Contact Group was devoted to security issues and compliance with the ceasefire in the conflict zone, in particular, to discussing the situation in the area of Shumy, of which the participants of the meeting have diverging assessments.</p><p>The participants of the TCG meeting agreed that a visit of the discussed area would be useful. The visit is scheduled for 10 September 2020.</p><p>I urge the sides to continue doing all it takes to ensure an effective and sustainable ceasefire, first and foremost in the interest of the civilian population."</p><h3>Contacts</h3><p><strong>Communication and Media Relations Section</strong></p><p>OSCE Secretariat</p><p>Phone: + 43 676 71 74 592</p><p>press@osce.org</p>                      ]]>
            </description>
            <category>Ukraine</category>
            <category>Organization for Security and Co-operation in Europe</category>
            <category>Peacekeeping and Peacebuilding</category>
            <category>News and Press Release</category>
            <author>Organization for Security and Co-operation in Europe</author>
        </item>
    </channel>
</rss>
'''.encode('utf-8')
RSS_FEED_MOCK_LAMBDA_RESPONSE_EXISTING_SOURCESDATA = [
    {"url": "https://reliefweb.int/report/ukraine/ukraine-drc-ddg-legal-alert-issue-55-august-2020-enruuk", "status": "success"},
    {"url": "https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2212020-issued-16-september", "status": "failure"},
    {"url": "https://reliefweb.int/report/ukraine/crossing-contact-line-august-2020-snapshot-enuk", "status": "success"},
    {"url": "https://reliefweb.int/report/ukraine/eu-and-undp-supply-protective-respirators-medical-workers-donetsk-oblast", "status": "failure"},
    {"url": "https://reliefweb.int/report/ukraine/osce-special-monitoring-mission-ukraine-smm-daily-report-2202020-issued-15-september", "status": "success"},
]

# -----------------------------------------------  EMM -----------------------------------------------
EMM_MOCK_DATA = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
    xmlns:emm="http://emm.jrc.it"
    xmlns:iso="http://www.iso.org/3166"
    xmlns:georss="http://www.georss.org/georss"
    xmlns:content="http://purl.org/rss/1.0/modules/content/">
    <channel>
        <lastBuildDate>Thu, 17 Sep 2020 10:25:47 CEST</lastBuildDate>
        <title>Latest articles about Philippines with RMR</title>
        <link>https://emm.newsbrief.eu/NewsBrief</link>
        <description>RSS feed from the corresponding page on http://emm.newsbrief.eu/NewsBrief</description>
        <item>
            <title>Coronavirus and globalisation: the surprising resilience of container shipping</title>
            <link>https://finanz.dk/coronavirus-and-globalisation-the-surprising-resilience-of-container-shipping/</link>
            <description>By pulling services to prevent a glut, they have so far not only shielded themselves from a financial onslaught — many are making more money than before. “Carriers have taught themselves a valuable lesson this year,” says Lars Jensen, chief executive of SeaIntelligence Consulting.</description>
            <pubDate>Thu, 17 Sep 2020 10:25:00 +0200</pubDate>
            <source url="https://finanz.dk/" country="DK" >finanz</source>
            <iso:language>en</iso:language>
            <guid isPermaLink="false">finanz-84d5672e866e063b91294a2344d4bdec</guid>
            <category>CommunicableDiseases</category>
            <category>KyotoProtocol</category>
            <category>CoronavirusInfection</category>
            <category>Globalisation</category>
            <category>PublicHealth</category>
            <category emm:trigger="(Philippines)Philippines[1]; (TH0504-LackOfHumanitarianOrOtherAccess)humanitarian crisis[1]; ">TH5739-Philippines</category>
            <emm:entity id="197872" name="International Maritime Organisation">International Maritime Organization</emm:entity>
            <emm:entity id="1697740" name="Rolf Habben-Jansen">Rolf Habben Jansen</emm:entity>
            <emm:entity id="2119046" name="Mr Li">Mr Li</emm:entity>
            <emm:entity id="632977" name="David Kerstens">David Kerstens</emm:entity>
            <emm:entity id="2065444" name="Martin Li">Martin Li</emm:entity>
            <emm:entity id="2528522" name="Coronavirus">Coronavirus</emm:entity>
            <emm:entity id="730468" name="Lars Jensen">Lars Jensen</emm:entity>
            <emm:entity id="20591" name="Hapag Lloyd">Hapag-Lloyd</emm:entity>
            <emm:entity id="2126047" name="Guy Platten">Guy Platten</emm:entity>
            <georss:point>-23.647659 146.633408</georss:point>
        </item>
        <item>
            <title>PCOO slams watchdog’s claim killings went up 50% during pandemic</title>
            <link>https://mindanaoexaminernewspaper.blogspot.com/2020/09/pcoo-slams-watchdogs-claim-killings.html</link>
            <description>THE DUTERTE administration has prioritized human rights and dignity of all Filipinos in the time of the pandemic, Presidential Communications Operations Office (PCOO) Secretary Martin Andanar said Wednesday, denying a report which claimed that killings in the country worsened during the ongoing health crisis.</description>
            <pubDate>Thu, 17 Sep 2020 10:22:00 +0200</pubDate>
            <source url="https://mindanaoexaminernewspaper.blogspot.com/feeds/posts/default?alt=rss" country="PH" >mindanaoexaminernewspaper</source>
            <iso:language>en</iso:language>
            <guid isPermaLink="false">mindanaoexaminernewspaper-912c2423f51640a03d188a0d83884680</guid>
            <category>CoronavirusInfection</category>
            <category>PublicHealth</category>
            <category>Society</category>
            <category emm:trigger="(Philippines)Philippines[2]; geo[Philippines];(TH0603-ExcessiveUseOfForceKillingsBySecurityForces)extra judicial killings[1]; ">TH5739-Philippines</category>
            <emm:entity id="370642" name="Harry Roque">Harry Roque</emm:entity>
            <emm:entity id="2039619" name="Martin Andanar">Martin Andanar</emm:entity>
            <emm:entity id="2335" name="Human Rights Watch">Human Rights Watch</emm:entity>
            <georss:point>14.6096 121.006</georss:point>
        </item>
        <item>
            <title>Gov’t determined to uphold human rights, prosecute those who commit abuses — Andanar</title>
            <link>https://mb.com.ph/2020/07/02/govt-determined-to-uphold-human-rights-prosecute-those-who-commit-abuses-andanar/</link>
            <description>The government is determined to protect and uphold human rights and prosecute those who commit abuses in the war on illegal drugs. PCOO Sec. Martin Andanar. Presidential Communications Secretary Martin Andanar made the assurance following the creation of an inter-agency panel to review the....</description>
            <pubDate>Thu, 17 Sep 2020 09:24:00 +0200</pubDate>
            <source url="https://news.mb.com.ph/" country="PH" >mb-com-ph</source>
            <iso:language>en</iso:language>
            <guid isPermaLink="false">mb-com-ph-8c61e767a95d5eb88971d17d7120338f</guid>
            <category>TH3101-MentionsOfOHCHR</category>
            <category>UNbodies</category>
            <category>Conflict</category>
            <category>Society</category>
            <category emm:trigger="(Philippines)source[PH](TH0603-ExcessiveUseOfForceKillingsBySecurityForces)extrajudicial killings[1]; ">TH5739-Philippines</category>
            <emm:entity id="152035" name="United Nations Human Rights Council">United Nations Human Rights Council</emm:entity>
            <emm:entity id="152035" name="United Nations Human Rights Council">UN Human Rights Council</emm:entity>
            <emm:entity id="3202" name="United Nations">United Nations</emm:entity>
            <emm:entity id="27398" name="Justice Department">Department of Justice</emm:entity>
            <emm:entity id="10264" name="Michelle Bachelet">Michelle Bachelet</emm:entity>
            <emm:entity id="2182443" name="Menardo Guevarra">Menardo Guevarra</emm:entity>
            <emm:entity id="2039619" name="Martin Andanar">Martin Andanar</emm:entity>
            <emm:entity id="2115501" name="Duterte government">Duterte government</emm:entity>
            <emm:entity id="2260013" name="Presidential Communications">Presidential Communications</emm:entity>
            <emm:entity id="23951" name="Member States">member-states</emm:entity>
        </item>
        <item>
            <title>Tribute to fallen human rights activists</title>
            <link>https://news.abs-cbn.com/news/multimedia/photo/09/17/20/tribute-to-fallen-human-rights-activists-philippines</link>
            <description>Human rights activists hold a eulogy and light candles for colleagues from the Cagayan Valley who were victims of alleged extrajudicial killings during the Marcos and Duterte administrations, at the Bantayog ng mga Bayani in Quezon City on Thursday. The tribute was organized leading up to the 48th....</description>
            <pubDate>Thu, 17 Sep 2020 09:20:00 +0200</pubDate>
            <source url="https://news.abs-cbn.com/business" country="PH" >abs-cbnnews</source>
            <iso:language>en</iso:language>
            <guid isPermaLink="false">abs-cbnnews-1e781b776142a3180498136d19de4988</guid>
            <category emm:trigger="(Philippines)geo[Quezon City];(TH0603-ExcessiveUseOfForceKillingsBySecurityForces)extrajudicial killings[1]; ">TH5739-Philippines</category>
            <georss:point>14.6629 121.065</georss:point>
        </item>
        <item>
            <title>At least 40 Filipinos under age 14 give birth in Philippines annually: POPCOM</title>
            <link>https://news.abs-cbn.com/news/09/17/20/at-least-40-filipinos-under-age-14-give-birth-in-philippines-annually-popcom</link>
            <description>MANILA - At least 40 children aged between 10 and 14-years-old give birth in the Philippines every year, an official from the Population Commission (POPCOM) said, Thursday. Of the 62,000 minors who gave birth in the country in 2018, 2,200 girls were below 15-years-old, POPCOM executive director....</description>
            <pubDate>Thu, 17 Sep 2020 09:20:00 +0200</pubDate>
            <source url="https://news.abs-cbn.com/business" country="PH" >abs-cbnnews</source>
            <iso:language>en</iso:language>
            <guid isPermaLink="false">abs-cbnnews-5cc1b8d4900ca40996c202e221980e3b</guid>
            <category emm:trigger="(Philippines)Philippines[4]; MANILA[1]; geo[Philippines];(TH0307-SexualViolence)rape[2]; sexual violence[1]; ">TH5739-Philippines</category>
            <emm:entity id="2029017" name="Population Commission">Population Commission</emm:entity>
            <emm:entity id="154005" name="Senate Majority">Senate Majority</emm:entity>
            <emm:entity id="2539209" name="Juan Miguel Zubiri">Juan Miguel Zubiri</emm:entity>
            <georss:point>14.6096 121.006</georss:point>
        </item>
    </channel>
</rss>
'''.encode('utf-8')
EMM_MOCK_LAMBDA_RESPONSE_EXISTING_SOURCESDATA = [
    {"url": "https://finanz.dk/coronavirus-and-globalisation-the-surprising-resilience-of-container-shipping/", "status": "success"},
    {"url": "https://mindanaoexaminernewspaper.blogspot.com/2020/09/pcoo-slams-watchdogs-claim-killings.html", "status": "success"},
    {"url": "https://mb.com.ph/2020/07/02/govt-determined-to-uphold-human-rights-prosecute-those-who-commit-abuses-andanar/", "status": "failure"},
    {"url": "https://news.abs-cbn.com/news/multimedia/photo/09/17/20/tribute-to-fallen-human-rights-activists-philippines", "status": "success"},
    {"url": "https://news.abs-cbn.com/news/09/17/20/at-least-40-filipinos-under-age-14-give-birth-in-philippines-annually-popcom", "status": "failure"},
]


MOCK_CONTENT_DATA_BY_KEY = {
    relief_web.ReliefWeb.key: RELIEF_WEB_MOCK_DATA,
    atom_feed.AtomFeed.key: ATOM_FEED_MOCK_DATA,
    rss_feed.RssFeed.key: RSS_FEED_MOCK_DATA,
    emm.EMM.key: EMM_MOCK_DATA,
    # TODO: Add further mock data
    # acaps_briefing_notes.AcapsBriefingNotes.key: ACAPS_BRIEFING_NOTES_MOCK_DATA,
    # unhcr_portal.UNHCRPortal.key: UNHCR_PORTAL_MOCK_DATA,
    # pdna.PDNA.key: PDNA_MOCK_DATA,
    # research_center.ResearchResourceCenter.key: RESEARCH_CENTER_MOCK_DATA,
    # wpf.WorldFoodProgramme.key: WPF_MOCK_DATA,
    # humanitarian_response.HumanitarianResponse.key: HUMANITARIAN_RESPONSE_MOCK_DATA,
}

MOCK_LAMBDA_RESPONSE_SOURCES_BY_KEY = {
    relief_web.ReliefWeb.key: (
        RELIEF_WEB_MOCK_DATA_LAMBDA_RESPONSE_EXISTING_SOURCES + RELIEF_WEB_MOCK_DATA_LAMBDA_RESPONSE_NEW_SOURCES
    ),
    atom_feed.AtomFeed.key: ATOM_FEED_MOCK_DATA_LAMBDA_RESPONSE_EXISTING_SOURCES,
    rss_feed.RssFeed.key: RSS_FEED_MOCK_LAMBDA_RESPONSE_EXISTING_SOURCESDATA,
    emm.EMM.key: EMM_MOCK_LAMBDA_RESPONSE_EXISTING_SOURCESDATA,
    # TODO: Add further mock data
    # acaps_briefing_notes.AcapsBriefingNotes.key: ACAPS_BRIEFING_NOTES_MOCK_LAMBDA_RESPONSE_EXISTING_SOURCESDATA,
    # unhcr_portal.UNHCRPortal.key: UNHCR_PORTAL_MOCK_LAMBDA_RESPONSE_EXISTING_SOURCESDATA,
    # pdna.PDNA.key: PDNA_MOCK_LAMBDA_RESPONSE_EXISTING_SOURCESDATA,
    # research_center.ResearchResourceCenter.key: RESEARCH_CENTER_MOCK_LAMBDA_RESPONSE_EXISTING_SOURCESDATA,
    # wpf.WorldFoodProgramme.key: WPF_MOCK_LAMBDA_RESPONSE_EXISTING_SOURCESDATA,
    # humanitarian_response.HumanitarianResponse.key: HUMANITARIAN_RESPONSE_MOCK_LAMBDA_RESPONSE_EXISTING_SOURCESDATA,
}

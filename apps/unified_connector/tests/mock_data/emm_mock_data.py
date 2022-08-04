import datetime

EMM_MOCK_DATA_RAW = '''<?xml version="1.0" encoding="utf-8" ?>
<rss xmlns:emm="http://emm.jrc.it" xmlns:iso="http://www.iso.org/3166" xmlns:georss="http://www.georss.org/georss" xmlns:content="http://purl.org/rss/1.0/modules/content/" version="2.0">
<channel>
<title>Latest news clusters for en</title>
<link>https://emm.newsbrief.eu/NewsBrief</link>
<description>RSS feed from the corresponding page on https://emm.newsbrief.eu/NewsBrief</description>
<!--  Note for users and developers.  -->
<!--  The element “emm:description” has been replaced by “emm:keywords”. Please contact jrc-emm-support [at] ec.europa.eu for any questions.  -->
<!--  This endpoint doesn't return articles older than 1 month. If you would like to access older content, please contact jrc-emm-support [at] ec.europa.eu.  -->
<item>
<title>RBA Governor says he ‘doesn’t see a recession on the horizon’</title>
<link>https://www.heraldsun.com.au/business/rba-governor-says-he-doesnt-see-a-recession-on-the-horizon/video/56f4558c345418ad2964232cdbd06ca7?nk=0ad220a3bbd23f948b26d2da2bb5ac09-1655775162</link>
<emm:keywords>reserve bank,recession,horizon,australia governor philip,forecasting economic downturns,rba governor,governor philip lowe,unemployment rate,bank of australia,australians have jobs,years,participation rate's,countries forecasting economic</emm:keywords>
<pubDate>Tue, 21 Jun 2022 03:32:00 +0200</pubDate>
<guid isPermaLink="false">heraldsun-8360f140d629f2d582d35fd2c9c5a627.20220621.en</guid>
<source url="http://www.heraldsun.com.au/business/rss" country="AU">heraldsun</source>
<iso:language>en</iso:language>
<emm:bns level="100">2022-06-21T01:46+0200</emm:bns>
<emm:entity id="12850" name="Reserve Bank">Reserve Bank</emm:entity>
<emm:entity id="2561290" name="Bank of Australia">Bank of Australia</emm:entity>
<emm:entity id="16351" name="Philip Lowe">Philip Lowe</emm:entity>
<emm:entity id="16351" name="Philip Lowe"/>
<emm:entity id="2561290" name="Bank of Australia"/>
<emm:entity id="12850" name="Reserve Bank"/>
<georss:point>-35.34990 149.04200</georss:point>
<georss:point>-35.3499 149.042</georss:point>
</item>
<item>
<title>Goyal calls for digital media use for speedy consumer complaint redressal</title>
<link>https://www.business-standard.com/article/current-affairs/goyal-calls-for-digital-media-use-for-speedy-consumer-complaint-redressal-122062100114_1.html</link>
<emm:keywords>district commissions,digital media,consumer protection act,consumer commissions,state,national commission,union minister piyush,speedy consumer complaint,consumer disputes redressal,goyal calls,cases,president and members</emm:keywords>
<pubDate>Tue, 21 Jun 2022 03:58:00 +0200</pubDate>
<guid isPermaLink="false">business-standard-98e2bf24ea6f876cd6d60f7618f840fe.20220621.en</guid>
<source url="https://www.business-standard.com/rss/latest.rss" country="IN">business-standard</source>
<iso:language>en</iso:language>
<emm:bns level="100">2022-06-21T01:46+0200</emm:bns>
<category>ConsumerPolicy</category>
<category>ConsumerPolicy</category>
<category>CoronavirusInfection</category>
<emm:entity id="2251810" name="BIS">BIS</emm:entity>
<emm:entity id="2683272" name="Kumar Singh">Kumar Singh</emm:entity>
<emm:entity id="2557189" name="Rohit Kumar Singh">Rohit Kumar Singh</emm:entity>
<emm:entity id="1861375" name="District Commission">District Commission</emm:entity>
<emm:entity id="1842841" name="Piyush Goyal">Piyush Goyal</emm:entity>
<emm:entity id="2559858" name="Anupam Mishra">Anupam Mishra</emm:entity>
<emm:entity id="2673127" name="Secretary Department">Secretary, Department</emm:entity>
<emm:entity id="2557189" name="Rohit Kumar Singh"/>
<emm:entity id="2683272" name="Kumar Singh"/>
<emm:entity id="1842841" name="Piyush Goyal"/>
<emm:entity id="2673127" name="Secretary Department"/>
<emm:entity id="2251810" name="BIS"/>
<emm:entity id="2559858" name="Anupam Mishra"/>
<emm:entity id="1861375" name="District Commission"/>
<emm:entity id="1821479" name="India News"/>
<emm:entity id="2528522" name="Coronavirus"/>
<emm:entity id="1763" name="Rahul Gandhi"/>
<emm:entity id="2625036" name="Also Read"/>
<georss:point>28.5687 77.2168</georss:point>
</item>
<item>
<title>Top saints laud PM Modi in Karnataka's Mysuru</title>
<link>https://www.longbeachstar.com/news/272592709/top-saints-laud-pm-modi-in-karnataka-mysuru</link>
<emm:keywords>india,top saints laud,karnataka's mysuru,minister narendra modi,laud pm modi,saints laud pm,unprecedented development works,shivarathri deshikendra mahaswamiji,prime minister,world,modi in karnataka's,mataji shrimati heeraben</emm:keywords>
<pubDate>Tue, 21 Jun 2022 04:13:00 +0200</pubDate>
<guid isPermaLink="false">northernirelandnews-453ff1e3d8afeee6d90f2f9ff2850516.20220621.en</guid>
<source url="https://www.longbeachstar.com/category/b8de8e630faf3631" country="US">longbeachstar</source>
<iso:language>en</iso:language>
<emm:bns level="100">2022-06-21T01:46+0200</emm:bns>
<category>CoronavirusInfection</category>
<emm:entity id="2001602" name="Indian Society">Indian society</emm:entity>
<emm:entity id="606324" name="Ram Mandir">Ram Mandir</emm:entity>
<emm:entity id="1231" name="Narendra Modi">Narendra Modi</emm:entity>
<emm:entity id="2001602" name="Indian Society"/>
<emm:entity id="1231" name="Narendra Modi"/>
<emm:entity id="606324" name="Ram Mandir"/>
<emm:entity id="1821479" name="India News"/>
<emm:entity id="2528522" name="Coronavirus"/>
<emm:entity id="2625036" name="Also Read"/>
<georss:point>14.70047 76.16115</georss:point>
<georss:point>14.70047 76.16115</georss:point>
</item>
</channel>
</rss>
'''.encode('utf-8')

EMM_PARAMS = {
    'feed-url': "test-url",
    'url-field': 'link',
    'date-field': 'pubDate',
    'source-field': 'source',
    'author-field': 'source',
    'title-field': 'title',
}

EMM_MOCK_EXCEPTED_LEADS = [
    {
        "url": "https://www.heraldsun.com.au/business/rba-governor-says-he-doesnt-see-a-recession-on-the-horizon/video/56f4558c345418ad2964232cdbd06ca7?nk=0ad220a3bbd23f948b26d2da2bb5ac09-1655775162",
        "published_on": datetime.date(2022, 6, 21),
        "title": "RBA Governor says he ‘doesn’t see a recession on the horizon’",
        "source_type": 'emm',
        'author_raw': 'heraldsun',
        'source_raw': 'heraldsun',
    },
    {
        "url": "https://www.business-standard.com/article/current-affairs/goyal-calls-for-digital-media-use-for-speedy-consumer-complaint-redressal-122062100114_1.html",
        "published_on": datetime.date(2022, 6, 21),
        "title": "Goyal calls for digital media use for speedy consumer complaint redressal",
        "source_type": 'emm',
        'author_raw': 'business-standard',
        'source_raw': 'business-standard',
    },
    {
        "url": "https://www.longbeachstar.com/news/272592709/top-saints-laud-pm-modi-in-karnataka-mysuru",
        "published_on": datetime.date(2022, 6, 21),
        "title": "Top saints laud PM Modi in Karnataka's Mysuru",
        "source_type": 'emm',
        'author_raw': 'longbeachstar',
        'source_raw': 'longbeachstar',
    }
]

from connector.sources import (
    atom_feed,
    relief_web,
    rss_feed,
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
        }
      ]
    }
'''

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
            <id>tag:feedly.com,2013:cloud/entry/tCS+2m1OpGdjXiXxCw+JFMvBfkRWtIxNSz4wk+LTxZw=_17497cf3034:35844c:af405028</id>
            <title type="html">Cerca de 700 jovens prestaram juramento hoje na Manhiça para o curso militar que arrancou em abril. Iniciou com mais de 800, mas outros desistiram. A cerimónia do encerramento foi secreta. Cerca de 200 deverão ir a #CaboDelgado enquanto outros às especialidades (artilharia etc).. pic.twitter.com/0QmZ2rWF6g&amp;mdash; Alexandre (@AllexandreMZ) September 14, 2020</title>
            <published>2020-09-16T16:46:12Z</published>
            <updated>2020-09-16T16:46:20Z</updated>
            <link rel="alternate" href="https://twitter.com/AllexandreMZ/status/1305555590001946624" type="text/html"/>
            <content type="html">&lt;div&gt;&lt;blockquote class="twitter-tweet"&gt;&lt;p lang="pt" dir="ltr"&gt;Cerca de 700 jovens prestaram juramento hoje na Manhiça para o curso militar que arrancou em abril. Iniciou com mais de 800, mas outros desistiram. A cerimónia do encerramento foi secreta. Cerca de 200 deverão ir a &lt;a href="https://twitter.com/hashtag/CaboDelgado?src=hash&amp;ref_src=twsrc%5Etfw"&gt;#CaboDelgado&lt;/a&gt; enquanto outros às especialidades (artilharia etc).. &lt;a href="https://t.co/0QmZ2rWF6g"&gt;pic.twitter.com/0QmZ2rWF6g&lt;/a&gt;&lt;/p&gt;— Alexandre (@AllexandreMZ) &lt;a href="https://twitter.com/AllexandreMZ/status/1305555590001946624?ref_src=twsrc%5Etfw"&gt;September 14, 2020&lt;/a&gt;&lt;/blockquote&gt;&lt;/div&gt;</content>
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
            <summary type="html">Mozambican Defence Minister Jaime Neto claimed on Wednesday that some of those involved in producing videos which supposedly show the Mozambican defence and security forces committing atrocities have been identified, and he promised that action will be taken against them. Neto was speaking the da</summary>
            <content type="html">&lt;div&gt;&lt;div&gt;&lt;div&gt;&lt;figcaption&gt;&lt;p&gt;Mozambican Defence Minister Jaime Neto claimed on Wednesday that some of those involved in producing videos which supposedly show the Mozambican defence and security forces committing atrocities have been identified, and he promised that action will be taken against them.&lt;/p&gt; &lt;p&gt;Neto was speaking the day after Interior Minister Amade Miquidade had announced that the government is investigating the origin of the videos. He said the government wants to find “where the nucleus is that is making these videos”.&lt;/p&gt; &lt;p&gt;Several videos have circulated in recent days claiming to show Mozambican troops committing torture, summary execution and other human rights abuses. The human rights organisation Amnesty International publicised some of them, and called for an investigation.&lt;/p&gt; &lt;p&gt;Several Mozambican organisations, including the National Human Rights Commission (CNDH), and the Mozambican Bar Association (OAM), have also called for a full inquiry.&lt;/p&gt; &lt;p&gt;The government, however, believes the videos are fakes, shot in order to denigrate the defence and security forces.&lt;/p&gt; &lt;p&gt;Speaking after he had launched a week of commemorations of the anniversary of the start of the independence war, on 25 September 1964, Neto said investigations into the videos are under way.&lt;/p&gt; &lt;p&gt;“Some Mozambicans make and assemble these images and send them abroad”, he accused. “We know who they are. We shall expose them one day, and we shall pick them up because they are attacking the Mozambican nation”.&lt;/p&gt; &lt;p&gt;Neto said the main challenge the defence and security forces face is to resist the attacks by islamist terrorists in the northern province of Cabo Delgado. Since the first terrorist raids, in October 2017, hundreds of people have died, and around 200,000 have been displaced from their homes.&lt;/p&gt; &lt;p&gt;“The challenge we face is to combat and eliminate terrorism”, said Neto. “The men and women on the battle field are making all manner of sacrifices to overcome the challenges. We are under attack from forces whose intentions we do not know, but we are determined to defeat terrorism”.&lt;/p&gt; &lt;p&gt; &lt;/p&gt; &lt;strong&gt;Source: &lt;/strong&gt;AIM    &lt;/figcaption&gt;&lt;/div&gt;&lt;/div&gt;&lt;/div&gt;</content>
            <author>
                <name>mozambique</name>
            </author>
            <media:content medium="image" url="https://clubofmozambique.com/wp-content/uploads/2020/09/jaimeneto.tvm_.jpg"/>
        </entry>
    </feed>
'''

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


MOCK_CONTENT_DATA_BY_KEY = {
    relief_web.ReliefWeb.key: RELIEF_WEB_MOCK_DATA,
    atom_feed.AtomFeed.key: ATOM_FEED_MOCK_DATA,
    rss_feed.RssFeed.key: RSS_FEED_MOCK_DATA,
}

import datetime

ATOM_FEED_MOCK_DATA_RAW = '''
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
   <category term="Python" label="r/Python" />
   <updated>2022-05-19T04:25:23+00:00</updated>
   <icon>https://www.redditstatic.com/icon.png/</icon>
   <id>/r/python/.rss</id>
   <link rel="self" href="https://www.reddit.com/r/python/.rss" type="application/atom+xml" />
   <link rel="alternate" href="https://www.reddit.com/r/python/" type="text/html" />
   <logo>https://b.thumbs.redditmedia.com/8HiO52_EuT_h63Qg.png</logo>
   <subtitle>News about the programming language Python. If you have something to teach others post here.</subtitle>
   <title>Python</title>
   <entry>
      <author>
         <name>/u/Im__Joseph</name>
         <uri>https://www.reddit.com/user/Im__Joseph</uri>
      </author>
      <category term="Python" label="r/Python" />
      <id>t3_uptmup</id>
      <link href="https://www.reddit.com/r/Python/comments/uptmup/sunday_daily_thread_whats_everyone_working_on/" />
      <updated>2022-05-15T00:00:09+00:00</updated>
      <published>2022-05-15T00:00:09+00:00</published>
      <title>Sunday Daily Thread: What's everyone working on this week?</title>
   </entry>
   <entry>
      <author>
         <name>/u/BigdadEdge</name>
         <uri>https://www.reddit.com/user/BigdadEdge</uri>
      </author>
      <category term="Python" label="r/Python" />
      <id>t3_usqy75</id>
      <link href="https://www.reddit.com/r/Python/comments/usqy75/best_methods_to_run_a_continuous_python_script_on/" />
      <updated>2022-05-19T00:29:56+00:00</updated>
      <published>2022-05-19T00:29:56+00:00</published>
      <title>Best methods to run a continuous Python script on a server</title>
   </entry>
   <entry>
      <author>
         <name>/u/pvc</name>
         <uri>https://www.reddit.com/user/pvc</uri>
      </author>
      <category term="Python" label="r/Python" />
      <id>t3_usjg8k</id>
      <link href="https://www.reddit.com/r/Python/comments/usjg8k/arcade_2614_has_been_released_2d_game_library/" />
      <updated>2022-05-18T18:29:54+00:00</updated>
      <published>2022-05-18T18:29:54+00:00</published>
      <title>Arcade 2.6.14 has been released (2D game library)</title>
   </entry>
   <entry>
      <author>
         <name>/u/jabza_</name>
         <uri>https://www.reddit.com/user/jabza_</uri>
      </author>
      <category term="Python" label="r/Python" />
      <id>t3_usdhpf</id>
      <link href="https://www.reddit.com/r/Python/comments/usdhpf/i_made_a_browser_extension_for_quick_nested/" />
      <updated>2022-05-18T13:54:21+00:00</updated>
      <published>2022-05-18T13:54:21+00:00</published>
      <title>I made a browser extension for quick nested browsing of the Python docs (and others)</title>
   </entry>
   <entry>
      <author>
         <name>/u/badassbilla</name>
         <uri>https://www.reddit.com/user/badassbilla</uri>
      </author>
      <category term="Python" label="r/Python" />
      <id>t3_usqwnc</id>
      <link href="https://www.reddit.com/r/Python/comments/usqwnc/time_series_modelling/" />
      <updated>2022-05-19T00:27:38+00:00</updated>
      <published>2022-05-19T00:27:38+00:00</published>
      <title>Time Series Modelling</title>
   </entry>
</feed>
'''

ATOM_FEED_PARAMS = {
    "feed-url": "test-url",
    "url-field": "link",
    "author-field": "author",
    "source-field": "source",
    "date-field": "published",
    "title-field": "title"
}

ATOM_FEED_MOCK_EXCEPTED_LEADS = [
    {
        "url": "https://www.reddit.com/r/Python/comments/uptmup/sunday_daily_thread_whats_everyone_working_on/",
        "author_raw": "/u/Im__Joseph",
        "published_on": datetime.date(2022, 5, 15),
        "title": "Sunday Daily Thread: What's everyone working on this week?",
        "source_type": 'rss'
    },
    {
        "url": "https://www.reddit.com/r/Python/comments/usqy75/best_methods_to_run_a_continuous_python_script_on/",
        "author_raw": "/u/BigdadEdge",
        "published_on": datetime.date(2022, 5, 19),
        "title": "Best methods to run a continuous Python script on a server",
        "source_type": 'rss'
    },
    {
        "url": "https://www.reddit.com/r/Python/comments/usjg8k/arcade_2614_has_been_released_2d_game_library/",
        "author_raw": "/u/pvc",
        "published_on": datetime.date(2022, 5, 18),
        "title": "Arcade 2.6.14 has been released (2D game library)",
        "source_type": 'rss'
    },
    {
        "url": "https://www.reddit.com/r/Python/comments/usdhpf/i_made_a_browser_extension_for_quick_nested/",
        "author_raw": "/u/jabza_",
        "published_on": datetime.date(2022, 5, 18),
        "title": "I made a browser extension for quick nested browsing of the Python docs (and others)",
        "source_type": 'rss'
    },
    {
        "url": "https://www.reddit.com/r/Python/comments/usqwnc/time_series_modelling/",
        "author_raw": "/u/badassbilla",
        "published_on": datetime.date(2022, 5, 19),
        "title": "Time Series Modelling",
        "source_type": 'rss'
    },
]

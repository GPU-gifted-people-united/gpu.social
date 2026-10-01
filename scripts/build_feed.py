#!/usr/bin/env python3
"""Build public feeds from reviewed updates only. Never read submissions."""
import json
from pathlib import Path
from datetime import datetime
from email.utils import format_datetime
from xml.etree.ElementTree import Element, SubElement, tostring
ROOT = Path(__file__).resolve().parents[1]
items = json.loads((ROOT / 'updates.json').read_text())
seen = set()
for item in items:
    assert item['id'] not in seen, 'Duplicate update ID'
    seen.add(item['id'])
    assert item['url'].startswith('https://gpu.social/'), 'Use a public GPU URL'
    datetime.fromisoformat(item['date_published'].replace('Z', '+00:00'))
feed = {'version': 'https://jsonfeed.org/version/1.1', 'title': 'GPU / Expedition log', 'home_page_url': 'https://gpu.social/', 'feed_url': 'https://gpu.social/workshop/feed.json', 'items': [{**i, 'content_text': i['summary']} for i in items]}
(ROOT / 'public/feed.json').write_text(json.dumps(feed, ensure_ascii=False, indent=2) + '\n')
rss = Element('rss', version='2.0')
channel = SubElement(rss, 'channel')
for name, value in [('title', 'GPU / Expedition log'), ('link', 'https://gpu.social/'), ('description', 'Projects, updates and opportunities to participate in Gifted People United.')]:
    SubElement(channel, name).text = value
for i in items:
    entry = SubElement(channel, 'item')
    for name, value in [('title', i['title']), ('link', i['url']), ('description', i['summary']), ('pubDate', format_datetime(datetime.fromisoformat(i['date_published'].replace('Z', '+00:00'))))]:
        SubElement(entry, name).text = value
    SubElement(entry, 'guid', isPermaLink='false').text = i['id']
(ROOT / 'public/feed.xml').write_bytes(tostring(rss, encoding='utf-8', xml_declaration=True))

import urllib.request
import re
import json

url = "https://etherreads.com/series/shut-up-malevolent-dragon-i-dont-want-to-have-any-more-children-with-you/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    links = re.findall(r'href=[\'"](https://etherreads\.com/shut-up-malevolent-dragon-i-dont-want-to-have-any-more-children-with-you-v1c\d+/)[\'"]', html)
    unique_links = list(dict.fromkeys(links))
    print(f"Total links found: {len(unique_links)}")
    for l in unique_links[:25]:
        print(l)
except Exception as e:
    print(f"Error: {e}")

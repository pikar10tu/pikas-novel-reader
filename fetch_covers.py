import urllib.request
import re

headers = {'User-Agent': 'Mozilla/5.0'}

# 1. Dragon cover
url_dragon = 'https://etherreads.com/series/shut-up-malevolent-dragon-i-dont-want-to-have-any-more-children-with-you/'
try:
    req = urllib.request.Request(url_dragon, headers=headers)
    html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
    m = re.findall(r'<div class="thumb"[^>]*>.*?<img[^>]+src=["\']([^"\']+)["\']', html, re.DOTALL)
    print("Dragon cover:", m)
except Exception as e:
    print("Dragon error:", e)

# 2. Suicide hunter cover
url_hunter = 'https://noveltranslationhub.com/novel/sss-class-suicide-hunter/'
try:
    req2 = urllib.request.Request(url_hunter, headers=headers)
    html2 = urllib.request.urlopen(req2, timeout=10).read().decode('utf-8')
    m2 = re.findall(r'<div class="summary_image"[^>]*>.*?<img[^>]+src=["\']([^"\']+)["\']', html2, re.DOTALL)
    print("Hunter cover 1:", m2)
    if not m2:
        m3 = re.findall(r'src=["\'](https://[^"\']+(?:suicide|sss|novel)[^"\']+\.(?:jpg|png|webp|jpeg))["\']', html2, re.I)
        print("Hunter cover 2:", m3)
except Exception as e:
    print("Hunter error:", e)

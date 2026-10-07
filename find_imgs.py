import urllib.request
import re

url = 'https://etherreads.com/series/shut-up-malevolent-dragon-i-dont-want-to-have-any-more-children-with-you/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')
imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
for img in imgs:
    print(img)

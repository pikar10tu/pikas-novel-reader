import urllib.request
import re
import os
import json
import time

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def fetch_url(url):
    req = urllib.request.Request(url, headers=headers)
    return urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')

# 1. SSS-Class Suicide Hunter Ch 1-5 (from noveltranslationhub)
os.makedirs('novels/revival-hunter/raw', exist_ok=True)
for ch in range(1, 6):
    file_path = f'novels/revival-hunter/raw/ch{ch}.json'
    if os.path.exists(file_path):
        continue
    url = f'https://noveltranslationhub.com/novel/sss-class-suicide-hunter/chapter-{ch}/'
    try:
        html = fetch_url(url)
        # title
        t_m = re.search(r'<h1[^>]*class="[^"]*entry-title[^"]*"[^>]*>(.*?)</h1>', html, re.I)
        if not t_m:
            t_m = re.search(r'<title>(.*?)</title>', html, re.I)
        title = t_m.group(1).strip() if t_m else f"Chapter {ch}"
        
        # content
        c_m = re.search(r'<div[^>]*class="[^"]*(?:reading-content|text-left|entry-content)[^"]*"[^>]*>(.*?)</div>\s*<(?:div|nav)', html, re.DOTALL)
        content_html = c_m.group(1) if c_m else html
        paras = re.findall(r'<p>(.*?)</p>', content_html, re.DOTALL)
        cleaned = []
        for p in paras:
            c = re.sub(r'<[^>]+>', '', p).strip()
            c = re.sub(r'&#8217;', "'", c)
            c = re.sub(r'&#8220;', '"', c)
            c = re.sub(r'&#8221;', '"', c)
            c = re.sub(r'&#8230;', '...', c)
            if c and 'noveltranslationhub' not in c.lower():
                cleaned.append(c)
        data = {'chapter': ch, 'title': title, 'paragraphs': cleaned}
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Suicide Hunter Ch {ch}: {len(cleaned)} paras")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error Hunter Ch {ch}: {e}")

# 2. Cultivation Chat Group Ch 1-5 (from empirenovel)
os.makedirs('novels/cultivation-chat-group/raw', exist_ok=True)
for ch in range(1, 6):
    file_path = f'novels/cultivation-chat-group/raw/ch{ch}.json'
    if os.path.exists(file_path):
        continue
    url = f'https://www.empirenovel.com/novel/cultivation-chat-group/chapter-{ch}'
    try:
        html = fetch_url(url)
        t_m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.I)
        title = t_m.group(1).strip() if t_m else f"Chapter {ch}"
        c_m = re.search(r'<div[^>]*class="[^"]*chapter-content[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        content_html = c_m.group(1) if c_m else html
        paras = re.findall(r'<p>(.*?)</p>', content_html, re.DOTALL)
        cleaned = [re.sub(r'<[^>]+>', '', p).strip() for p in paras if p.strip()]
        data = {'chapter': ch, 'title': title, 'paragraphs': cleaned}
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"CCG Ch {ch}: {len(cleaned)} paras")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error CCG Ch {ch}: {e}")

# 3. Dual Cultivation Ch 1-5 (from empirenovel)
os.makedirs('novels/dual-cultivation/raw', exist_ok=True)
for ch in range(1, 6):
    file_path = f'novels/dual-cultivation/raw/ch{ch}.json'
    if os.path.exists(file_path):
        continue
    url = f'https://www.empirenovel.com/novel/dual-cultivation/chapter-{ch}'
    try:
        html = fetch_url(url)
        t_m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.I)
        title = t_m.group(1).strip() if t_m else f"Chapter {ch}"
        c_m = re.search(r'<div[^>]*class="[^"]*chapter-content[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        content_html = c_m.group(1) if c_m else html
        paras = re.findall(r'<p>(.*?)</p>', content_html, re.DOTALL)
        cleaned = [re.sub(r'<[^>]+>', '', p).strip() for p in paras if p.strip()]
        data = {'chapter': ch, 'title': title, 'paragraphs': cleaned}
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Dual Cultivation Ch {ch}: {len(cleaned)} paras")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error DC Ch {ch}: {e}")

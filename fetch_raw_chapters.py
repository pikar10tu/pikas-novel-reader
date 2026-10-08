import urllib.request
import re
import os
import json
import time

os.makedirs('raw_chapters', exist_ok=True)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for ch in range(81, 101):
    file_path = f'raw_chapters/v1c{ch}.json'
    if os.path.exists(file_path):
        continue
    url = f'https://etherreads.com/shut-up-malevolent-dragon-i-dont-want-to-have-any-more-children-with-you-v1c{ch}/'
    try:
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8')
        # Extract title
        title_match = re.search(r'<h1 class="entry-title"[^>]*>(.*?)</h1>', html)
        title = title_match.group(1).strip() if title_match else f"Chapter {ch}"
        
        # Extract content inside epcontent entry-content
        content_match = re.search(r'<div class="epcontent entry-content"[^>]*>(.*?)</div>\s*<div class="bottomnav">', html, re.DOTALL)
        if not content_match:
            content_match = re.search(r'<div class="epcontent entry-content"[^>]*>(.*?)</div>', html, re.DOTALL)
        
        raw_text = content_match.group(1) if content_match else ""
        
        # Extract paragraphs
        paragraphs = re.findall(r'<p>(.*?)</p>', raw_text, re.DOTALL)
        cleaned_paras = []
        for p in paragraphs:
            # clean html tags except em, strong
            clean = re.sub(r'&#8217;', "'", p)
            clean = re.sub(r'&#8220;', '"', clean)
            clean = re.sub(r'&#8221;', '"', clean)
            clean = re.sub(r'&#8230;', '...', clean)
            clean = clean.replace('&nbsp;', ' ').strip()
            if clean:
                cleaned_paras.append(clean)
                
        data = {
            'chapter': ch,
            'title': title,
            'paragraphs': cleaned_paras
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Downloaded Chapter {ch}: {len(cleaned_paras)} paragraphs")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error Ch {ch}: {e}")

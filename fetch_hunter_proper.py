import urllib.request
import re
import os
import json
import time

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

os.makedirs('novels/revival-hunter/raw', exist_ok=True)

for ch in range(1, 6):
    file_path = f'novels/revival-hunter/raw/ch{ch}.json'
    url = f'https://noveltranslationhub.com/novel/sss-class-suicide-hunter/chapter-{ch}/'
    try:
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
        
        paras = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
        cleaned_paras = []
        for p in paras:
            p_clean = re.sub(r'<[^>]+>', '', p).strip()
            p_clean = re.sub(r'&#8217;', "'", p_clean)
            p_clean = re.sub(r'&#8220;', '"', p_clean)
            p_clean = re.sub(r'&#8221;', '"', p_clean)
            p_clean = re.sub(r'&#8230;', '...', p_clean)
            
            # Skip footer/site notes
            if not p_clean:
                continue
            if 'noveltranslationhub' in p_clean.lower() or 'patreon' in p_clean.lower() or 'all rights reserved' in p_clean.lower():
                continue
            if 'please enter your username' in p_clean.lower() or 'save my name' in p_clean.lower():
                continue
            if p_clean.startswith('Translator:') or p_clean.startswith('Formatter:') or p_clean.startswith('Editor:'):
                continue
            cleaned_paras.append(p_clean)
            
        title = cleaned_paras[0] if cleaned_paras else f"Chapter {ch}"
        data = {
            'chapter': ch,
            'title': f"Chapter {ch}: {title}",
            'paragraphs': cleaned_paras[1:] if len(cleaned_paras) > 1 else cleaned_paras
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Suicide Hunter Ch {ch} saved: {len(data['paragraphs'])} paras")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error Ch {ch}: {e}")

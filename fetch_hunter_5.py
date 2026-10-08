import urllib.request
import re
import os
import json
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

def clean_text(text):
    text = re.sub(r'&#8217;', "'", text)
    text = re.sub(r'&#8220;', '"', text)
    text = re.sub(r'&#8221;', '"', text)
    text = re.sub(r'&#8230;', '...', text)
    return text.strip()

# 1. Suicide Hunter Ch 1-5
os.makedirs('novels/revival-hunter/raw', exist_ok=True)
for ch in range(1, 6):
    file_path = f'novels/revival-hunter/raw/ch{ch}.json'
    url = f'https://noveltranslationhub.com/novel/sss-class-suicide-hunter/chapter-{ch}/'
    try:
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
        
        # Extract title
        m_title = re.search(r'<h1[^>]*class="[^"]*entry-title[^"]*"[^>]*>(.*?)</h1>', html, re.I)
        title = clean_text(m_title.group(1)) if m_title else f"Chapter {ch}"
        
        # The chapter text is inside <div class="reading-content"> or inside <p> tags
        # Let's extract content inside entry-content or reading-content
        m_content = re.search(r'<div[^>]*class="[^"]*text-left[^"]*"[^>]*>(.*?)</div>\s*<div class="nav-links"', html, re.DOTALL)
        if not m_content:
            m_content = re.search(r'<div[^>]*class="[^"]*reading-content[^"]*"[^>]*>(.*?)</div>\s*<div class="nav-links"', html, re.DOTALL)
        if not m_content:
            m_content = re.search(r'<div[^>]*class="[^"]*reading-content[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
            
        content_html = m_content.group(1) if m_content else html
        paras = re.findall(r'<p[^>]*>(.*?)</p>', content_html, re.DOTALL)
        cleaned_paras = []
        for p in paras:
            p_clean = re.sub(r'<[^>]+>', '', p).strip()
            p_clean = clean_text(p_clean)
            if p_clean and 'noveltranslationhub' not in p_clean.lower() and 'patreon' not in p_clean.lower():
                cleaned_paras.append(p_clean)
                
        data = {'chapter': ch, 'title': title, 'paragraphs': cleaned_paras}
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Suicide Hunter Ch {ch} saved: {len(cleaned_paras)} paras")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error Hunter Ch {ch}: {e}")

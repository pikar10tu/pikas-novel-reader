"""แก้ครั้งเดียว (2026-10-09): ลบวงเล็บอังกฤษ/จีน, แท็ก HTML, ชื่อ เชอร์ลีย์ -> เชอร์รี  (แก้เฉพาะไฟล์ตอนแยก แล้วรัน sync_books.py)"""
import json, glob, re, os, sys
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
changed = 0
for f in sorted(glob.glob('novels/*/chapters/ch*.json')):
    ch = json.load(open(f, encoding='utf-8'))
    new = []
    for p in ch['paragraphs']:
        q = re.sub(r'\s?\((?=[^()]*[a-z])[^()ก-๙]*\)', '', p)        # (Pure Yang Aura)
        q = re.sub(r'\s?\([一-鿿]+\)', '', q)                 # (金孔子)
        q = re.sub(r'</?(em|strong|b|i)>', '', q)
        q = q.replace('เชอร์ลีย์', 'เชอร์รี')
        new.append(q)
    if new != ch['paragraphs']:
        ch['paragraphs'] = new
        json.dump(ch, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        changed += 1
print('แก้ไฟล์', changed, 'ไฟล์')

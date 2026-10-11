"""สร้างไฟล์รวมจากไฟล์ตอนแยก (novels/<id>/chapters/chNNN.json = ต้นฉบับจริง)
- index.json    : สารบัญ (เลขตอน + ชื่อตอน) ที่หน้าเว็บโหลด — เบามาก
- books.json    : อัปเดต chapterCount / dir / indexPath อัตโนมัติ (status เขียนเองได้ เช่น 'กำลังแปล', 'จบแล้ว')
รันทุกครั้งหลังเพิ่ม/แก้ตอน:  python sync_books.py
"""
import json, os, glob, sys
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

books = json.load(open('books.json', encoding='utf-8'))
for b in books:
    ndir = (b.get('dir') or os.path.dirname(b.pop('chaptersPath', ''))).rstrip('/')
    b.pop('chaptersPath', None)   # chapters.json (ไฟล์รวมทุกตอน) เลิกใช้แล้ว — เว็บโหลดไฟล์ตอนแยก
    files = sorted(glob.glob(os.path.join(ndir, 'chapters', 'ch*.json')))
    chapters = [json.load(open(f, encoding='utf-8')) for f in files]
    chapters.sort(key=lambda c: c['chapter'])
    index = [{'chapter': c['chapter'], 'title': c['title']} for c in chapters]
    json.dump(index, open(os.path.join(ndir, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    b['chapterCount'] = len(chapters)
    b['dir'] = ndir.replace('\\', '/') + '/'
    b['indexPath'] = os.path.join(ndir, 'index.json').replace('\\', '/')
    if not b.get('status') or b['status'].startswith('กำลังแปล ('):
        b['status'] = 'กำลังแปล'
    print(f"{b['id']}: {len(chapters)} ตอน")

json.dump(books, open('books.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('อัปเดต books.json / index.json แล้ว')

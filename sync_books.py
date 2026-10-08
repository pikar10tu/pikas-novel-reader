"""สร้างไฟล์รวมจากไฟล์ตอนแยก (novels/<id>/chapters/chNNN.json = ต้นฉบับจริง)
- chapters.json : ทุกตอนรวมเนื้อหา (สำรอง/ใช้กับสคริปต์เก่า)
- index.json    : สารบัญ (เลขตอน + ชื่อตอน) ที่หน้าเว็บโหลด — เบามาก
- books.json    : อัปเดต chapterCount อัตโนมัติ (status เขียนเองได้ เช่น 'กำลังแปล', 'จบแล้ว')
รันทุกครั้งหลังเพิ่ม/แก้ตอน:  python sync_books.py
"""
import json, os, glob, sys
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

books = json.load(open('books.json', encoding='utf-8'))
for b in books:
    ndir = os.path.dirname(b['chaptersPath'])
    files = sorted(glob.glob(os.path.join(ndir, 'chapters', 'ch*.json')))
    chapters = [json.load(open(f, encoding='utf-8')) for f in files]
    chapters.sort(key=lambda c: c['chapter'])
    json.dump(chapters, open(b['chaptersPath'], 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    index = [{'chapter': c['chapter'], 'title': c['title']} for c in chapters]
    json.dump(index, open(os.path.join(ndir, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    b['chapterCount'] = len(chapters)
    b['indexPath'] = os.path.join(ndir, 'index.json').replace('\\', '/')
    if not b.get('status') or b['status'].startswith('กำลังแปล ('):
        b['status'] = 'กำลังแปล'
    print(f"{b['id']}: {len(chapters)} ตอน")

json.dump(books, open('books.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('อัปเดต books.json / chapters.json / index.json แล้ว')

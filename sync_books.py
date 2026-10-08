import json
import os

with open('books.json', 'r', encoding='utf-8') as f:
    books = json.load(f)

for b in books:
    p = b.get('chaptersPath')
    if p and os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as cf:
            cdata = json.load(cf)
        actual_count = len(cdata)
        b['chapterCount'] = actual_count
        b['status'] = f"กำลังแปล (มี {actual_count} ตอน)"
        print(f"{b['id']}: actual={actual_count}")

with open('books.json', 'w', encoding='utf-8') as f:
    json.dump(books, f, ensure_ascii=False, indent=2)

print("Updated books.json successfully!")

import json

with open('novels/dragon/chapters/ch002.json', 'r', encoding='utf-8') as f:
    d2 = json.load(f)
d2['paragraphs'][76] = d2['paragraphs'][76].replace(' (จุดจบ)', '').replace(' (ความตื่นตา)', '')
with open('novels/dragon/chapters/ch002.json', 'w', encoding='utf-8') as f:
    json.dump(d2, f, ensure_ascii=False, indent=2)

with open('novels/dragon/chapters/ch016.json', 'r', encoding='utf-8') as f:
    d16 = json.load(f)
d16['paragraphs'][50] = d16['paragraphs'][50].replace(" (ทางช้างเผือก) สินะ", " ที่หมายถึงทางช้างเผือกสินะ")
with open('novels/dragon/chapters/ch016.json', 'w', encoding='utf-8') as f:
    json.dump(d16, f, ensure_ascii=False, indent=2)

print('Updated Ch 2 and Ch 16')

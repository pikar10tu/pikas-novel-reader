import json

def update_json(filepath, updater):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    updater(data)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Ch 2
def fix_ch2(d):
    d['paragraphs'][76] = d['paragraphs'][76].replace(' (หมัดเด็ด)', '').replace(' (แฝดสอง)', '')
update_json('novels/dragon/chapters/ch002.json', fix_ch2)

# Ch 16
def fix_ch16(d):
    d['paragraphs'][50] = d['paragraphs'][50].replace(' (ปีกแห่งทางออก)', '')
update_json('novels/dragon/chapters/ch016.json', fix_ch16)

# Ch 17
def fix_ch17(d):
    d['paragraphs'][59] = d['paragraphs'][59].replace("'มูน' (ดวงจันทร์)", "'มูน' ที่แปลว่าดวงจันทร์")
    d['paragraphs'][71] = d['paragraphs'][71].replace(' (แฝดสอง)', '')
update_json('novels/dragon/chapters/ch017.json', fix_ch17)

# Ch 51
def fix_ch51(d):
    d['paragraphs'][30] = d['paragraphs'][30].replace("'ป...' (ปะป๊า)", "'ป...' คล้ายจะเรียกปะป๊า")
update_json('novels/dragon/chapters/ch051.json', fix_ch51)

# Ch 55
def fix_ch55(d):
    d['paragraphs'][5] = d['paragraphs'][5].replace(' (หลงต้าลี่)', '')
update_json('novels/dragon/chapters/ch055.json', fix_ch55)

# Ch 57
def fix_ch57(d):
    d['paragraphs'][87] = d['paragraphs'][87].replace(' (สาวกระต่าย!)', ' สาวกระต่ายเรอะ!')
    d['paragraphs'][101] = d['paragraphs'][101].replace(' (เพราะขืนใครมาเห็นเข้า คงไม่มีทางอธิบายให้รอดได้แน่!)', ' เพราะขืนใครมาเห็นเข้าคงไม่มีทางอธิบายให้รอดได้แน่')
update_json('novels/dragon/chapters/ch057.json', fix_ch57)

# Ch 60
def fix_ch60(d):
    d['paragraphs'][28] = d['paragraphs'][28].replace(' (ในเมื่อหลอกตัวเองได้ ก็ปิดตาไปซะเลย!)', ' ในเมื่อหลอกตัวเองได้ก็ปิดตาไปเสียเลย!')
update_json('novels/dragon/chapters/ch060.json', fix_ch60)

# Ch 67
def fix_ch67(d):
    d['paragraphs'][45] = d['paragraphs'][45].replace(' (ด้วยกำปั้น!)', ' ด้วยกำปั้นอยู่แล้ว')
update_json('novels/dragon/chapters/ch067.json', fix_ch67)

# Ch 70
def fix_ch70(d):
    d['paragraphs'][12] = d['paragraphs'][12].replace(' (ทำหน้าใสซื่อ):', 'ทำหน้าใสซื่อ')
update_json('novels/dragon/chapters/ch070.json', fix_ch70)

# Ch 94
def fix_ch94(d):
    d['paragraphs'][24] = d['paragraphs'][24].replace('พี่สาวของหนู (โนอา)', 'พี่โนอาของหนู')
update_json('novels/dragon/chapters/ch094.json', fix_ch94)

print('Successfully cleaned up parenthesis warnings in chapters 2, 16, 17, 51, 55, 57, 60, 67, 70, 94')

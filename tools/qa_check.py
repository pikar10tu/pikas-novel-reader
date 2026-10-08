"""QA ตรวจบทแปลอัตโนมัติ
ใช้: python tools/qa_check.py                 (ทุกเรื่อง)
     python tools/qa_check.py dragon          (เฉพาะเรื่อง)
     python tools/qa_check.py dragon 101-120  (เฉพาะช่วงตอน)
ตรวจ: ชื่อต้องห้าม (จาก GLOSSARY.md ส่วน 'ห้ามใช้'), อังกฤษ/จีนค้าง, แท็ก HTML,
      ย่อหน้ายาวเกิน, สัดส่วนความยาวเทียบต้นฉบับ, ไฟล์ตอนแยกกับ chapters.json ไม่ตรงกัน
exit code 1 ถ้ามี ERROR
"""
import json, glob, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# คำอังกฤษที่อนุญาตให้อยู่ในเนื้อหาได้ (ระดับ/ศัพท์เกมที่คนไทยใช้ทับตรงๆ)
ALLOWED_LATIN = {'SSS', 'SS', 'EX', 'OK', 'PK', 'NPC', 'LIVE', 'Bad', 'End', 'Enter', 'HP', 'MP', 'VIP'}
RAW_DIRS = {'dragon': 'raw_chapters/v1c{n}.json'}   # เพิ่มเรื่องอื่นได้ เช่น 'ccg': 'novels/cultivation-chat-group/raw/ch{n}.json'
MIN_RATIO = 0.65     # ความยาวไทย/อังกฤษ ต่ำกว่านี้ = สงสัยตกหล่น (ไทยปกติ ~0.75-1.1)
MAX_PARA = 600       # ตัวอักษรต่อย่อหน้า

def load_banned(novel_dir):
    """อ่านตาราง 'ห้ามใช้' ใน GLOSSARY.md: | ❌ คำผิด | ✅ คำถูก | ..."""
    banned = {}
    g = os.path.join(novel_dir, 'GLOSSARY.md')
    if not os.path.exists(g):
        return banned
    for line in open(g, encoding='utf-8'):
        m = re.match(r'\|\s*❌\s*([^|]+?)\s*\|\s*✅\s*([^|]+?)\s*\|', line)
        if m:
            for bad in m.group(1).split('/'):
                banned[bad.strip()] = m.group(2).strip()
    return banned

def raw_paras(book_id, n):
    pat = RAW_DIRS.get(book_id)
    if not pat:
        return None
    p = pat.format(n=n)
    if not os.path.exists(p):
        return None
    r = json.load(open(p, encoding='utf-8'))
    return r['paragraphs'] if isinstance(r, dict) else r

def parse_range(s):
    a, _, b = s.partition('-')
    return int(a), int(b or a)

def main():
    books = json.load(open('books.json', encoding='utf-8'))
    only = sys.argv[1] if len(sys.argv) > 1 else None
    rng = parse_range(sys.argv[2]) if len(sys.argv) > 2 else None
    errors = warns = 0
    for b in books:
        if only and b['id'] != only:
            continue
        ndir = os.path.dirname(b['chaptersPath'])
        banned = load_banned(ndir)
        files = sorted(glob.glob(os.path.join(ndir, 'chapters', 'ch*.json')))
        agg = {c['chapter']: c for c in json.load(open(b['chaptersPath'], encoding='utf-8'))}
        print(f"\n=== {b['id']} ({len(files)} ตอน, คำต้องห้าม {len(banned)} คำ)")
        nums = []
        for f in files:
            ch = json.load(open(f, encoding='utf-8'))
            n = ch['chapter']; nums.append(n)
            if rng and not (rng[0] <= n <= rng[1]):
                continue
            issues = []
            text = '\n'.join(ch['paragraphs'])
            for bad, good in banned.items():
                if bad in text:
                    issues.append(('ERROR', f"ชื่อต้องห้าม '{bad}' x{text.count(bad)} -> ใช้ '{good}'"))
            if re.search(r'<[^>]+>|\*\*|__', text.replace('* * *', '')):
                issues.append(('ERROR', 'มีแท็ก HTML หรือ Markdown (<em>, **) ในเนื้อหา'))
            for m in re.findall(r'\([^()]*[a-z][^()]*\)', text):
                issues.append(('ERROR', f'วงเล็บภาษาต้นฉบับ {m[:40]}'))
            cjk = re.findall(r'[぀-ヿ一-鿿가-힯]+', text)
            if cjk:
                issues.append(('ERROR', f'อักษรจีน/ญี่ปุ่น/เกาหลีค้าง {cjk[:3]}'))
            latin = {w for w in re.findall(r'[A-Za-z]{2,}', text) if w not in ALLOWED_LATIN}
            if latin:
                issues.append(('WARN', f'คำอังกฤษ {sorted(latin)[:6]}'))
            if '[NOTE' in text:
                issues.append(('WARN', 'ยังมี [NOTE: ...] ค้างในเนื้อหา'))
            long = [i + 1 for i, p in enumerate(ch['paragraphs']) if len(p) > MAX_PARA]
            if long:
                issues.append(('WARN', f'ย่อหน้ายาวเกิน {MAX_PARA} ตัวอักษร: ย่อหน้าที่ {long[:5]}'))
            if any(not p.strip() for p in ch['paragraphs']):
                issues.append(('WARN', 'มีย่อหน้าว่าง'))
            rp = raw_paras(b['id'], n)
            if rp:
                ratio = sum(map(len, ch['paragraphs'])) / max(1, sum(map(len, rp)))
                if ratio < MIN_RATIO:
                    issues.append(('ERROR', f'สั้นกว่าต้นฉบับผิดปกติ (ไทย/อังกฤษ = {ratio:.2f}, ย่อหน้า {len(ch["paragraphs"])}/{len(rp)}) อาจตกหล่น'))
            a = agg.get(n)
            if not a or a['paragraphs'] != ch['paragraphs'] or a['title'] != ch['title']:
                issues.append(('WARN', 'ไม่ตรงกับ chapters.json — รัน python sync_books.py'))
            for lvl, msg in issues:
                print(f"  [{lvl}] ตอน {n}: {msg}")
                if lvl == 'ERROR': errors += 1
                else: warns += 1
        missing = sorted(set(range(1, max(nums, default=0) + 1)) - set(nums))
        if missing:
            print(f"  [ERROR] ตอนที่หายไป: {missing}"); errors += 1
    print(f"\nสรุป: ERROR {errors} | WARN {warns}")
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()

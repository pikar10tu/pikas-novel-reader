"""ทำความสะอาดต้นฉบับที่ดึงจากเว็บ ก่อนส่งให้ AI แปล (ทำครั้งเดียวต่อไฟล์ ก่อนเริ่มแปล)
ใช้: python tools/clean_raw.py novels/<เรื่อง>/raw            ดูว่าจะลบอะไร (ไม่แก้ไฟล์)
     python tools/clean_raw.py novels/<เรื่อง>/raw --write    เขียนทับจริง
ทำ: ย้ายเชิงอรรถผู้แปลอังกฤษ ([1] ..., Footnotes:) ไปช่อง notes, ถอด &nbsp; &amp; ฯลฯ, ลบแท็กโครงหน้าเว็บ (<p> <br> <a>), ลบบรรทัดขยะท้ายหน้า (ฟอร์มล็อกอิน,
    ลิงก์กลับเว็บ, โฆษณาตอนถัดไป), ลบย่อหน้าว่าง
ไม่ทำ: แท็กเน้นคำ (<em> <i> <strong>) เก็บไว้ เพราะบอกได้ว่าเป็นความคิดในใจ/เสียงเน้น
ห้ามรันกับต้นฉบับ dragon (raw_chapters/) — บทแปลเดิมเทียบย่อหน้า 1:1 กับไฟล์ชุดนั้นอยู่แล้ว
"""
import glob, html, json, os, re, sys

sys.stdout.reconfigure(encoding='utf-8')

# บรรทัดที่เป็นส่วนของหน้าเว็บ ไม่ใช่เนื้อเรื่อง (เทียบทั้งบรรทัด ไม่สนตัวพิมพ์)
JUNK = [
    r'(?:←\s*)?back to\s+(?:\S+\s+){0,4}(?:hub|home|index|novel|series|site|top)',   # ลิงก์กลับเว็บ ไม่ใช่ 'Back to my Hell.'
    r'username(?: or email address)?\s*\*?',
    r'email address\s*\*?',
    r'password\s*\*?',
    r'register for this site\.?',
    r'remember me',
    r'(?:log ?in|sign ?up)?\s*\|?\s*(?:lost your password\??)?',
    r'(?:previous|next) chapter|table of contents|index',
    r'(?:translator|editor|tl|ed|proofreader|formatter|raws?)s?\s*:.*',
    r'.*(?:patreon|discord|ko-fi|support us).*',
    r'your email address will not be published.*|name \*|email \*|website',
    r'save my name, email, and website.*|©.*all rights reserved\.?',
    r'please enter your username or email address.*',
]
JUNK_RE = re.compile(r'^(?:' + '|'.join(JUNK) + r')$', re.I)
LAYOUT_TAGS = re.compile(r'</?(?:p|br|a|span|div|sup|u)(?:\s[^>]*)?/?>', re.I)


def clean_para(p):
    p = html.unescape(p).replace('\xa0', ' ')
    p = LAYOUT_TAGS.sub('', p)
    return re.sub(r'\s+', ' ', p).strip()


# หัวข้อเชิงอรรถ: ทุกบรรทัดหลังจากนี้ถึงท้ายตอน = โน้ตผู้แปลอังกฤษ
FOOTNOTE_HEAD = re.compile(r'^(?:<[^>]+>)*\s*[\[(]?\s*(?:footnotes?|tln?|tl notes?|t/n|note)\s*[\])]?\s*:?\s*(?:<[^>]+>)*\s*:?$', re.I)
# โน้ตบรรทัดเดียว: [1] ..., [TN: ...], (TL: ...)
FOOTNOTE = re.compile(r'^(?:\[\d+\]\s|[\[(]\s*(?:t/?n|tln?|note)\s*:)', re.I)


def clean(paras):
    """คืน (ย่อหน้าที่เหลือ, ย่อหน้าที่ลบ, เชิงอรรถของผู้แปลอังกฤษ)
    เชิงอรรถย้ายไปช่อง notes — ไม่ต้องแปล แต่ AI ผู้แปลใช้เป็นข้อมูลประกอบได้"""
    kept, dropped, notes = [], [], []
    in_notes = False
    for p in paras:
        c = clean_para(p)
        if not c or JUNK_RE.match(c):
            dropped.append(p)
        elif FOOTNOTE_HEAD.match(c):
            in_notes = True
        elif in_notes or FOOTNOTE.match(c):
            notes.append(c)
        else:
            kept.append(c)
    return kept, dropped, notes


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    folder = os.path.normpath(args[0])
    if os.path.basename(folder) == 'raw_chapters':
        sys.exit('ห้ามรันกับ raw_chapters/ (ต้นฉบับ dragon) — ดูคำอธิบายต้นไฟล์')
    write = '--write' in sys.argv
    for f in sorted(glob.glob(os.path.join(folder, '*.json'))):
        data = json.load(open(f, encoding='utf-8'))
        paras = data['paragraphs'] if isinstance(data, dict) else data
        kept, dropped, notes = clean(paras)
        if dropped or notes or kept != paras:
            print(f"{os.path.basename(f)}: ลบ {len(dropped)} ย่อหน้า, ย้ายเชิงอรรถ {len(notes)}, เหลือ {len(kept)}"
                  + ''.join(f"\n   - {d[:70]}" for d in dropped[:8]))
        if write and kept != paras:
            if not isinstance(data, dict):
                data = {}
            data['paragraphs'] = kept
            if notes:
                data['notes'] = data.get('notes', []) + notes
            with open(f, 'w', encoding='utf-8', newline='') as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
    if not write:
        print('\n(ยังไม่ได้แก้ไฟล์ — เพิ่ม --write เพื่อเขียนทับ)')


if __name__ == '__main__':
    main()

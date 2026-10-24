"""QA ตรวจบทแปลอัตโนมัติ
ใช้: python tools/qa_check.py                 (ทุกเรื่อง)
     python tools/qa_check.py dragon          (เฉพาะเรื่อง)
     python tools/qa_check.py dragon 101-120  (เฉพาะช่วงตอน)
ตรวจ: ชื่อต้องห้าม (จาก GLOSSARY.md ส่วน 'ห้ามใช้'), อังกฤษ/จีนค้าง, แท็ก HTML,
      ย่อหน้ายาวเกิน, สัดส่วนความยาวเทียบต้นฉบับ, ไฟล์ตอนแยกกับ chapters.json ไม่ตรงกัน,
      ย่อหน้า 1:1 กับต้นฉบับ, 'เธอ' ในบทบรรยาย, ชื่อเฉพาะในต้นฉบับที่ยังไม่อยู่ใน GLOSSARY
exit code 1 ถ้ามี ERROR
"""
import json, glob, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
from tools import glossary   # noqa: E402

# คำอังกฤษที่อนุญาตให้อยู่ในเนื้อหาได้ (ระดับ/ศัพท์เกมที่คนไทยใช้ทับตรงๆ)
ALLOWED_LATIN = {'SSS', 'SS', 'EX', 'OK', 'PK', 'NPC', 'LIVE', 'Bad', 'End', 'Enter', 'HP', 'MP', 'VIP', 'GG'}
# ค่าตั้งรายเรื่องอยู่ใน novels/<เรื่อง>/novel.json (ดู load_cfg) — เพิ่มเรื่องใหม่ไม่ต้องแก้โค้ด
MIN_RATIO = 0.65     # ความยาวไทย/อังกฤษ ต่ำกว่านี้ = สงสัยตกหล่น (ไทยปกติ ~0.75-1.1)
MAX_PARA = 600       # ตัวอักษรต่อย่อหน้า
TERU_MAX = 10        # 'เธอ' ต่อหมื่นตัวอักษร เกินนี้ = สำนวนแปลตรงตัว (ตอน 81-100 อยู่ที่ ~0.5, ตอน 101-140 พุ่งไป ~30)
MODERN_MAX = 15      # 'ฉัน'/'นาย' ในบทพูดต่อหมื่นตัวอักษร (dragon ใช้ ข้า/เจ้า: ปกติ <8, Ch 238 ก่อนแก้ ~40)
NAI = r'(?<!เจ้า)นาย(?!พล|ทหาร|ท่าน|กอง|ก[^ ]|หน้า|ทุน|อำเภอ|ช่าง|ร้อย|สิบ|ห้าง)'
STIFF = ['อย่างไรก็ตาม', 'ในขณะเดียวกัน', 'ได้รับการ', 'อันหรูหรา']   # คำเชื่อมสำนวนแปล
# ใครห้ามเรียกพ่อด้วยคำไหน: {เรื่อง: [(ชื่อลูก, คำต้องห้าม, คำที่ถูก)]}
# ย่อหน้าที่ตรวจด้วยตาแล้วว่าถูก (บทบรรยาย / ลีออนคุยกับมูน) {เรื่อง: {(ตอน, ย่อหน้า 1-based)}}
# คำขึ้นต้นตัวใหญ่ในต้นฉบับที่ไม่ใช่ชื่อเฉพาะ (ไม่ต้องอยู่ใน GLOSSARY)
NOT_NAMES = set('''I Dad Daddy Mom Mommy Mother Father Mama Papa Your Majesty Highness Queen King Princess Prince
Lord Lady Sir Miss Mr Mrs Ms Madam Teacher Master Captain Head Maid Dragon Dragons Slayer Silver Empire Imperial
Sanctuary Temple Army God Oh Ah Hmm Huh Okay Ok Alright Well Yes No Hey Wow Chapter Chap
Monday Tuesday Wednesday Thursday Friday Saturday Sunday Mondays Tuesdays Saturdays Sundays
January February March April May June July August September October November December
English French Chinese Headmaster Principal Vice Auntie Uncle General Classmate Girl Boy Brother Sister'''.split())

def narration(p):
    """ตัดบทพูด/ความคิดในเครื่องหมายคำพูดออก เหลือแต่บทบรรยาย"""
    if p.count('"') % 2:   # คำพูดยาวหลายย่อหน้า (เปิด/ปิดไม่ครบในย่อหน้านี้) = นับเป็นบทพูด
        return ''
    return re.sub(r'"[^"]*"|\'[^\']*\'|‘[^’]*’', '', p)

def new_names(rp, gloss_lower):
    """ชื่อเฉพาะที่ขึ้นต้นตัวใหญ่กลางประโยค >= 2 ครั้ง และไม่มีใน GLOSSARY"""
    cnt, body = {}, rp[1:]   # rp[0] = ชื่อตอน (Title Case ทุกคำ)
    text = ' '.join(body)
    for p in body:
        for w in re.findall(r'(?<=[a-z,;] )([A-Z][a-z]{2,})', p):
            singular = w[:-1] if w.endswith('s') else w   # Hunters / Kings -> มีใน GLOSSARY แบบเอกพจน์
            if w not in NOT_NAMES and w.lower() not in gloss_lower and singular.lower() not in gloss_lower:
                cnt[w] = cnt.get(w, 0) + 1
    # คำที่โผล่เป็นตัวเล็กในตอนเดียวกันด้วย = คำนามทั่วไป (Magic/magic) ไม่ใช่ชื่อ
    return sorted(w for w, c in cnt.items() if c >= 2 and not re.search(r'\b' + w.lower() + r'\b', text))

# ความยาวไทย/ต้นฉบับขั้นต่ำ ตามภาษาต้นฉบับ (จีน 1 ตัวอักษร ≈ ไทย 3.5-4.5 ตัวอักษร — ccg Ch 1-5 อยู่ที่ ~4.1)
MIN_RATIO_BY_LANG = {'en': MIN_RATIO, 'zh': 2.5, 'ko': 1.0, 'ja': 1.0}
ARCHAIC = ['ไฉน', 'ดั่ง', 'ประหนึ่ง', 'มิได้', 'มิใช่', 'หาใช่']
ARCHAIC_MAX = 3      # คำโบราณต่อตอน (ตัวละครพูดโบราณจริงๆ มีได้บ้าง)

CFG_DEFAULTS = {
    'raw': None,                 # รูปแบบที่อยู่ต้นฉบับ เช่น "novels/x/raw/ch{n}.json" ({n} หรือ {n:03d})
    'source_lang': 'en',         # en / zh / ko / ja — ใช้ตั้งเกณฑ์ความยาว และเช็กชื่อใหม่ได้เฉพาะ en
    'genre': None,               # western-fantasy / xianxia / modern-korean / modern-xianxia (ดู GENRE_*.md)
    'strict_from': 1,            # ตั้งแต่ตอนนี้ย่อหน้าต้องตรงต้นฉบับ 1:1
    'names_from': 1,             # ตั้งแต่ตอนนี้เช็กชื่อในต้นฉบับที่ยังไม่อยู่ใน GLOSSARY
    'vols': [],                  # [[ตอนแรกของเล่ม, เล่ม], ...]
    'no_teru_narration': False,  # ห้าม 'เธอ' ในบทบรรยาย (เรื่องย้อนยุค/แฟนตาซี) — เรื่องยุคปัจจุบันใช้ได้
    'classical_pronouns': False, # ตัวละครหลักใช้ ข้า/เจ้า — เตือนเมื่อ ฉัน/นาย ในบทพูดหนาแน่น
    'no_archaic': False,         # ห้ามคำโบราณ ไฉน/ดั่ง/มิได้ (dragon เลือกโทน A+C)
    'father': [],                # [[ชื่อลูก, คำต้องห้าม, คำที่ถูก], ...]
    'father_ok': [],             # [[ตอน, ย่อหน้า 1-based], ...] ที่ตรวจด้วยตาแล้วว่าถูก
    'dup_ok': [],                # ตอนที่ย่อหน้าซ้ำเป็นก้อนโดยเจตนาของผู้แต่ง
    'dialogue_ok': [],           # ตอนที่บทพูด/บรรยายไม่ตรงต้นฉบับโดยเจตนา (ความคิด/จดหมาย) ตรวจด้วยตาแล้ว
}

def load_cfg(ndir):
    p = os.path.join(ndir, 'novel.json')
    cfg = dict(CFG_DEFAULTS)
    if os.path.exists(p):
        cfg.update(json.load(open(p, encoding='utf-8')))
    return cfg

def load_banned(novel_dir):
    """ตาราง 'ห้ามใช้' ใน GLOSSARY.md: | ❌ คำผิด | ✅ คำถูก | ... -> {คำผิด: คำถูก}"""
    return glossary.parse(os.path.join(novel_dir, 'GLOSSARY.md')).banned

def book_dir(b):
    """โฟลเดอร์ของเรื่อง (books.json: 'dir' — รองรับ 'chaptersPath' แบบเก่า)"""
    return (b.get('dir') or os.path.dirname(b['chaptersPath'])).rstrip('/')

def _bigrams(s):
    return {s[i:i + 2] for i in range(len(s) - 1)}

def dup_blocks(P, thr=0.35):
    """หาก้อนย่อหน้าที่ซ้ำ: มี >=3 คู่ที่ห่างกันเท่ากัน (d) และคล้ายกันเกิน thr
    = อาการเกลาแล้วเขียนทับไม่หมด ทำให้ย่อหน้าเก่าค้างต่อท้าย (เคยเกิดใน Ch 107)"""
    B = [_bigrams(p) for p in P]
    found = {}
    for i in range(len(P)):
        for d in range(1, 21):
            j = i + d
            if j < len(P) and len(P[i]) > 30 and len(B[i] & B[j]) / max(1, len(B[i] | B[j])) > thr:
                found.setdefault(d, []).append(i + 1)
    return {d: v for d, v in found.items() if len(v) >= 3}

def raw_paras(cfg, n):
    pat = cfg.get('raw')
    if not pat:
        return None
    p = pat.format(n=n)
    if not os.path.exists(p):
        return None
    r = json.load(open(p, encoding='utf-8'))
    return r['paragraphs'] if isinstance(r, dict) else r

def body_paras(th, raw):
    """ตัดบรรทัดชื่อตอนออกทั้งสองฝั่งก่อนเทียบย่อหน้า 1:1"""
    had_title = bool(th and th[0].startswith('ตอนที่'))
    if had_title:
        th = th[1:]
    if raw and re.search(r'chap(?:ter)?\s*\d|^第\s*\d+\s*章', raw[0], re.I):
        raw = raw[1:]
    elif had_title and raw and len(raw[0]) < 80 and not re.search(r'[.!?"”…:;,]\s*$', raw[0]):
        raw = raw[1:]   # ชื่อตอนเปล่าๆ ไม่มีคำว่า Chapter (เช่น revival-hunter: "The Greatest Envy")
    return th, raw

def first_drift(th, raw):
    """ย่อหน้าแรกที่ความยาวไทย/อังกฤษผิดสัดส่วน = จุดที่น่าจะเริ่มเลื่อน"""
    for i, (t, e) in enumerate(zip(th, raw)):
        if len(e) > 60 and not 0.4 < len(t) / len(e) < 2.0:
            return i + 1
    return None

def _plain(s):
    return re.sub(r'<[^>]+>', '', s)

def truncated_paras(th, raw, min_len=80, ratio=0.5):
    """ย่อหน้าที่ไทยสั้นไม่ถึงครึ่งของต้นฉบับคู่กัน = แปลแค่ครึ่งประโยคแรกแล้วทิ้งที่เหลือ
    (Ch 345-352 เคยเจอ 21 ย่อหน้า — จำนวนย่อหน้าตรง 1:1 แต่เนื้อหาหายไปครึ่ง)"""
    return [i + 1 for i, (t, e) in enumerate(zip(th, raw))
            if len(_plain(e)) > min_len and len(t) / len(_plain(e)) < ratio]

def _is_dialogue(s):
    return bool(re.match(r'^\s*(<[^>]+>)*\s*["“]', s))

def dialogue_mismatch(th, raw):
    """ย่อหน้าที่ต้นฉบับเป็นบทพูดแต่ไทยเป็นบทบรรยาย (หรือกลับกัน)
    ถ้าเจอหลายจุดติดกัน = ช่วงนั้นไม่ได้แปลจากต้นฉบับ (Ch 354 เคยแต่งฉากใหม่ 39 ย่อหน้าโดยจำนวนย่อหน้ายังตรง)
    ความคิดในใจที่ไทยใส่ ' ไม่นับ เพราะต้นฉบับมักไม่มีเครื่องหมาย"""
    return [i + 1 for i, (t, e) in enumerate(zip(th, raw)) if _is_dialogue(t) != _is_dialogue(e)]

def modern_density(paras):
    """'ฉัน' + 'นาย' (สรรพนาม ไม่นับ เจ้านาย/นายพล ฯลฯ) ในบทพูด/ความคิด ต่อหมื่นตัวอักษร"""
    q = ' '.join(x for p in paras for t in re.findall(r'"([^"]*)"|\'([^\']*)\'', p) for x in t)
    L = max(1, len('\n'.join(paras))) / 10000
    return (q.count('ฉัน') + len(re.findall(NAI, q))) / L

def header_issues(ch, n, vols):
    """เลขตอนในย่อหน้าแรก/title ต้องตรงกับไฟล์ และ vol ต้องตรงกับเล่ม (Ch 237-245 เคยใช้เลขต้นฉบับ + vol 1)"""
    out = []
    p0 = ch['paragraphs'][0] if ch['paragraphs'] else ''
    for where, t in (('ย่อหน้าแรก', p0), ('title', ch.get('title', ''))):
        m = re.match(r'ตอนที่\s*(\d+)', t)
        if m and int(m.group(1)) != n:
            out.append(('ERROR', f"{where} เขียน 'ตอนที่ {m.group(1)}' แต่ไฟล์นี้คือตอน {n} — ห้ามใช้เลขตอนของต้นฉบับ"))
    vol = max((v for start, v in vols if n >= start), default=None)
    if vol and ch.get('vol') != vol:
        out.append(('ERROR', f"vol = {ch.get('vol')} แต่ตอน {n} อยู่เล่ม {vol}"))
    return out

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
        ndir = book_dir(b)
        cfg = load_cfg(ndir)
        g = glossary.parse(os.path.join(ndir, 'GLOSSARY.md'))
        banned, gloss_lower = g.banned, g.text.lower()
        files = sorted(glob.glob(os.path.join(ndir, 'chapters', 'ch*.json')))
        ip = os.path.join(ndir, 'index.json')
        toc = {c['chapter']: c['title'] for c in json.load(open(ip, encoding='utf-8'))} if os.path.exists(ip) else {}
        print(f"\n=== {b['id']} ({len(files)} ตอน, คำต้องห้าม {len(banned)} คำ)")
        for no, msg in g.problems:
            print(f"  [ERROR] GLOSSARY.md บรรทัด {no}: {msg}"); errors += 1
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
            if '[SKIPPED' in text:
                issues.append(('ERROR', f"มีฉากที่ AI ผู้แปลข้ามไว้ {text.count('[SKIPPED')} จุด — ส่งให้ Claude แปลต่อ"))
            if '[NOTE' in text:
                issues.append(('WARN', 'ยังมี [NOTE: ...] ค้างในเนื้อหา'))
            long = [i + 1 for i, p in enumerate(ch['paragraphs']) if len(p) > MAX_PARA]
            if long:
                issues.append(('WARN', f'ย่อหน้ายาวเกิน {MAX_PARA} ตัวอักษร: ย่อหน้าที่ {long[:5]}'))
            L = max(1, len(text)) / 10000
            teru = text.count('เธอ') / L
            if cfg['no_teru_narration'] and teru > TERU_MAX:
                issues.append(('WARN', f"สำนวนแปลตรงตัว: 'เธอ' {teru:.0f} ครั้ง/หมื่นตัวอักษร (เกณฑ์ {TERU_MAX}) — บทบรรยายใช้ นาง/แก/ชื่อ"))
            if cfg['classical_pronouns']:
                modern = modern_density(ch['paragraphs'])
                if modern > MODERN_MAX:
                    issues.append(('WARN', f"สรรพนาม 'ฉัน/นาย' ในบทพูด {modern:.0f} ครั้ง/หมื่นตัวอักษร (เกณฑ์ {MODERN_MAX}) — เรื่องนี้ใช้ ข้า/เจ้า (เคยหลุดใน Ch 237-243)"))
            issues += header_issues(ch, n, [tuple(v) for v in cfg['vols']])
            stiff = {w: text.count(w) for w in STIFF if text.count(w) >= 3}
            if stiff:
                issues.append(('WARN', f'คำเชื่อมสำนวนแปลหนาแน่น {stiff}'))
            fw = re.findall(r'[！？，。：；（）]', text)
            if fw:
                issues.append(('ERROR', f'เครื่องหมายแบบตัวเต็ม (จีน) ค้าง x{len(fw)}'))
            if re.search(r'[“”‘’]', text):
                issues.append(('WARN', 'ใช้เครื่องหมายคำพูดโค้ง “ ” หรือ ‘ ’ — ให้ใช้ " (หรือ \' สำหรับคำพูดซ้อน) ตรงตามตอนอื่น'))
            teru_n = [i + 1 for i, p in enumerate(ch['paragraphs']) if 'เธอ' in narration(p)]
            if cfg['no_teru_narration'] and teru_n:
                issues.append(('WARN', f"'เธอ' ในบทบรรยาย ย่อหน้าที่ {teru_n[:6]} — ใช้ นาง/แก/ชื่อ (ในบทพูดใช้ได้)"))
            if cfg['no_archaic']:
                arch = {w: text.count(w) for w in ARCHAIC if w in text}
                if sum(arch.values()) > ARCHAIC_MAX:
                    issues.append(('WARN', f'คำโบราณ {arch} — เรื่องนี้ใช้ภาษาปัจจุบัน ยกเว้นตัวละครที่พูดโบราณจริงๆ (ดู STYLE_SAMPLES)'))
            father_ok = {tuple(x) for x in cfg['father_ok']}
            for i, p in enumerate(ch['paragraphs']):
                for kid, bad, good in cfg['father']:
                    others = [k for k, _, _ in cfg['father'] if k != kid]
                    if (n, i + 1) in father_ok:
                        continue
                    if kid in p and bad in p and not any(o in p for o in others):
                        issues.append(('WARN', f"ย่อหน้า {i + 1}: {kid} คู่กับ '{bad}' — ถ้า{kid}เป็นคนพูด ต้องใช้ '{good}'"))
            for d, idx in ({} if n in cfg['dup_ok'] else dup_blocks(ch['paragraphs'])).items():
                issues.append(('ERROR', f'ย่อหน้าซ้ำเป็นก้อน (ห่างกัน {d}) ที่ย่อหน้า {idx[:6]} — น่าจะเหลือย่อหน้าฉบับเก่าค้าง หรือตัดต่อพลาด'))
            if any(not p.strip() for p in ch['paragraphs']):
                issues.append(('WARN', 'มีย่อหน้าว่าง'))
            rp = raw_paras(cfg, n)
            if rp:
                ratio = sum(map(len, ch['paragraphs'])) / max(1, sum(map(len, rp)))
                notes = re.findall(r'\(ผู้แปล:[^()]*(?:\([^()]*\)[^()]*)*\)', text)   # โน้ตผู้แปลที่กฎอนุญาต ไม่นับ
                np_th = len(re.findall(r'\(', text)) - sum(n.count('(') for n in notes)
                np_raw = len(re.findall(r'\(', ' '.join(rp)))
                if np_th > np_raw:
                    issues.append(('WARN', f'วงเล็บมากกว่าต้นฉบับ ({np_th} > {np_raw}) — ห้ามเติมคำอธิบาย/ความเห็นผู้แปลในวงเล็บ'))
                if re.search(r'[￣︿◕ᴗ✿]', text):
                    issues.append(('WARN', 'มีอีโมจิตัวอักษร (kaomoji) — ตัดออกหรือบรรยายเป็นคำ'))
                diff = len(ch['paragraphs']) - len(rp)
                if n >= cfg['strict_from']:
                    th_b, raw_b = body_paras(ch['paragraphs'], rp)
                    if len(th_b) != len(raw_b):
                        hint = first_drift(th_b, raw_b)
                        issues.append(('ERROR', f'ย่อหน้าไม่ตรงต้นฉบับ 1:1 (ไทย {len(th_b)} / ต้นฉบับ {len(raw_b)} ไม่นับชื่อตอน)'
                                       + (f' เริ่มเพี้ยนราวย่อหน้าที่ {hint}' if hint else '') + ' — ตกหล่น ซ้ำ หรือแต่งเพิ่ม'))
                elif diff < -5:   # ย่อหน้าน้อยกว่าต้นฉบับมาก = อาจตกหล่น (มากกว่าไม่เป็นไร ตอนต้นๆ แตกย่อหน้าเยอะ)
                    issues.append(('WARN', f'จำนวนย่อหน้าต่างจากต้นฉบับ {diff:+d} ({len(ch["paragraphs"])}/{len(rp)}) — เช็กว่าตกหล่นหรือซ้ำ'))
                if n >= cfg['strict_from'] and cfg['source_lang'] in ('en', 'ko', 'ja'):
                    th_b, raw_b = body_paras(ch['paragraphs'], rp)
                    if len(th_b) == len(raw_b):
                        tr = truncated_paras(th_b, raw_b)
                        if tr:
                            issues.append(('ERROR' if len(tr) >= 3 else 'WARN',
                                           f'ย่อหน้าที่แปลไม่ครบ (สั้นกว่าครึ่งของต้นฉบับ) {len(tr)} จุด: {tr[:8]} — แปลให้ครบทั้งย่อหน้า'))
                        dm = dialogue_mismatch(th_b, raw_b)
                        if len(dm) >= 4 and n not in cfg['dialogue_ok']:
                            issues.append(('ERROR', f'บทพูด/บทบรรยายไม่ตรงต้นฉบับ {len(dm)} จุด: {dm[:10]} — ช่วงนี้อาจไม่ได้แปลจากต้นฉบับ (แต่งเอง/ข้ามแล้วเติม) เทียบทีละย่อหน้า'))
                if cfg['source_lang'] == 'en' and n >= cfg['names_from'] and gloss_lower:
                    nn = new_names(rp, gloss_lower)
                    if nn:
                        issues.append(('WARN', f'ชื่อเฉพาะในต้นฉบับที่ยังไม่อยู่ใน GLOSSARY: {nn[:8]} — เสนอใน Proposed New Terms'))
                if ratio < MIN_RATIO_BY_LANG.get(cfg['source_lang'], MIN_RATIO):
                    # ตอนก่อน strict_from = ฉบับเก่าที่รอแปลใหม่ แจ้งเป็น WARN ไม่บล็อก commit
                    lvl = 'ERROR' if n >= cfg['strict_from'] else 'WARN'
                    issues.append((lvl, f'สั้นกว่าต้นฉบับผิดปกติ (ไทย/ต้นฉบับ = {ratio:.2f}, ย่อหน้า {len(ch["paragraphs"])}/{len(rp)}) อาจตกหล่น'))
            if toc.get(n) != ch['title']:
                issues.append(('WARN', 'สารบัญ index.json ไม่ตรงกับไฟล์ตอน — รัน python sync_books.py'))
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

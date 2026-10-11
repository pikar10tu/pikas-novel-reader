"""อ่าน GLOSSARY.md เป็นข้อมูลมีโครงสร้าง + ตรวจว่าตารางไม่พัง
GLOSSARY.md ยังเป็นต้นฉบับจริง (คนและ AI ผู้แปลอ่าน/แก้ไฟล์นี้) โมดูลนี้แค่ parse ให้เครื่องใช้
ตรวจเอง: python tools/glossary.py [novels/<เรื่อง>]
"""
import os, re, sys
from dataclasses import dataclass, field


@dataclass
class Table:
    section: str            # หัวข้อ ## ที่ตารางอยู่
    line: int               # บรรทัดของหัวตาราง (1-based)
    headers: list
    rows: list = field(default_factory=list)   # [(บรรทัด, [cell, ...])]


@dataclass
class Glossary:
    path: str
    tables: list
    banned: dict            # {คำต้องห้าม: คำที่ถูก}
    approved: dict          # {ชื่อ/ศัพท์อังกฤษ: ชื่อไทย} จากตารางตัวละครและตารางศัพท์
    problems: list          # [(บรรทัด, ข้อความ)] — ตารางที่ parse ไม่ได้ / ข้อมูลขัดกัน
    text: str


def _cells(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def _is_sep(line):
    return re.fullmatch(r'\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?', line.strip()) is not None


def parse(path):
    text = open(path, encoding='utf-8').read() if os.path.exists(path) else ''
    lines = text.split('\n')
    tables, problems, section = [], [], ''
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('#'):
            section = ln.lstrip('#').strip()
        if ln.lstrip().startswith('|') and i + 1 < len(lines) and _is_sep(lines[i + 1]):
            t = Table(section, i + 1, _cells(ln))
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith('|'):
                cells = _cells(lines[i])
                if len(cells) != len(t.headers):
                    problems.append((i + 1, f'แถวมี {len(cells)} ช่อง แต่หัวตารางมี {len(t.headers)} ช่อง (ตรวจเครื่องหมาย | ในเนื้อหา)'))
                t.rows.append((i + 1, cells))
                i += 1
            tables.append(t)
            continue
        i += 1

    banned, approved = {}, {}
    for t in tables:
        if 'ห้ามใช้' in t.section:
            for no, cells in t.rows:
                m = re.fullmatch(r'❌\s*(.+)', cells[0]) if cells else None
                ok = re.fullmatch(r'✅\s*(.+)', cells[1]) if len(cells) > 1 else None
                if not (m and ok):
                    problems.append((no, 'แถวในตาราง "ห้ามใช้" ต้องเป็นรูปแบบ | ❌ คำผิด | ✅ คำถูก | เหตุผล | — แถวนี้ qa_check จะไม่เห็น'))
                    continue
                for bad in m.group(1).split('/'):
                    if bad.strip():
                        banned[bad.strip()] = ok.group(1).strip()
        elif t.headers and re.search(r'อังกฤษ|ต้นฉบับ|English', t.headers[0], re.I):
            for no, cells in t.rows:
                if len(cells) >= 2 and cells[0]:
                    if cells[0] in approved and approved[cells[0]] != cells[1]:
                        problems.append((no, f"'{cells[0]}' มีสองแถวที่แปลไม่ตรงกัน: '{approved[cells[0]]}' กับ '{cells[1]}'"))
                    approved.setdefault(cells[0], cells[1])

    for bad, good in banned.items():
        if bad == good:
            problems.append((0, f"คำต้องห้าม '{bad}' เหมือนคำที่ถูกทุกตัว"))
        for en, th in approved.items():
            # ห้ามคำต้องห้ามไปโผล่เป็นคำที่อนุมัติ (ยกเว้นเป็นส่วนหนึ่งของคำที่ถูกเอง เช่น ❌ รูบิค ไม่ชน ✅ รูบิก)
            if bad in th and good not in th:
                problems.append((0, f"คำต้องห้าม '{bad}' อยู่ในคำแปลที่อนุมัติของ '{en}' ({th})"))
    return Glossary(path, tables, banned, approved, problems, text)


def main():
    dirs = sys.argv[1:] or sorted(os.path.dirname(p) for p in __import__('glob').glob('novels/*/GLOSSARY.md'))
    bad = 0
    for d in dirs:
        g = parse(os.path.join(d, 'GLOSSARY.md'))
        print(f'{d}: ตาราง {len(g.tables)}, ศัพท์อนุมัติ {len(g.approved)}, คำต้องห้าม {len(g.banned)}, ปัญหา {len(g.problems)}')
        for no, msg in g.problems:
            print(f'  บรรทัด {no}: {msg}')
        bad += len(g.problems)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()

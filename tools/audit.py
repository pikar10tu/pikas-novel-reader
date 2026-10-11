"""ตัวเลขวัดคุณภาพบทแปลรายชุด (ใช้ประกอบการ audit — ไม่แก้ไฟล์ใดๆ ยกเว้น --log)
ใช้: python tools/audit.py dragon 181-200              ตารางรายตอน + สรุปชุด
     python tools/audit.py dragon 181-200 --sample 3   + สุ่ม 3 ตอน พิมพ์ต้นฉบับคู่คำแปลลงไฟล์ชั่วคราว
     python tools/audit.py dragon 181-200 --log        + บันทึกสรุปชุดต่อท้าย novels/<เรื่อง>/audit_log.csv
คอลัมน์:
  ย่อหน้า   ไทย/ต้นฉบับ (ไม่นับชื่อตอน) ไม่เท่ากัน = ตกหล่น/ซ้ำ/แต่งเพิ่ม
  ยาว      ความยาวไทย/อังกฤษ (ปกติ 0.85-1.05)
  ผิดสัดส่วน ย่อหน้าที่ยาวผิดสัดส่วนกับย่อหน้าต้นฉบับคู่กัน
  เธอ      'เธอ' ในบทบรรยาย, แข็ง = คำเชื่อมสำนวนแปลต่อหมื่นตัวอักษร
  แก้      ย่อหน้าที่ต่างจาก HEAD (ใช้ดูว่า "เกลา" จริงหรือแค่แตะไม่กี่บรรทัด)
"""
import csv, datetime, json, os, random, subprocess, sys, tempfile
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import qa_check as qa   # noqa: E402  (import แล้ว cwd = ราก repo)

STIFF = qa.STIFF + ['ค่อนข้าง', 'ตระหนัก', 'ถูกทำให้']


def chapter_path(book, n):
    return os.path.join(qa.book_dir(book), 'chapters', f'ch{n:03d}.json')


def head_paras(path):
    r = subprocess.run(['git', 'show', f'HEAD:{path.replace(os.sep, "/")}'], capture_output=True)
    return json.loads(r.stdout.decode('utf-8'))['paragraphs'] if r.returncode == 0 else None


def measure(book, n, gloss_lower):
    path = chapter_path(book, n)
    if not os.path.exists(path):
        return None
    paras = json.load(open(path, encoding='utf-8'))['paragraphs']
    rp = qa.raw_paras(book['id'], n) or []
    th, raw = qa.body_paras(paras, rp)
    text = ''.join(th)
    k = max(1, len(text)) / 10000
    old = head_paras(path)
    return {
        'n': n, 'th': len(th), 'raw': len(raw),
        'ratio': len(text) / max(1, len(''.join(raw))) if raw else 0,
        'odd': sum(1 for t, e in zip(th, raw) if len(e) > 50 and not 0.45 < len(t) / len(e) < 1.7),
        'dup': sum(c - 1 for p, c in Counter(th).items() if c > 1 and len(p) > 15),
        'teru': sum(qa.narration(p).count('เธอ') for p in th),
        'stiff': sum(text.count(w) for w in STIFF) / k,
        'changed': None if old is None else sum(1 for a, b in zip(paras, old) if a != b) + abs(len(paras) - len(old)),
        'names': qa.new_names(rp, gloss_lower) if rp and gloss_lower else [],
        'chars': len(text), 'th_paras': th, 'raw_paras': raw,
    }


def write_samples(rows, count):
    rng = random.Random(','.join(str(r['n']) for r in rows))
    picks = rng.sample(rows, min(count, len(rows)))
    out = os.path.join(tempfile.gettempdir(), f"audit_sample_{picks[0]['n']}.txt")
    with open(out, 'w', encoding='utf-8') as f:
        for r in sorted(picks, key=lambda r: r['n']):
            start = rng.randrange(max(1, len(r['raw_paras']) - 10))
            f.write(f"===== ตอน {r['n']} ย่อหน้า {start + 1}-{start + 10}\n")
            for i in range(start, min(start + 10, len(r['raw_paras']))):
                f.write(f"{i + 1} EN {r['raw_paras'][i]}\n")
                f.write(f"   TH {r['th_paras'][i] if i < len(r['th_paras']) else '-'}\n")
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) < 2:
        sys.exit(__doc__)
    book_id, (a, b) = args[0], qa.parse_range(args[1])
    sample = int(sys.argv[sys.argv.index('--sample') + 1]) if '--sample' in sys.argv else 0
    book = next(x for x in json.load(open('books.json', encoding='utf-8')) if x['id'] == book_id)
    gp = os.path.join(qa.book_dir(book), 'GLOSSARY.md')
    gloss_lower = open(gp, encoding='utf-8').read().lower() if os.path.exists(gp) else ''

    rows = [r for r in (measure(book, n, gloss_lower) for n in range(a, b + 1)) if r]
    print(f"{'ตอน':>4} {'ย่อหน้า':>9} {'ยาว':>5} {'ผิดสัดส่วน':>9} {'ซ้ำ':>3} {'เธอ':>3} {'แข็ง':>5} {'แก้':>4}  ชื่อใหม่")
    for r in rows:
        flag = '' if r['th'] == r['raw'] else ' <-'
        changed = '-' if r['changed'] is None else r['changed']
        print(f"{r['n']:>4} {r['th']:>4}/{r['raw']:<4} {r['ratio']:>5.2f} {r['odd']:>9} {r['dup']:>3} {r['teru']:>3} "
              f"{r['stiff']:>5.1f} {changed:>4}  {', '.join(r['names'][:5])}{flag}")
    if not rows:
        sys.exit('ไม่พบตอนในช่วงนี้')

    chars = sum(r['chars'] for r in rows)
    summary = {
        'date': datetime.date.today().isoformat(), 'range': f'{a}-{b}', 'chapters': len(rows),
        'ratio': round(sum(r['ratio'] for r in rows) / len(rows), 3),
        'misaligned': sum(r['th'] != r['raw'] for r in rows),
        'teru_per_10k': round(sum(r['teru'] for r in rows) / chars * 10000, 2),
        'stiff_per_10k': round(sum(r['stiff'] * r['chars'] for r in rows) / chars, 2),
        'odd_paras': sum(r['odd'] for r in rows),
    }
    print('\nสรุปชุด:', ', '.join(f'{k}={v}' for k, v in summary.items()))

    if sample:
        print('ตัวอย่างต้นฉบับคู่คำแปล:', write_samples(rows, sample))
    if '--log' in sys.argv:
        log = os.path.join(qa.book_dir(book), 'audit_log.csv')
        new = not os.path.exists(log)
        with open(log, 'a', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(summary))
            if new:
                w.writeheader()
            w.writerow(summary)
        print('บันทึกลง', log)


if __name__ == '__main__':
    main()

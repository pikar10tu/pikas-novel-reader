"""เทสต์ของ qa_check — รัน: python -m unittest tools.test_qa_check
(pre-commit hook รันให้อัตโนมัติเมื่อมีการแก้ไฟล์ใน tools/)"""
import os, re, tempfile, unittest

from tools import qa_check as qa


class SourceHygiene(unittest.TestCase):
    def test_no_control_chars_in_tools(self):
        # เคยเกิด: เขียน r'\b' ผ่าน heredoc แล้วกลายเป็นตัวอักษร backspace จริง regex เลยไม่ทำงานเงียบๆ
        tools = os.path.dirname(os.path.abspath(__file__))
        for f in os.listdir(tools):
            if f.endswith('.py'):
                with open(os.path.join(tools, f), encoding='utf-8') as fh:
                    src = fh.read()
                bad = re.findall(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', src)
                self.assertFalse(bad, f'{f} มีตัวอักษรควบคุม {bad[:3]}')


class Narration(unittest.TestCase):
    def test_strips_dialogue_and_thoughts(self):
        p = 'นางหันไปมอง "เธอทำอะไรน่ะ" แล้วคิดในใจ \'เธอนี่นะ\' ก่อนจะเดินออกไป'
        self.assertNotIn('เธอ', qa.narration(p))
        self.assertIn('นางหันไปมอง', qa.narration(p))

    def test_keeps_narration(self):
        self.assertIn('เธอ', qa.narration('รอสวิธาหยุดเดิน เธอขมวดคิ้ว'))

    def test_multi_paragraph_quote_counts_as_dialogue(self):
        # ย่อหน้าท้ายของคำพูดยาว: ไม่มีเครื่องหมายเปิด มีแต่ปิด
        self.assertEqual(qa.narration('พวกเธอไม่เกรงกลัวในความรัก"'), '')


class BodyParas(unittest.TestCase):
    def test_strips_both_titles(self):
        th, raw = qa.body_paras(['ตอนที่ 5: ชื่อ', 'ก', 'ข'], ['<strong>Chapter 5: Title</strong>', 'a', 'b'])
        self.assertEqual((th, raw), (['ก', 'ข'], ['a', 'b']))

    def test_chap_abbreviation(self):
        _, raw = qa.body_paras([], ['Chap 176 - Title', 'a'])
        self.assertEqual(raw, ['a'])

    def test_no_title(self):
        th, raw = qa.body_paras(['ก'], ['a'])
        self.assertEqual((th, raw), (['ก'], ['a']))


class FirstDrift(unittest.TestCase):
    def test_finds_shift(self):
        e = 'x' * 100
        th = ['ก' * 90, 'ก' * 95, 'ก' * 10, 'ก' * 90]   # ย่อหน้าที่ 3 สั้นผิดปกติ
        self.assertEqual(qa.first_drift(th, [e] * 4), 3)

    def test_aligned(self):
        self.assertIsNone(qa.first_drift(['ก' * 90] * 3, ['x' * 100] * 3))


class DupBlocks(unittest.TestCase):
    def test_detects_leftover_block(self):
        P = [f'ย่อหน้าที่ {i} เนื้อหายาวพอสมควรเพื่อให้เกินสามสิบตัวอักษรแน่นอน {chr(0x0E01 + i) * 5}' for i in range(6)]
        self.assertIn(6, qa.dup_blocks(P + P[:4]))

    def test_clean_chapter(self):
        P = [f'{chr(0x0E01 + i) * 40}' for i in range(10)]
        self.assertEqual(qa.dup_blocks(P), {})


class NewNames(unittest.TestCase):
    RAW = ['Chapter 1: Title Words',
           'Leon met Rebecca at the gate, and Rebecca smiled.',
           'Later, Rebecca waved. Then Leon cast Magic, real magic this time.',
           'Your Majesty, Dad said the Sanctuary is safe, and Dad was right.']

    def test_reports_unknown_name(self):
        self.assertEqual(qa.new_names(self.RAW, 'leon'), ['Rebecca'])

    def test_known_in_glossary(self):
        self.assertEqual(qa.new_names(self.RAW, 'leon rebecca'), [])

    def test_ignores_common_nouns_and_title(self):
        names = qa.new_names(self.RAW, '')
        for w in ('Magic', 'Dad', 'Majesty', 'Sanctuary', 'Title', 'Words'):
            self.assertNotIn(w, names)


class LoadBanned(unittest.TestCase):
    def test_parses_table_with_variants(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, 'GLOSSARY.md'), 'w', encoding='utf-8') as f:
                f.write('## ห้ามใช้\n| ห้ามใช้ | ใช้แทน | เหตุผล |\n|---|---|---|\n'
                        '| ❌ เจ้าชาย | ✅ องค์ชาย | x |\n| ❌ มูเอน / มูอึน | ✅ มูน | y |\n')
            self.assertEqual(qa.load_banned(d), {'เจ้าชาย': 'องค์ชาย', 'มูเอน': 'มูน', 'มูอึน': 'มูน'})

    def test_real_glossary_loads(self):
        banned = qa.load_banned(os.path.join(qa.ROOT, 'novels', 'dragon'))
        self.assertEqual(banned.get('เจ้าชาย'), 'องค์ชาย')
        self.assertEqual(banned.get('เมลค์วี'), 'เมลควิ')


if __name__ == '__main__':
    unittest.main()

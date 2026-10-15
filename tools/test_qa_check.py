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


class GlossaryParse(unittest.TestCase):
    def parse(self, md):
        from tools import glossary
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'GLOSSARY.md')
            with open(p, 'w', encoding='utf-8') as f:
                f.write(md)
            return glossary.parse(p)

    CHARS = ('## 2. ตัวละคร\n| ชื่ออังกฤษ | ชื่อไทย | หมายเหตุ |\n|---|---|---|\n'
             '| Leon | ลีออน | พระเอก |\n| Prince | องค์ชาย | ฐานันดร |\n')
    BANNED = '## ห้ามใช้\n| ห้ามใช้ | ใช้แทน | เหตุผล |\n|---|---|---|\n'

    def test_approved_terms(self):
        g = self.parse(self.CHARS)
        self.assertEqual(g.approved, {'Leon': 'ลีออน', 'Prince': 'องค์ชาย'})
        self.assertEqual(g.problems, [])

    def test_malformed_banned_row_is_reported(self):
        # ลืม ✅ = แถวนี้เคยถูกข้ามเงียบๆ
        g = self.parse(self.BANNED + '| ❌ เจ้าชาย | องค์ชาย | x |\n')
        self.assertEqual(g.banned, {})
        self.assertEqual(len(g.problems), 1)

    def test_wrong_column_count(self):
        g = self.parse(self.CHARS + '| Anna | แอนนา | เมด | เกิน |\n')
        self.assertTrue(any('ช่อง' in m for _, m in g.problems))

    def test_banned_word_inside_approved_term(self):
        g = self.parse(self.CHARS.replace('องค์ชาย', 'เจ้าชาย') + self.BANNED + '| ❌ เจ้าชาย | ✅ องค์ชาย | x |\n')
        self.assertTrue(any('เจ้าชาย' in m for _, m in g.problems))

    def test_conflicting_duplicate(self):
        g = self.parse(self.CHARS + '| Leon | เลออน | ซ้ำ |\n')
        self.assertTrue(any('ไม่ตรงกัน' in m for _, m in g.problems))

    def test_real_glossaries_are_clean(self):
        from tools import glossary
        import glob
        for p in glob.glob(os.path.join(qa.ROOT, 'novels', '*', 'GLOSSARY.md')):
            self.assertEqual(glossary.parse(p).problems, [], p)


if __name__ == '__main__':
    unittest.main()


class ModernPronouns(unittest.TestCase):
    def test_flags_chan_nai_dialogue(self):
        # Ch 238 ก่อนแก้: ลีออน/รอสวิธาคุยกันด้วย ฉัน/นาย
        P = ['"ฉันจะไปกับนายเอง" นางเอ่ย'] * 5
        self.assertGreater(qa.modern_density(P), qa.MODERN_MAX)

    def test_ignores_narration_and_compounds(self):
        P = ['ฉันในบทบรรยายไม่นับ "ข้าจะไปหาเจ้านายกับท่านนายพล" ลีออนว่า'] * 5
        self.assertEqual(qa.modern_density(P), 0)


class Header(unittest.TestCase):
    def test_source_chapter_number(self):
        ch = {'paragraphs': ['ตอนที่ 43: ชื่อ'], 'title': 'ตอนที่ 238: ชื่อ', 'vol': 2}
        self.assertEqual(len(qa.header_issues(ch, 238, [(1, 1), (196, 2)])), 1)

    def test_wrong_vol(self):
        ch = {'paragraphs': ['ตอนที่ 238: ชื่อ'], 'title': 'ตอนที่ 238: ชื่อ', 'vol': 1}
        self.assertEqual(len(qa.header_issues(ch, 238, [(1, 1), (196, 2)])), 1)

    def test_ok_and_untitled(self):
        ok = {'paragraphs': ['ตอนที่ 238: ชื่อ'], 'title': 'ตอนที่ 238: ชื่อ', 'vol': 2}
        early = {'paragraphs': ['ภายในคุกใต้ดิน'], 'title': 'ตอนที่ 1: ชื่อ', 'vol': 1}
        self.assertEqual(qa.header_issues(ok, 238, [(1, 1), (196, 2)]), [])
        self.assertEqual(qa.header_issues(early, 1, [(1, 1), (196, 2)]), [])

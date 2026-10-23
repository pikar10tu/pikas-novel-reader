"""เทสต์ของ qa_check — รัน: python -m unittest tools.test_qa_check
(pre-commit hook รันให้อัตโนมัติเมื่อมีการแก้ไฟล์ใน tools/)"""
import glob, json, os, re, tempfile, unittest

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

    def test_bare_title_without_chapter_word(self):
        th, raw = qa.body_paras(['ตอนที่ 1: ความริษยา', 'ข่าวด่วน!'], ['The Greatest Envy', 'Breaking news!'])
        self.assertEqual((th, raw), (['ข่าวด่วน!'], ['Breaking news!']))

    def test_short_first_line_kept_when_thai_has_no_title(self):
        th, raw = qa.body_paras(['ข่าวด่วน!'], ['Breaking news!'])
        self.assertEqual(raw, ['Breaking news!'])

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


class NovelConfig(unittest.TestCase):
    def test_defaults_when_no_file(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = qa.load_cfg(d)
        self.assertFalse(cfg['no_teru_narration'])
        self.assertEqual(cfg['strict_from'], 1)

    def test_file_overrides_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, 'novel.json'), 'w', encoding='utf-8') as f:
                f.write('{"source_lang": "zh", "no_archaic": true}')
            cfg = qa.load_cfg(d)
        self.assertEqual((cfg['source_lang'], cfg['no_archaic'], cfg['vols']), ('zh', True, []))

    def test_every_novel_config_has_known_keys(self):
        for p in glob.glob(os.path.join(qa.ROOT, 'novels', '*', 'novel.json')):
            with open(p, encoding='utf-8') as f:
                unknown = set(json.load(f)) - set(qa.CFG_DEFAULTS)
            self.assertFalse(unknown, f'{p}: คีย์ที่ไม่รู้จัก {unknown}')

    def test_raw_paras_formats_chapter_number(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, 'ch007.json'), 'w', encoding='utf-8') as f:
                f.write('{"paragraphs": ["a", "b"]}')
            self.assertEqual(qa.raw_paras({'raw': os.path.join(d, 'ch{n:03d}.json')}, 7), ['a', 'b'])
            self.assertIsNone(qa.raw_paras({'raw': os.path.join(d, 'ch{n:03d}.json')}, 8))


class ChineseTitle(unittest.TestCase):
    def test_strips_chinese_heading(self):
        _, raw = qa.body_paras([], ['第1章 黃山真君和9洲1號群', '正文'])
        self.assertEqual(raw, ['正文'])


class CleanRaw(unittest.TestCase):
    def test_drops_site_boilerplate_and_entities(self):
        from tools import clean_raw
        kept, dropped, _ = clean_raw.clean(['I&nbsp;envied him.', '&larr; Back to Novel Translation Hub',
                                         'Username or Email Address', '', '<p>Next.</p>'])
        self.assertEqual(kept, ['I envied him.', 'Next.'])
        self.assertEqual(len(dropped), 3)

    def test_keeps_emphasis_tags(self):
        from tools import clean_raw
        self.assertEqual(clean_raw.clean(['<em>Damn it.</em>'])[0], ['<em>Damn it.</em>'])

    def test_rejoins_dotted_words(self):
        from tools import clean_raw
        self.assertEqual(clean_raw.clean_para('the s.p.a.ce around a n.o.ble man, e.g. here, U.S.A, 5 p.m.'),
                         'the space around a noble man, e.g. here, U.S.A, 5 p.m.')
        self.assertEqual(clean_raw.clean_para('a ma.s.sage, her but.tocks, relations.h.i.p'), 'a massage, her buttocks, relationship')

    def test_moves_footnotes_to_notes(self):
        from tools import clean_raw
        kept, _, notes = clean_raw.clean(['Story.', '[1] 역대급 means all-time greatest', '<strong>Footnotes:</strong>', 'Mana is magic.'])
        self.assertEqual(kept, ['Story.'])
        self.assertEqual(notes, ['[1] 역대급 means all-time greatest', 'Mana is magic.'])

    def test_translator_chatter_goes_to_notes(self):
        from tools import clean_raw
        kept, _, notes = clean_raw.clean(['Story.', '(TL: goosebumps)', '[TN: Auror confusion]', '[T/N]', 'Pyung note'])
        self.assertEqual(kept, ['Story.'])
        self.assertEqual(len(notes), 3)

    def test_note_head_takes_rest_of_chapter(self):
        from tools import clean_raw
        kept, _, notes = clean_raw.clean(['End.', '(Note:', 'Hey there guys, new translator from now on.'])
        self.assertEqual((kept, len(notes)), (['End.'], 1))

    def test_keeps_story_lines_starting_with_back_to(self):
        from tools import clean_raw
        line = 'Back to my Hell. My 125 square-foot, single room apartment.'
        self.assertEqual(clean_raw.clean([line, 'Back to the time the Flame Emperor could still die!'])[1], [])

import copy
import unittest
from evobridge import model


class Commands(unittest.TestCase):
    def setUp(self):
        self.p = model.new_project()

    def test_missing_brief_fields_are_asked_sequentially(self):
        for text in ['创建项目', '街角咖啡馆', '邻居', '12', '温暖']:
            model.command(self.p, text)
        self.assertEqual(self.p['theme'], '街角咖啡馆')
        self.assertEqual(self.p['audience'], '邻居')
        self.assertEqual(sum(s['seconds'] for s in self.p['scenes']), 12)
        self.assertFalse(self.p['wizard'])

    def test_english_brief_then_two_edits_undo(self):
        for text in ['Create a project', 'My community garden', 'neighbors', '9 seconds', 'calm']:
            model.command(self.p, text)
        old = copy.deepcopy(self.p['scenes'])
        model.command(self.p, 'Shorten scene 2')
        model.command(self.p, 'Tone warm')
        self.assertEqual(self.p['duration'], 8)
        self.assertEqual(self.p['tone'], 'warm')
        model.command(self.p, 'Undo')
        self.assertEqual(self.p['tone'], 'calm')
        model.command(self.p, 'Undo')
        self.assertEqual(self.p['scenes'], old)

    def test_unicode_text_and_order(self):
        model.build(self.p, '阳台菜园 🌱', '家人', 12, 'warm')
        model.command(self.p, '文本2：春天你好 Café 🎬')
        self.assertEqual(self.p['scenes'][1]['caption'], '春天你好 Café 🎬')
        second = self.p['scenes'][1]['id']
        model.command(self.p, '移动2到1')
        self.assertEqual(self.p['scenes'][0]['id'], second)
        model.command(self.p, 'Title 1: Welcome home')
        self.assertEqual(self.p['scenes'][0]['title'], 'Welcome home')

    def test_unsupported_and_invalid_preserve_storyboard(self):
        model.build(self.p, 'A café', 'neighbors', 12, 'warm')
        for text in ['', ' ', 'x' * 2001, 'make a hollywood movie', '第999段设为3秒', '第2段设为99秒']:
            before = copy.deepcopy(self.p)
            with self.subTest(text=text[:20]), self.assertRaises(ValueError):
                model.command(self.p, text)
            self.assertEqual(before, self.p)

    def test_invalid_brief(self):
        for duration in [0, -1, 5, 46, 7.2, True, 'twelve', '12.0']:
            before = copy.deepcopy(self.p)
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                model.build(self.p, 'Garden', 'neighbors', duration, 'warm')
            self.assertEqual(self.p, before)

    def test_cancel_wizard_preserves_previous_scenes(self):
        model.build(self.p, 'Garden', 'neighbors', 12, 'warm')
        old = copy.deepcopy(self.p['scenes'])
        model.command(self.p, 'Create a project')
        model.command(self.p, 'Different project')
        model.command(self.p, 'Cancel')
        self.assertEqual(old, self.p['scenes'])
        self.assertFalse(self.p['wizard'])

    def test_export_only_requests_confirmation(self):
        model.build(self.p, 'Garden', 'neighbors', 6, 'calm')
        _, action = model.command(self.p, 'Export')
        self.assertEqual(action, 'confirm')
        self.assertEqual(self.p['status'], 'storyboard')

    def test_bad_patch_is_atomic(self):
        model.build(self.p, 'Garden', 'neighbors', 12, 'warm')
        for patch in [{'scene': 0, 'title': 'Good', 'seconds': 0}, {'scene': 0, 'asset': '../../secret'}, {'move': [0,99]}, {'format': 'bad'}, {'scene': 0, 'color': 'red;url(http://evil)'}]:
            before = copy.deepcopy(self.p)
            with self.assertRaises(ValueError):
                model.edit(self.p, patch)
            self.assertEqual(before, self.p)

    def test_new_project_is_isolated(self):
        model.build(self.p, 'Old', 'friends', 9, 'bold')
        new = model.new_project()
        self.assertNotEqual(self.p['id'], new['id'])
        self.assertEqual(new['scenes'], [])
        self.assertEqual(new['history'], [])

    def test_history_is_bounded(self):
        model.build(self.p, 'Garden', 'neighbors', 12, 'warm')
        for i in range(25):
            model.command(self.p, f'Title 1: Scene {i}')
        self.assertEqual(len(self.p['history']), 20)


if __name__ == '__main__':
    unittest.main()

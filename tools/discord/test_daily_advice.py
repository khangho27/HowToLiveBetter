import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import daily_advice as app


class DigestTests(unittest.TestCase):
    def setUp(self):
        self.entries = [{'id': f'3:{i}', 'title': '标题', 'text': 'source',
                         'evidence': 'B', 'path': 'book/03-不要浪费精力.md',
                         'line': i * 10} for i in range(1, 11)]

    def test_recent_entries_are_excluded(self):
        history = {'3:1': '2026-11-09', '3:2': '2026-11-10'}
        picked = app.select_entries(self.entries, history, '2026-11-11')
        self.assertEqual(len(picked), 3)
        self.assertTrue(all(e['id'] not in history for e in picked))
        self.assertEqual(picked, app.select_entries(self.entries, history, '2026-11-11'))

    def test_exhausted_pool_prefers_oldest(self):
        history = {e['id']: f'2026-11-{i:02d}' for i, e in enumerate(self.entries, 1)}
        picked = app.select_entries(self.entries, history, '2026-11-11')
        self.assertEqual([e['id'] for e in picked], ['3:1', '3:2', '3:3'])

    def test_parse_and_filter_real_structure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'book').mkdir()
            text = '# 3. Test\n'
            for i in range(1, 6):
                title = '关掉通知' if i < 5 else '社保规定'
                text += f'\n### {i}. {title}\n- 说人话：内容\n- 证据等级：B\n- 来源：https://doi.org/example\n- 备注：限制条件\n'
            (root / 'book/03-test.md').write_text(text)
            parsed = app.parse_book(root)
            self.assertEqual(len(parsed), 4)
            self.assertEqual(parsed[0]['line'], 3)
            self.assertIn('限制条件', parsed[0]['text'])

    def test_invalid_translation_is_rejected(self):
        entries = self.entries[:3]
        valid = [{'id': e['id'], 'title': 'Turn off notifications',
                  'summary': 'Put your phone away while concentrating. The evidence comes from short laboratory tasks.'} for e in entries]
        self.assertEqual(app.validate_summaries(valid, entries), valid)
        bad = json.loads(json.dumps(valid))
        bad[0]['summary'] = 'x' * 361
        with self.assertRaises(ValueError):
            app.validate_summaries(bad, entries)
        bad[0]['summary'] = '中文'
        with self.assertRaises(ValueError):
            app.validate_summaries(bad, entries)
        bad[0]['id'] = 'wrong'
        with self.assertRaises(ValueError):
            app.validate_summaries(bad, entries)

    def test_payload_has_exact_sources_and_no_pings(self):
        entries = self.entries[:3]
        summaries = [{'title': 'Tip', 'summary': 'A short summary with its caveat.'} for e in entries]
        payload = app.make_payload(entries, summaries, '2026-11-11', 'owner/repo', 'abc123')
        self.assertEqual(payload['allowed_mentions'], {'parse': []})
        fields = payload['embeds'][0]['fields']
        self.assertEqual(len(fields), 4)
        self.assertIn('/blob/abc123/book/', fields[0]['value'])
        self.assertIn('#L10', fields[0]['value'])
        self.assertIn('CC BY 4.0', fields[-1]['value'])

    def test_failed_delivery_does_not_advance_history(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'history.json'
            with patch.object(app, 'STATE', state), patch.object(app, 'parse_book', return_value=self.entries), patch.object(app, 'translate', return_value=[{'title': 'Tip', 'summary': 'Text'}] * 3), patch.object(app, 'post_json', side_effect=RuntimeError('Delivery failed')), patch.dict(app.os.environ, {'ANTHROPIC_API_KEY': 'test', 'DISCORD_WEBHOOK_URL': 'https://discord.com/api/webhooks/123/token'}), patch('sys.argv', ['daily_advice.py']):
                with self.assertRaises(RuntimeError):
                    app.main()
                self.assertFalse(state.exists())

    def test_same_day_send_skips_network(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'history.json'
            today = app.datetime.now(app.ZoneInfo('America/Los_Angeles')).date().isoformat()
            state.write_text(json.dumps({'last_sent': today, 'history': {}}))
            with patch.object(app, 'STATE', state), patch.object(app, 'post_json') as request, patch('sys.argv', ['daily_advice.py']):
                app.main()
                request.assert_not_called()


if __name__ == '__main__':
    unittest.main()

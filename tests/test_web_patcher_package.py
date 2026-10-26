"""Static package checks for the Drayano/smoldice-based Sacred Gold browser installer."""
import base64
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from package_sacred_gold_web import build_site, js_string, render_html, worker_source
from export_sacred_gold_patcher_repo import export


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.blocks = {'script': [], 'style': []}
        self.current = None
        self.policy = ''
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag in self.blocks:
            self.current = tag
            self.blocks[tag].append('')
        if tag == 'meta' and attrs.get('http-equiv') == 'Content-Security-Policy':
            self.policy = attrs['content']

    def handle_endtag(self, tag):
        if tag == self.current:
            self.current = None

    def handle_data(self, text):
        if self.current:
            self.blocks[self.current][-1] += text


class WebPackage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = render_html(dict(format=1, version='synthetic', profiles={}))
        cls.page = Page(cls.html)

    def test_csp_matches_the_actual_inline_code_and_css(self):
        for kind in ('script', 'style'):
            self.assertEqual(len(self.page.blocks[kind]), 1)
            digest = base64.b64encode(hashlib.sha256(self.page.blocks[kind][0].encode()).digest()).decode()
            self.assertIn(f"{kind}-src 'sha256-{digest}'", self.page.policy)

    def test_network_connections_and_form_submissions_are_forbidden(self):
        for policy in ("connect-src 'none'", "form-action 'none'", "object-src 'none'", "base-uri 'none'"):
            self.assertIn(policy, self.page.policy)
        self.assertNotIn('unsafe-eval', self.page.policy)
        self.assertNotIn('unsafe-inline', self.page.policy)
        self.assertFalse(any(tag == 'script' and 'src' in attrs for tag, attrs in self.page.tags))
        self.assertFalse(any(tag == 'form' for tag, _ in self.page.tags))

    def test_dynamic_data_cannot_close_the_script_tag(self):
        hostile = '</script><script>alert(1)</script>'
        self.assertNotIn('<', js_string(hostile))
        page = Page(render_html(dict(format=1, version=hostile, profiles={})))
        self.assertEqual(len(page.blocks['script']), 1)

    def test_creator_credits_and_local_media_are_present(self):
        self.assertIn('Drayano', self.html)
        self.assertIn('smoldice', self.html)
        self.assertIn('marcrobledo/RomPatcher.js', self.html)
        videos = [attrs for tag, attrs in self.page.tags if tag == 'video']
        self.assertEqual(len(videos), 1)
        self.assertNotIn('autoplay', videos[0])
        self.assertEqual(videos[0]['preload'], 'none')
        for tag, attrs in self.page.tags:
            if tag == 'source' and attrs.get('type') == 'video/mp4':
                self.assertTrue(attrs['src'].startswith('media/'))

    def test_animated_sprites_have_static_alternatives_and_a_pause_control(self):
        sprites = [attrs for tag, attrs in self.page.tags if tag == 'img' and 'data-animated' in attrs]
        self.assertEqual({sprite['alt'] for sprite in sprites}, {'Ho-Oh', 'Lugia'})
        for sprite in sprites:
            self.assertEqual(sprite['src'], sprite['data-still'])
            for field in ('src', 'data-still', 'data-animated'):
                self.assertTrue(sprite[field].startswith('media/'))
        self.assertTrue(any(tag == 'button' and attrs.get('id') == 'sprite-motion' for tag, attrs in self.page.tags))

    def test_page_and_worker_contain_no_private_workspace_paths(self):
        for text in (self.html, worker_source()):
            for value in ('/Users/', 'Desktop/Screen Recording', 'file:///'):
                self.assertNotIn(value, text)

    def test_bad_release_patches_do_not_create_a_site(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            wrong = root / 'wrong.xdelta'
            wrong.write_bytes(b'not a release patch')
            out = root / 'site'
            with self.assertRaisesRegex(ValueError, 'release delta'):
                build_site(out, wrong, wrong)
            self.assertFalse(out.exists())
            self.assertFalse(out.with_suffix('.zip').exists())

    def test_existing_site_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'site'
            out.mkdir()
            valuable = out / 'index.html'
            valuable.write_text('existing site')
            with self.assertRaises(FileExistsError):
                build_site(out, Path('missing'), Path('missing'))
            self.assertEqual(valuable.read_text(), 'existing site')

    def test_vendored_originals_match_their_pins(self):
        pins = json.loads((ROOT / 'patcher/web/vendor/provenance.json').read_text())
        for name, info in pins.items():
            self.assertEqual(hashlib.sha256((ROOT / 'patcher/web/vendor' / name).read_bytes()).hexdigest(), info['sha256'])

    def test_source_export_contains_build_templates_without_private_game_files(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'source'
            export(out)
            names = {p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()}
            for name in ('patcher/repository/pages.yml', 'patcher/repository/tests.yml',
                         '.github/workflows/pages.yml', 'patcher/web/media/hooh-gen5.gif'):
                self.assertIn(name, names)
            for name in names:
                self.assertFalse(Path(name).suffix.lower() in {'.nds', '.sav', '.dsv', '.dst', '.bundle', '.xdelta', '.mov', '.pyc'})
                self.assertFalse(set(Path(name).parts) & {'games', 'inputs', 'local', '.git', '__pycache__'})
            with zipfile.ZipFile(out.with_suffix('.zip')) as archive:
                self.assertEqual({name.removeprefix('source/') for name in archive.namelist()}, names)
            with self.assertRaises(FileExistsError):
                export(out)


if __name__ == '__main__':
    unittest.main()

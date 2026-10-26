"""Exercise the installer with tiny real xdelta patches, without touching game saves."""
import errno
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'patcher'))
import sacred_gold_patcher as installer

XDELTA = shutil.which('xdelta3') or str(ROOT / 'local/tools/xdelta-build/xdelta3')


@unittest.skipUnless(Path(XDELTA).is_file(), 'xdelta3 is required for codec integration tests')
class Installer(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sg, self.donor = self.root / 'sg.nds', self.root / 'donor.nds'
        self.sg.write_bytes(bytes(range(256)) * 4)
        self.donor.write_bytes(bytes(reversed(range(256))) * 8)
        target = self.root / 'target.nds'
        self.expected = self.sg.read_bytes() + b'our changes' + self.donor.read_bytes()[40:1000]
        target.write_bytes(self.expected)
        source = self.root / 'combined.bin'
        installer.concatenate([self.sg, self.donor], source)
        delta = self.root / 'release.xdelta'
        installer.run_tool([XDELTA, '-e', '-D', '-A', '-S', 'none', '-s', source, target, delta])
        self.release = dict(format=1, version='test', source_order=['sacred_gold', 'reforged'],
            inputs=dict(sacred_gold=installer.fingerprint(self.sg), reforged=installer.fingerprint(self.donor)),
            patch=installer.fingerprint(delta), patch_name=delta.name, output=installer.fingerprint(target))
        self.manifest = self.root / 'release.json'
        self.save_manifest()
        self.out = self.root / 'new-game.nds'
        self.options = dict(release=self.manifest, sacred_gold=self.sg, reforged=self.donor,
                            xdelta3=XDELTA, out=self.out)

    def save_manifest(self):
        self.manifest.write_text(json.dumps(self.release), encoding='utf-8')

    def check_no_output(self):
        self.assertFalse(self.out.exists())
        self.assertEqual(list(self.root.glob('.sacred-gold-build-*')), [])

    def test_real_patch_roundtrip_preserves_inputs(self):
        before = [installer.fingerprint(p) for p in (self.sg, self.donor)]
        result = installer.build(self.options, lambda _: None)
        self.assertEqual(self.out.read_bytes(), self.expected)
        self.assertEqual(result, self.release['output'])
        self.assertEqual(before, [installer.fingerprint(p) for p in (self.sg, self.donor)])
        self.assertEqual(list(self.root.glob('.sacred-gold-build-*')), [])

    def test_existing_output_preserved(self):
        self.out.write_bytes(b'valuable existing ROM')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            installer.build(self.options, lambda _: None)
        self.assertEqual(self.out.read_bytes(), b'valuable existing ROM')

    def test_save_output_refused(self):
        with self.assertRaisesRegex(ValueError, '.nds output'):
            installer.build(dict(self.options, out=self.root / 'my-save.sav'), lambda _: None)
        self.assertFalse((self.root / 'my-save.sav').exists())

    def test_broken_symlink_not_replaced(self):
        self.out.symlink_to(self.root / 'missing.nds')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            installer.build(self.options, lambda _: None)
        self.assertTrue(self.out.is_symlink())

    def test_same_size_wrong_source_rejected_before_decode(self):
        self.sg.write_bytes(b'x' * self.sg.stat().st_size)
        with patch.object(installer, 'decode') as decode:
            with self.assertRaisesRegex(ValueError, 'unsupported or damaged'):
                installer.build(self.options, lambda _: None)
            decode.assert_not_called()
        self.check_no_output()

    def test_tampered_patch_rejected(self):
        (self.root / 'release.xdelta').write_bytes(b'damaged patch')
        with self.assertRaisesRegex(ValueError, 'Release patch'):
            installer.build(self.options, lambda _: None)
        self.check_no_output()

    def test_output_hash_failure_cleans_up(self):
        self.release['output']['sha256'] = '0' * 64
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'Finished ROM'):
            installer.build(self.options, lambda _: None)
        self.check_no_output()

    def test_bad_codec_payload_cleans_up(self):
        delta = self.root / 'release.xdelta'
        delta.write_bytes(b'not VCDIFF')
        self.release['patch'] = installer.fingerprint(delta)
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'failed'):
            installer.build(self.options, lambda _: None)
        self.check_no_output()

    def test_source_order_cannot_be_reversed(self):
        self.release['source_order'].reverse()
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'source order'):
            installer.build(self.options, lambda _: None)
        self.check_no_output()

    def test_mixed_modes_refused(self):
        with self.assertRaisesRegex(ValueError, 'Do not mix modes'):
            installer.build(dict(self.options, heartgold=self.sg), lambda _: None)
        self.check_no_output()

    def test_manifest_cannot_escape_patch_folder(self):
        self.release['patch_name'] = '../release.xdelta'
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'filename'):
            installer.load_release(self.manifest)

    def test_environment_cannot_disable_xdelta_checksums(self):
        original = installer.subprocess.run
        with patch.dict(os.environ, {'XDELTA': '-n -f'}):
            with patch.object(installer.subprocess, 'run', wraps=original) as run:
                installer.build(self.options, lambda _: None)
                self.assertNotIn('XDELTA', run.call_args.kwargs['env'])

    def test_final_publish_does_not_replace_file_created_during_build(self):
        self.out.write_bytes(b'created by another program')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            installer.publish(self.sg, self.out)
        self.assertEqual(self.out.read_bytes(), b'created by another program')

    def test_exfat_fallback_and_failure_cleanup(self):
        with patch.object(installer.os, 'link', side_effect=OSError(errno.ENOSYS, 'no hard links')):
            installer.publish(self.sg, self.out)
        self.assertEqual(self.out.read_bytes(), self.sg.read_bytes())
        self.out.unlink()
        with patch.object(installer.os, 'link', side_effect=OSError(errno.ENOSYS, 'no hard links')):
            with patch.object(installer.shutil, 'copyfileobj', side_effect=OSError('disk full')):
                with self.assertRaisesRegex(OSError, 'disk full'):
                    installer.publish(self.sg, self.out)
        self.check_no_output()

    def test_fallback_close_failure_removes_partial_file(self):
        original_open = Path.open

        class FailOnClose:
            def __init__(self, stream):
                self.stream = stream

            def __enter__(self):
                return self.stream

            def __exit__(self, *args):
                self.stream.close()
                raise OSError('close failed: disk full')

        def open_file(path, *args, **kwargs):
            stream = original_open(path, *args, **kwargs)
            return FailOnClose(stream) if path == self.out else stream

        with patch.object(installer.os, 'link', side_effect=OSError(errno.ENOSYS, 'no hard links')):
            with patch.object(Path, 'open', open_file):
                with self.assertRaisesRegex(OSError, 'close failed'):
                    installer.publish(self.sg, self.out)
        self.check_no_output()

    def test_incomplete_cli_inputs_do_not_open_gui(self):
        with patch.object(installer, 'gui') as gui:
            with self.assertRaises(SystemExit):
                installer.main(['--platinum', str(self.sg)])
            gui.assert_not_called()


class AnvilSource(unittest.TestCase):
    def test_changed_or_extra_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            code = root / 'anvil/reforged_anvil/__init__.py'
            code.parent.mkdir(parents=True)
            code.write_text('# pinned\n')
            name = code.relative_to(root).as_posix()
            release = dict(anvil_files={name: installer.fingerprint(code)['sha256']})
            self.assertEqual(installer.validate_anvil(root, release), root.resolve())
            code.write_text('# modified\n')
            with self.assertRaisesRegex(ValueError, 'differs'):
                installer.validate_anvil(root, release)
            code.write_text('# pinned\n')
            code.with_name('extra.py').write_text('# unexpected import\n')
            with self.assertRaisesRegex(ValueError, 'do not match'):
                installer.validate_anvil(root, release)


if __name__ == '__main__':
    unittest.main()

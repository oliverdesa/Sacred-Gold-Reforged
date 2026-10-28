"""Create a local Sacred Gold installer package; never include ROMs, saves or upstream bundles."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'patcher'))
from sacred_gold_patcher import concatenate, find_xdelta, fingerprint, run_tool, verify

VERSION = 'alpha5a'
ANVIL_COMMIT = '89e6cfe11420dd8823d0ecfb7885f3a528ad18f1'
INPUTS = {
    'heartgold': dict(size=134217728, sha256='65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105'),
    'platinum': dict(size=134217728, sha256='ede62292aa7f7014ff27d42097e769753380531739889c29b968b67b80f80678'),
    'black2': dict(size=536870912, sha256='2e6b2415354aa41471bc7617068dce059a59931bf5c4348a264f8043f297683a'),
    'sacred_gold_patch': dict(size=15023442, sha256='266bcb49b9a9795c38c06fa462eca7852bfc96be1e6575cefa83003545d3f5b5'),
    'bundle': dict(size=630876, sha256='c4b271c5e20a17ff5ce5ff252686fddf099939fbddac999cf07fd0ad2b159313'),
    'sacred_gold': dict(size=131037664, sha256='49f29848878406990ea288f26872d4355c92c4a2677f56973750bbf2566c13c1'),
    'reforged': dict(size=268435456, sha256='17afd998421183ab1421c0419bf9a6d545c034dc6c9ee3fa62779d8aa342ca77'),
}
OUTPUT = dict(size=268435456, sha256='7401754e880b386c73c7eb354a08fd717b9b9f7745994b6f367b726262346cdc')


def anvil_hashes(root):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()
    if git('rev-parse', 'HEAD') != ANVIL_COMMIT or git('status', '--porcelain'):
        raise ValueError('Anvil must be the clean pinned checkout.')
    files = sorted([*(root / 'anvil/reforged_anvil').glob('*.py'), *(root / 'tools/port').glob('*.py'),
                    root / 'game/tools/msgenc/charmap.txt'])
    return {path.relative_to(root).as_posix(): fingerprint(path)['sha256'] for path in files}


def package(args):
    out = args.out.resolve()
    archive = out.with_suffix('.zip')
    if out.exists() or archive.exists():
        raise FileExistsError('Package output already exists; choose a new directory.')
    xdelta = find_xdelta(args.xdelta3)
    verify(args.sacred_gold, INPUTS['sacred_gold'], 'Sacred Gold Complete 1.05')
    verify(args.reforged, INPUTS['reforged'], 'Pinned Reforged donor')
    verify(args.target, OUTPUT, f'Released Sacred Gold {VERSION}')
    hashes = anvil_hashes(args.anvil_source)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.sg-package-', dir=out.parent) as folder:
        temp = Path(folder)
        composite = temp / 'source.bin'
        concatenate([args.sacred_gold, args.reforged], composite)
        payload = temp / out.name
        payload.mkdir()
        patch_name = f'SacredGold-Reforged-{VERSION}.xdelta'
        print('Encoding against both local donor ROMs...', flush=True)
        # One source window covers the complete dictionary, so matches can cross donor order.
        # No application header (which would record local filenames) or secondary codec dependency.
        run_tool([xdelta, '-e', '-9', '-D', '-A', '-S', 'none', '-B', str(512 * 1024 ** 2),
                  '-s', composite, args.target, payload / patch_name])
        release = dict(format=1, version=VERSION, source_order=['sacred_gold', 'reforged'],
                       inputs=INPUTS, output=OUTPUT, patch_name=patch_name,
                       patch=fingerprint(payload / patch_name), anvil_commit=ANVIL_COMMIT,
                       anvil_files=hashes)
        (payload / 'release.json').write_text(json.dumps(release, indent=2) + '\n', encoding='utf-8')
        shutil.copyfile(ROOT / 'patcher/sacred_gold_patcher.py', payload / 'sacred_gold_patcher.py')
        shutil.copyfile(ROOT / 'patcher/README.md', payload / 'README.txt')
        shutil.copyfile(ROOT / 'patcher/KNOWN_ISSUES.md', payload / 'KNOWN_ISSUES.txt')
        shutil.copyfile(ROOT / 'THIRD_PARTY_NOTICES.md', payload / 'CREDITS.txt')
        (payload / 'Start Patcher.command').write_text(
            '#!/bin/sh\ncd -- "$(dirname -- "$0")" || exit 1\npython3 sacred_gold_patcher.py --gui\n', encoding='utf-8')
        (payload / 'Start Patcher.command').chmod(0o755)
        (payload / 'Start Patcher.bat').write_bytes(
            b'@echo off\r\ncd /d "%~dp0"\r\npy -3 sacred_gold_patcher.py --gui\r\nif errorlevel 1 pause\r\n')
        with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for path in sorted(payload.iterdir()):
                z.write(path, out.name + '/' + path.name)
        shutil.move(str(payload), out)
    print(f'Installer: {out}\nZIP: {archive}\nPatch bytes: {release["patch"]["size"]}')
    return release


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sacred-gold', type=Path, default=ROOT / 'local/sacred-gold/SacredGold-Complete-1.05.nds')
    parser.add_argument('--reforged', type=Path, default=ROOT / 'output/Platinum-Reforged-baseline.nds')
    parser.add_argument('--target', type=Path, default=ROOT / f'output/SacredGold-Reforged-{VERSION}.nds')
    parser.add_argument('--anvil-source', type=Path, default=ROOT / 'platinum-reforged-anvil')
    parser.add_argument('--xdelta3', type=Path, default=ROOT / 'local/tools/xdelta-build/xdelta3')
    parser.add_argument('--out', type=Path, default=ROOT / f'output/patcher/SacredGold-Reforged-{VERSION}-installer-v1')
    package(parser.parse_args())


if __name__ == '__main__':
    main()

"""Build a self-contained, offline-capable static Sacred Gold patcher from verified local patches."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'patcher/web'
sys.path.insert(0, str(ROOT / 'patcher'))
sys.path.insert(0, str(ROOT / 'tools'))
from sacred_gold_patcher import concatenate, decode, find_xdelta, fingerprint, run_tool, verify
from package_sacred_gold_patcher import INPUTS, OUTPUT, VERSION

CLEAN_ORDER = ['heartgold', 'platinum', 'black2', 'sacred_gold_patch', 'bundle']
LABELS = {'heartgold': 'HeartGold · USA Rev 0', 'platinum': 'Platinum · USA Rev 0',
          'black2': 'Black 2 · USA/Europe Rev 0', 'sacred_gold_patch': 'SacredGold105.xdelta · Complete 1.05',
          'bundle': 'reforged.bundle · original Anvil alpha', 'sacred_gold': 'Sacred Gold · Complete 1.05',
          'reforged': 'Platinum Reforged · original Anvil alpha'}
PATCHES = {
    'clean': dict(size=5339667, sha256='2203f72eaed6917e7f6e24f19ce5fe1af4ee05f62a0440766ffb0530f4cbc874'),
    'prepared': dict(size=1747417, sha256='361465e6e07a60ff4438087e194fc3c139329358e86f39c51e976292f32bd418'),
}
SITE_MEDIA = {'chuck-gym-preview.mp4', 'chuck-gym-poster.webp', 'hooh-gen5.gif',
              'lugia-gen5.gif', 'hooh-still.png', 'lugia-still.png'}


def replace_once(source, before, after):
    if source.count(before) != 1:
        raise ValueError('Pinned browser decoder no longer matches the reviewed adaptation.')
    return source.replace(before, after, 1)


def worker_source():
    provenance = json.loads((WEB / 'vendor/provenance.json').read_text())
    for name, expected in provenance.items():
        if fingerprint(WEB / 'vendor' / name)['sha256'] != expected['sha256']:
            raise ValueError(f'Vendored file changed: {name}')
    vcdiff = (WEB / 'vendor/vcdiff.js').read_text()
    vcdiff = replace_once(vcdiff, 'VCDIFF.prototype.apply=function(romFile, validate){',
                         'VCDIFF.prototype.apply=function(romFile, validate, progress){')
    vcdiff = replace_once(vcdiff, 'tempFile=new BinFile(newFileSize);', 'var tempFile=new BinFile(newFileSize);')
    start = vcdiff.index('\t\t\t\t\tvar addr = cache.decodeAddress(')
    end = vcdiff.index('\t\t\t\t}else if(instruction.type===VCD_RUN)', start)
    vcdiff = vcdiff[:start] + '''                    var addr = cache.decodeAddress(addRunDataIndex+winHeader.sourceLength, instruction.mode);
                    SacredGoldCore.copy(romFile, tempFile._u8array, targetWindowPosition,
                                        addRunDataIndex, winHeader, addr, size);
                    addRunDataIndex += size;
''' + vcdiff[end:]
    vcdiff = replace_once(vcdiff, '\t\t\t\tif(instruction.type===VCD_NOOP){', '''                if (!Number.isSafeInteger(size) || size < 0 || size > winHeader.targetWindowLength-addRunDataIndex)
                    throw new Error('Patch instruction exceeds its output window');
                if(instruction.type===VCD_NOOP){''')
    vcdiff = replace_once(vcdiff, 'if(validate && winHeader.adler32 &&',
                         'if(validate && winHeader.adler32 !== false &&')
    vcdiff = replace_once(vcdiff, '\t\ttargetWindowPosition += winHeader.targetWindowLength;', '''        if (addRunDataIndex !== winHeader.targetWindowLength)
            throw new Error('Patch did not fill its output window');
        targetWindowPosition += winHeader.targetWindowLength;
        if (progress) progress(targetWindowPosition / newFileSize);''')
    old = vcdiff[vcdiff.index('VCDIFF_Parser.prototype.read7BitEncodedInt=function(){'):
                 vcdiff.index('VCDIFF_Parser.prototype.decodeWindowHeader=function(){')]
    vcdiff = replace_once(vcdiff, old, '''VCDIFF_Parser.prototype.read7BitEncodedInt=function(){
    var value=0, part;
    do {
        if(this.offset >= this.fileSize) throw new Error('Truncated patch integer');
        part=this.readU8(); value=value*128+(part&127);
        if(!Number.isSafeInteger(value) || value>1073741824) throw new Error('Patch integer exceeds supported range');
    } while(part&128);
    return value;
};
''')
    return '\n'.join([(WEB / 'vendor/sha256.js').read_text(),
                      (WEB / 'vendor/BinFile.js').read_text(), vcdiff,
                      (WEB / 'core.js').read_text(), (WEB / 'worker.js').read_text()])


def profile(name, order, patch):
    verify(patch, PATCHES[name], f'{name.title()} release delta')
    return dict(id=name, version=VERSION,
                inputs=[dict(id=key, label=LABELS[key], **INPUTS[key]) for key in order],
                output=OUTPUT, patch=fingerprint(patch),
                data=base64.b64encode(patch.read_bytes()).decode('ascii'))


def js_string(value):
    # Avoid ending an HTML script element from text embedded inside JavaScript strings.
    return json.dumps(value, ensure_ascii=True).replace('<', '\\u003c')


def render_html(config):
    scripts = ('const SG_RELEASE=' + js_string(config) + ';\nconst SG_WORKER=' +
               js_string(worker_source()) + ';\n' + (WEB / 'app.js').read_text())
    styles = (WEB / 'style.css').read_text()
    digest = lambda text: base64.b64encode(hashlib.sha256(text.encode()).digest()).decode()
    policy = ("default-src 'none'; script-src 'sha256-" + digest(scripts) +
              "'; style-src 'sha256-" + digest(styles) +
              "'; worker-src blob:; connect-src 'none'; img-src 'self' data:; media-src 'self'; object-src 'none'; "
              "base-uri 'none'; form-action 'none'; frame-src 'none'")
    html = (WEB / 'index.html').read_text().replace('<!-- CSP -->', policy)
    html = html.replace('/* SITE_STYLES */', styles).replace('/* SITE_SCRIPT */', scripts)
    if '<!-- CSP -->' in html or '/* SITE_' in html:
        raise ValueError('Site template is incomplete.')
    return html


def build_site(out, clean_patch, prepared_patch):
    if out.exists() or out.with_suffix('.zip').exists():
        raise FileExistsError('Choose a new web package output directory.')
    config = dict(format=1, version=VERSION,
                  profiles={'clean': profile('clean', CLEAN_ORDER, clean_patch),
                            'prepared': profile('prepared', ['sacred_gold', 'reforged'], prepared_patch)})
    html = render_html(config)
    media = json.loads((WEB / 'media/manifest.json').read_text())
    if set(media['files']) != SITE_MEDIA:
        raise ValueError('Only the reviewed clip, poster and legendary sprites may be packaged.')
    for name, expected in media['files'].items():
        verify(WEB / 'media' / name, expected, 'Reviewed gameplay preview')
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.sg-web-package-', dir=out.parent) as directory:
        staging = Path(directory) / out.name
        staging.mkdir()
        (staging / 'index.html').write_text(html, encoding='utf-8')
        (staging / '.nojekyll').touch()
        (staging / 'media').mkdir()
        for name in [*media['files'], 'manifest.json']:
            shutil.copyfile(WEB / 'media' / name, staging / 'media' / name)
        shutil.copyfile(WEB / 'README.md', staging / 'README.md')
        shutil.copyfile(WEB / 'CREDITS.md', staging / 'CREDITS.txt')
        shutil.copyfile(ROOT / 'patcher/KNOWN_ISSUES.md', staging / 'KNOWN_ISSUES.txt')
        notices = staging / 'licenses'
        notices.mkdir()
        for name in ['RomPatcher-LICENSE.txt', 'SHA256-LICENSE.txt', 'Apache-2.0.txt', 'G4Patcher-LICENSE.txt']:
            shutil.copyfile(WEB / 'vendor' / name, notices / name)
        (staging / 'release.json').write_text(json.dumps(
            {**config, 'profiles': {k: {field: value for field, value in p.items() if field != 'data'}
                                   for k, p in config['profiles'].items()}}, indent=2) + '\n')
        archive = Path(directory) / 'site.zip'
        with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for path in sorted(staging.rglob('*')):
                if path.is_file(): z.write(path, out.name + '/' + path.relative_to(staging).as_posix())
        shutil.move(str(staging), out)
        try:
            from sacred_gold_patcher import publish
            publish(archive, out.with_suffix('.zip'))
        except BaseException:
            shutil.rmtree(out)
            raise
    return config


def encode_clean_patch(paths, target, output, xdelta):
    """Maintainer-only generation. Browser users supply files without executing this pipeline."""
    if output.exists():
        raise FileExistsError(output)
    for key in CLEAN_ORDER:
        verify(paths[key], INPUTS[key], LABELS[key])
    verify(target, OUTPUT, f'Sacred Gold {VERSION} target')
    executable = find_xdelta(xdelta)
    version = subprocess.check_output([executable, '-V'], stderr=subprocess.STDOUT, text=True)
    if 'version 3.2.2,' not in version:
        raise ValueError('Release encoding is pinned to xdelta3 3.2.2.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.sg-direct-delta-', dir=output.parent) as folder:
        folder = Path(folder)
        source, delta, decoded = folder / 'source.bin', folder / 'release.xdelta', folder / 'roundtrip.nds'
        concatenate([paths[key] for key in CLEAN_ORDER], source)
        run_tool([executable, '-e', '-9', '-D', '-A', '-S', 'none', '-B', str(1024 ** 3),
                  '-s', source, target, delta])
        verify(delta, PATCHES['clean'], 'Reproduced clean delta')
        decode(executable, source, delta, decoded)
        verify(decoded, OUTPUT, 'Native decoder roundtrip')
        from sacred_gold_patcher import publish
        publish(delta, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clean-patch', type=Path, default=ROOT / f'output/patcher/browser-research/SacredGold-{VERSION}-clean.xdelta')
    parser.add_argument('--prepared-patch', type=Path,
        default=ROOT / f'output/patcher/SacredGold-Reforged-{VERSION}-installer-v1/SacredGold-Reforged-{VERSION}.xdelta')
    parser.add_argument('--out', type=Path, default=ROOT / f'output/patcher/SacredGold-Reforged-{VERSION}-web-v1')
    parser.add_argument('--encode-clean', action='store_true', help='regenerate the clean delta from pinned local inputs first')
    parser.add_argument('--xdelta3', type=Path, default=ROOT / 'local/tools/xdelta-build/xdelta3')
    parser.add_argument('--target', type=Path, default=ROOT / f'output/SacredGold-Reforged-{VERSION}.nds')
    defaults = {
        'heartgold': ROOT / 'games/Pokemon HeartGold Version (USA).nds',
        'platinum': ROOT / 'games/Pokemon-Platinum-ROM-en.nds',
        'black2': ROOT / 'games/Pokemon - Black Version 2 (USA, Europe) (NDSi Enhanced).nds',
        'sacred_gold_patch': ROOT / 'inputs/sacred-gold/modern/SGSS_xDeltaPatches/SacredGold105.xdelta',
        'bundle': ROOT / 'inputs/anvil/reforged.bundle',
    }
    for key, default in defaults.items():
        parser.add_argument('--' + key.replace('_', '-'), type=Path, default=default)
    args = parser.parse_args()
    if args.encode_clean:
        encode_clean_patch({key: getattr(args, key) for key in CLEAN_ORDER}, args.target, args.clean_patch, args.xdelta3)
    config = build_site(args.out.resolve(), args.clean_patch, args.prepared_patch)
    print(f'Offline/Pages site: {args.out}\nZIP: {args.out.with_suffix(".zip")}')
    print('Patch sizes:', {name: p['patch']['size'] for name, p in config['profiles'].items()})


if __name__ == '__main__':
    main()

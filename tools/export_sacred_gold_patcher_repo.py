"""Export a source-only Sacred Gold patcher repository; never traverse the game workspace."""
import argparse
from pathlib import Path
import shutil
import tempfile
import zipfile
from package_sacred_gold_web import SITE_MEDIA

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    'patcher/sacred_gold_patcher.py', 'patcher/README.md', 'patcher/KNOWN_ISSUES.md',
    'tools/package_sacred_gold_patcher.py', 'tools/package_sacred_gold_web.py',
    'tools/generate_patcher_fixtures.py', 'tools/export_sacred_gold_patcher_repo.py',
    'tests/test_sacred_gold_patcher.py', 'tests/test_web_patcher.mjs',
    'tests/test_web_patcher_package.py', 'tests/fixtures/patcher-vcdiff.json', 'THIRD_PARTY_NOTICES.md',
    'patcher/repository/README.md', 'patcher/repository/pages.yml', 'patcher/repository/tests.yml',
]
IGNORES = '''dist/
output/
local/
games/
inputs/
release-inputs/
__pycache__/
*.pyc
*.nds
*.sav
*.dsv
*.dst
*.bundle
*.xdelta
*.zip
*.mov
.DS_Store
'''


def export(out):
    out = out.resolve()
    if out.exists() or out.with_suffix('.zip').exists():
        raise FileExistsError('Choose a new source export directory.')
    files = list(FILES)
    for path in (ROOT / 'patcher/web').rglob('*'):
        if path.is_file() and (path.suffix in ('.js', '.css', '.html', '.md', '.json', '.txt') or
                             path.name in SITE_MEDIA):
            files.append(path.relative_to(ROOT).as_posix())
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.sg-source-export-', dir=out.parent) as temp:
        staging = Path(temp) / out.name
        staging.mkdir()
        for name in sorted(set(files)):
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        shutil.copyfile(ROOT / 'patcher/repository/README.md', staging / 'README.md')
        (staging / '.gitignore').write_text(IGNORES)
        workflows = staging / '.github/workflows'
        workflows.mkdir(parents=True)
        for name in ('pages.yml', 'tests.yml'):
            shutil.copyfile(ROOT / 'patcher/repository' / name, workflows / name)
        archive = Path(temp) / 'source.zip'
        with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for path in sorted(staging.rglob('*')):
                if path.is_file(): z.write(path, out.name + '/' + path.relative_to(staging).as_posix())
        shutil.move(str(staging), out)
        from sys import path as search_path
        search_path.insert(0, str(ROOT / 'patcher'))
        from sacred_gold_patcher import publish
        publish(archive, out.with_suffix('.zip'))
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'output/patcher/SacredGold-Patcher-source-v1')
    args = parser.parse_args()
    files = export(args.out)
    print(f'Source-only export: {args.out}\nSource files: {len(set(files))}')


if __name__ == '__main__':
    main()

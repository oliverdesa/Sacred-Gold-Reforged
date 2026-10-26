"""Generate synthetic VCDIFF fixtures with native xdelta; no game files are read."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'patcher'))
from sacred_gold_patcher import find_xdelta, run_tool


def materialize(source):
    pattern = bytes.fromhex(source['hex'])
    size = source.get('size', len(pattern))
    return (pattern * ((size + len(pattern) - 1) // len(pattern)))[:size]


def target_bytes(parts, sources):
    out = []
    for part in parts:
        if 'copy' in part:
            index, start, length = part['copy']
            out.append(sources[index][start:start + length])
        else:
            out.append(materialize(part))
    return b''.join(out)


def specs():
    pattern = bytes(range(256)).hex()
    sources = [dict(hex=pattern, size=4096), dict(hex=bytes(reversed(range(256))).hex(), size=8192)]
    cases = [
        ('identity', sources, [{'copy': [0, 0, 4096]}]),
        ('append', sources, [{'copy': [0, 0, 4096]}, {'hex': 'aabbccddeeff'}]),
        ('prepend', sources, [{'hex': '12' * 17}, {'copy': [1, 0, 8192]}]),
        ('reorder', sources, [{'copy': [1, 200, 4000]}, {'copy': [0, 2, 3000]}]),
        ('boundary', sources, [{'copy': [0, 4000, 96]}, {'copy': [1, 0, 4000]}]),
        ('single-byte', [{'hex': 'ab'}], [{'hex': 'fe'}]),
        ('run-zero', sources, [{'hex': '00', 'size': 30000}]),
        ('run-ff', sources, [{'hex': 'ff', 'size': 30000}]),
        ('overlap', sources, [{'hex': '416263', 'size': 45000}]),
        ('small-windows', sources, [{'copy': [0, 0, 4096]}, {'hex': 'ab0c', 'size': 90000}]),
        ('app-header', sources, [{'hex': '00112233'}, {'copy': [0, 0, 4096]}]),
        ('default-window-boundary', [{'hex': pattern, 'size': 1024}], [{'hex': pattern, 'size': 9 * 1024**2 + 13}]),
        ('source-page-boundary', [{'hex': pattern, 'size': 5 * 1024**2 + 19}],
            [{'copy': [0, 4 * 1024**2 - 5, 1024**2 + 24]}, {'hex': 'f00dcafe'}]),
    ]
    for index in range(12):
        literal = hashlib.sha256(f'synthetic-test-{index}'.encode()).hexdigest()
        cases.append((f'mixed-{index}', sources,
            [{'copy': [index % 2, index * 17, 1200 + index * 31]}, {'hex': literal},
             {'hex': f'{index:02x}', 'size': 500 + index * 53}, {'copy': [1, 3200 - index * 19, 3000]}]))
    return cases


def generate(xdelta):
    fixtures = []
    with tempfile.TemporaryDirectory(prefix='sg-synthetic-') as folder:
        folder = Path(folder)
        for name, recipes, parts in specs():
            inputs = [materialize(recipe) for recipe in recipes]
            expected = target_bytes(parts, inputs)
            (folder / 'source.bin').write_bytes(b''.join(inputs))
            (folder / 'target.bin').write_bytes(expected)
            delta, decoded = folder / 'patch.xdelta', folder / 'decoded.bin'
            flags = ['-Asynthetic-fixture'] if name == 'app-header' else ['-A']
            if name == 'small-windows': flags += ['-W', '16384']
            run_tool([xdelta, '-e', '-9', '-D', '-S', 'none', *flags, '-s', folder / 'source.bin', folder / 'target.bin', delta])
            run_tool([xdelta, '-d', '-D', '-R', '-s', folder / 'source.bin', delta, decoded])
            if decoded.read_bytes() != expected: raise ValueError('Native fixture verification failed')
            stamp = lambda data: dict(size=len(data), sha256=hashlib.sha256(data).hexdigest())
            fixtures.append(dict(name=name, sources=recipes, target=parts,
                profile=dict(inputs=[dict(id=str(i), label=f'Synthetic input {i}', **stamp(data))
                                     for i, data in enumerate(inputs)],
                             output=stamp(expected), patch=stamp(delta.read_bytes())),
                patch=base64.b64encode(delta.read_bytes()).decode()))
            delta.unlink()
            decoded.unlink()
    return dict(description='Synthetic fixtures generated and round-tripped with native xdelta3. No ROMs.', cases=fixtures)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xdelta3', default=str(ROOT / 'local/tools/xdelta-build/xdelta3'))
    parser.add_argument('--out', type=Path, default=ROOT / 'tests/fixtures/patcher-vcdiff.json')
    args = parser.parse_args()
    result = generate(find_xdelta(args.xdelta3))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(f'{len(result["cases"])} independently verified synthetic fixtures: {args.out}')


if __name__ == '__main__':
    main()

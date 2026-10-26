"""Local Sacred Gold Reforged installer. Run without arguments for the file picker."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading

HERE = Path(__file__).resolve().parent
LIMIT = 1024 ** 3


def fingerprint(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 ** 2), b''):
            digest.update(chunk)
    return dict(size=path.stat().st_size, sha256=digest.hexdigest())


def verify(path, expected, label):
    path = Path(path)
    if not path.is_file():
        raise ValueError(f'{label}: file not found: {path}')
    if path.stat().st_size != expected['size'] or fingerprint(path) != expected:
        raise ValueError(f'{label}: unsupported or damaged file. Use the exact version in README.txt.')
    return path.resolve()


def load_release(path):
    path = Path(path).resolve()
    if path.stat().st_size > 1024 ** 2:
        raise ValueError('Release manifest is too large.')
    release = json.loads(path.read_text(encoding='utf-8'))
    if release['format'] != 1 or release['source_order'] != ['sacred_gold', 'reforged']:
        raise ValueError('Unsupported patch format or source order.')
    for spec in [*release['inputs'].values(), release['output'], release['patch']]:
        if (type(spec['size']) is not int or not 0 < spec['size'] <= LIMIT
                or len(spec['sha256']) != 64
                or any(c not in '0123456789abcdef' for c in spec['sha256'])):
            raise ValueError('Invalid file size or checksum in release manifest.')
    name = release['patch_name']
    if not name or '/' in name or '\\' in name or name in ('.', '..'):
        raise ValueError('Patch filename must be beside the release manifest.')
    verify(path.parent / name, release['patch'], 'Release patch')
    return release


def find_xdelta(value=None):
    candidate = str(value) if value else 'xdelta3'
    found = shutil.which(candidate)
    if not found:
        raise ValueError('xdelta3 was not found. Install xdelta3, or select its executable in the file picker.')
    return str(Path(found).resolve())


def run_tool(args):
    env = os.environ.copy()
    # xdelta reads options from this variable, including options disabling checksums.
    env.pop('XDELTA', None)
    result = subprocess.run([str(a) for a in args], env=env, capture_output=True, text=True,
                            errors='replace', shell=False)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()[-4000:]
        raise ValueError(f'{Path(args[0]).name} failed ({result.returncode}): {detail}')


def decode(xdelta, source, patch, output):
    # Disable external decompression/recompression, retain source/target checksums, never force.
    run_tool([xdelta, '-d', '-D', '-R', '-s', source, patch, output])


def concatenate(paths, output):
    with Path(output).open('xb') as dest:
        for path in paths:
            with Path(path).open('rb') as source:
                shutil.copyfileobj(source, dest, 1024 ** 2)


def publish(temporary, output):
    """Only publish verified bytes; exclusive creation protects existing files, including symlinks."""
    output = Path(output)
    # A hard link is atomic and cannot replace another file. exFAT has no hard links.
    try:
        os.link(temporary, output)
    except FileExistsError:
        raise ValueError(f'Output already exists: {output}. Choose a new filename.') from None
    except OSError:
        dest = output.open('xb')
        try:
            with dest:
                with Path(temporary).open('rb') as source:
                    shutil.copyfileobj(source, dest, 1024 ** 2)
        except BaseException:
            output.unlink(missing_ok=True)
            raise


def validate_anvil(root, release):
    root = Path(root).resolve()
    expected = release['anvil_files']
    folders = ('anvil/reforged_anvil', 'tools/port')
    actual = {p.relative_to(root).as_posix() for folder in folders
              for p in (root / folder).glob('*.py')}
    if actual != {p for p in expected if p.endswith('.py')}:
        raise ValueError('Anvil source files do not match the pinned version. See README.txt.')
    for name, sha in expected.items():
        path = root / name
        if not path.is_file() or fingerprint(path)['sha256'] != sha:
            raise ValueError(f'Anvil source differs from the pinned version: {name}')
    return root


ANVIL_BUILD = '''import sys
from pathlib import Path
root, pt, bw, bundle, out = sys.argv[1:]
sys.path.insert(0, str(Path(root) / "anvil"))
from reforged_anvil.build import make
from reforged_anvil.bundle import Bundle
make(pt, bw, out, bundle=Bundle(bundle))
'''


def build(options, progress=print):
    release_path = Path(options['release']).resolve()
    release = load_release(release_path)
    output = Path(options['out']).expanduser().absolute()
    if output.suffix.lower() != '.nds':
        raise ValueError('Choose an .nds output filename. Saves are never installer outputs.')
    if os.path.lexists(output):
        raise ValueError(f'Output already exists: {output}. Choose a new filename.')
    if not output.parent.is_dir():
        raise ValueError('The output folder does not exist.')
    xdelta = find_xdelta(options.get('xdelta3'))
    clean = bool(options.get('heartgold'))
    clean_keys = ('heartgold', 'platinum', 'black2', 'sacred_gold_patch', 'anvil_source', 'bundle')
    prepared_keys = ('sacred_gold', 'reforged')
    required, other = (clean_keys, prepared_keys) if clean else (prepared_keys, clean_keys)
    if any(not options.get(key) for key in required) or any(options.get(key) for key in other):
        raise ValueError('Choose either both prepared ROMs, or all six clean-build inputs. Do not mix modes.')
    progress('Checking source files...')
    files = {key: verify(options[key], release['inputs'][key], key.replace('_', ' ').title())
             for key in required if key != 'anvil_source'}
    if clean:
        anvil = validate_anvil(options['anvil_source'], release)
        try:
            import PIL  # noqa: F401 -- Anvil needs Pillow in the same Python installation.
        except ImportError:
            raise ValueError('Clean-ROM mode requires Pillow. Run: python3 -m pip install Pillow') from None
    needed = (sum(release['inputs'][k]['size'] for k in prepared_keys)
              + release['output']['size'] + (400 * 1024 ** 2 if clean else 0) + 64 * 1024 ** 2)
    if shutil.disk_usage(output.parent).free < needed:
        raise ValueError(f'Not enough free space in the output folder. Allow at least {needed / 1024**3:.1f} GiB.')
    with tempfile.TemporaryDirectory(prefix='.sacred-gold-build-', dir=output.parent) as temp:
        temp = Path(temp)
        if clean:
            progress('Applying Sacred Gold Complete 1.05...')
            sg = temp / 'SacredGold-Complete.nds'
            decode(xdelta, files['heartgold'], files['sacred_gold_patch'], sg)
            verify(sg, release['inputs']['sacred_gold'], 'Prepared Sacred Gold')
            progress('Building the pinned Reforged donor from Platinum and Black 2 (this may take a few minutes)...')
            donor = temp / 'Reforged-donor.nds'
            run_tool([sys.executable, '-c', ANVIL_BUILD, anvil, files['platinum'], files['black2'],
                      files['bundle'], donor])
            verify(donor, release['inputs']['reforged'], 'Prepared Reforged donor')
            files.update(sacred_gold=sg, reforged=donor)
        progress('Preparing the local patch source...')
        source = temp / 'combined-source.bin'
        concatenate([files[key] for key in release['source_order']], source)
        progress(f'Building Sacred Gold Reforged {release["version"]}...')
        staged = temp / 'verified-output.nds'
        decode(xdelta, source, release_path.parent / release['patch_name'], staged)
        verify(staged, release['output'], 'Finished ROM')
        publish(staged, output)
    progress(f'Finished: {output}\nSHA-256: {release["output"]["sha256"]}')
    return fingerprint(output)


def gui(release_path):
    try:
        import tkinter as tk
        from tkinter import filedialog, ttk
    except ImportError:
        raise ValueError('This Python has no Tk file picker. Use command-line mode, or install Python with Tk.') from None
    release = load_release(release_path)
    root = tk.Tk()
    root.title(f'Sacred Gold Reforged {release["version"]} — local installer')
    root.minsize(760, 560)
    frame = ttk.Frame(root, padding=16)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Build your game locally. Source files and saves are preserved.').pack(anchor='w')
    tabs = ttk.Notebook(frame)
    tabs.pack(fill='x', pady=12)
    values = {}

    def field(parent, key, title, directory=False, save=False, initial=''):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=4)
        ttk.Label(row, text=title, width=26).pack(side='left')
        var = values[key] = tk.StringVar(value=initial)
        ttk.Entry(row, textvariable=var).pack(side='left', fill='x', expand=True, padx=6)

        def browse():
            if directory:
                path = filedialog.askdirectory(parent=root, title=title)
            elif save:
                path = filedialog.asksaveasfilename(parent=root, title=title, defaultextension='.nds',
                         initialfile=Path(var.get()).name, filetypes=[('Nintendo DS ROM', '*.nds')])
            else:
                path = filedialog.askopenfilename(parent=root, title=title)
            if path:
                var.set(path)
        ttk.Button(row, text='Choose…', command=browse).pack(side='right')

    clean = ttk.Frame(tabs, padding=8)
    prepared = ttk.Frame(tabs, padding=8)
    tabs.add(clean, text='Clean ROMs')
    tabs.add(prepared, text='Prepared ROMs')
    clean_fields = [('heartgold', 'HeartGold USA Rev 0'), ('platinum', 'Platinum USA Rev 0'),
                    ('black2', 'Black 2 USA/Europe Rev 0'), ('sacred_gold_patch', 'SacredGold105.xdelta'),
                    ('anvil_source', 'Pinned Anvil source folder'), ('bundle', 'Pinned reforged.bundle')]
    for key, title in clean_fields:
        field(clean, key, title, directory=key == 'anvil_source')
    ttk.Label(prepared, text='Use the exact Complete 1.05 ROM and original Anvil donor listed in README.txt.',
              wraplength=680).pack(anchor='w', pady=6)
    field(prepared, 'sacred_gold', 'Sacred Gold Complete 1.05')
    field(prepared, 'reforged', 'Original Reforged donor')
    field(frame, 'xdelta3', 'xdelta3 executable (or PATH)')
    field(frame, 'out', 'New output ROM', save=True,
          initial=str(Path.home() / f'SacredGold-Reforged-{release["version"]}.nds'))
    status = tk.StringVar(value='Select inputs, then Build. See README.txt for supported versions and setup.')
    ttk.Label(frame, textvariable=status, wraplength=700).pack(fill='x', pady=12)
    messages = queue.Queue()
    running = [False]

    def start():
        keys = [k for k, _ in clean_fields] if tabs.index(tabs.select()) == 0 else ['sacred_gold', 'reforged']
        options = {key: values[key].get().strip() for key in keys + ['xdelta3', 'out']}
        options['release'] = release_path
        running[0] = True
        button.config(state='disabled')

        def work():
            try:
                build(options, lambda message: messages.put(('progress', message)))
            except Exception as error:
                messages.put(('progress', f'Build stopped: {error}'))
            finally:
                messages.put(('done', None))
        threading.Thread(target=work, daemon=True).start()

    def poll():
        while True:
            try:
                kind, message = messages.get_nowait()
            except queue.Empty:
                break
            if kind == 'done':
                running[0] = False
                button.config(state='normal')
            else:
                status.set(message)
        root.after(100, poll)

    def close():
        if running[0]:
            status.set('A build is running. Wait for it to finish before closing the installer.')
        else:
            root.destroy()
    button = ttk.Button(frame, text='Build Sacred Gold Reforged', command=start)
    button.pack(anchor='e')
    root.protocol('WM_DELETE_WINDOW', close)
    poll()
    root.mainloop()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, default=HERE / 'release.json', help='release manifest beside its patch')
    parser.add_argument('--gui', action='store_true', help='open the file picker')
    for key in ('heartgold', 'platinum', 'black2', 'sacred_gold_patch', 'anvil_source', 'bundle',
                'sacred_gold', 'reforged', 'xdelta3', 'out'):
        parser.add_argument('--' + key.replace('_', '-'), type=Path)
    args = parser.parse_args(argv)
    if args.gui or not any(getattr(args, key) for key in ('heartgold', 'platinum', 'black2',
            'sacred_gold_patch', 'anvil_source', 'bundle', 'sacred_gold', 'reforged', 'out')):
        gui(args.release)
    else:
        if not args.out:
            parser.error('--out is required for command-line builds')
        build(vars(args))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        sys.exit(f'Build stopped: {error}')

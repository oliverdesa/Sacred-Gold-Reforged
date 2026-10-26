/* Sacred Gold by Drayano; upstream Reforged/Anvil by smoldice. Tests use synthetic data only. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync, writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';
import test from 'node:test';

const root = fileURLToPath(new URL('../', import.meta.url));
const code = execFileSync(process.env.SG_PATCHER_PYTHON || 'python3', ['-S', '-c', "import sys;sys.path.insert(0,'tools');from package_sacred_gold_web import worker_source;print(worker_source())"], {cwd: root, encoding: 'utf8'});
const context = {Uint8Array, ArrayBuffer, Int16Array, DataView, console,
  fetch() { throw Error('Network access is forbidden in the patch engine'); }};
context.self = context;
vm.createContext(context);
vm.runInContext(code, context);
const core = context.SacredGoldCore;
const cases = JSON.parse(readFileSync(new URL('./fixtures/patcher-vcdiff.json', import.meta.url))).cases;
const hash = bytes => createHash('sha256').update(bytes).digest('hex');

function bytes(recipe) {
  const pattern = Buffer.from(recipe.hex, 'hex');
  const out = new Uint8Array(recipe.size ?? pattern.length);
  for (let at = 0; at < out.length; at++) out[at] = pattern[at % pattern.length];
  return out;
}
function setup(fixture) {
  const files = fixture.sources.map(recipe => { const data = bytes(recipe); return {size: data.length, data}; });
  const read = (file, at, length) => file.data.slice(at, at + length);
  const patch = new Uint8Array(Buffer.from(fixture.patch, 'base64'));
  return {files, read, patch, profile: structuredClone(fixture.profile)};
}

for (const fixture of cases) test(`native xdelta compatibility: ${fixture.name}`, () => {
  const {files, read, patch, profile} = setup(fixture);
  const before = files.map(file => hash(file.data));
  const output = core.assemble(profile, files, patch, read);
  const expected = Buffer.concat(fixture.target.map(part => {
    if ('copy' in part) { const [index, start, length] = part.copy; return Buffer.from(files[index].data.subarray(start, start + length)); }
    return Buffer.from(bytes(part));
  }));
  assert.equal(hash(output.bytes), hash(expected));
  assert.equal(output.sha256, profile.output.sha256);
  assert.deepEqual(files.map(file => hash(file.data)), before);
});

test('SHA-256 matches Node crypto across chunk boundaries and known vectors', () => {
  for (const length of [0, 1, 55, 56, 63, 64, 65, 1000, core.CHUNK - 1, core.CHUNK, core.CHUNK + 1]) {
    const data = bytes({hex: '0a23ff0081', size: length});
    assert.equal(core.hashFile({size: length, data}, (f, at, n) => f.data.slice(at, at + n)), hash(data));
  }
});

test('source ranges cross file and cache-page boundaries correctly', () => {
  const data = bytes({hex: '0123456789abcdef', size: core.CHUNK + 13});
  const files = [{size: data.length, data}, {size: 7, data: new Uint8Array([11, 22, 33, 44, 55, 66, 77])}];
  let reads = 0;
  const source = new core.CompositeSource(files, (f, at, n) => { reads++; return f.data.slice(at, at + n); });
  const out = new Uint8Array(40);
  source.copyRange(out, 0, data.length - 33, 40);
  assert.deepEqual(Buffer.from(out), Buffer.concat([Buffer.from(data.subarray(-33)), Buffer.from(files[1].data)]));
  for (let i = 0; i < 50; i++) source.copyRange(out, 0, data.length - 20, 20);
  assert.ok(reads <= 3, `small reads should hit cache, got ${reads}`);
  assert.throws(() => source.copyRange(out, 0, -1, 1), /outside/);
});

test('source cache stays within 16 MiB and evicts older pages', () => {
  const file = {size: core.CHUNK * 6};
  let reads = 0;
  const source = new core.CompositeSource([file], (_file, _at, n) => { reads++; return new Uint8Array(n); });
  for (let at = 0; at < file.size; at += 65536) source.copyRange(new Uint8Array(1), 0, at, 1);
  assert.ok([...source.cache.values()].reduce((n, page) => n + page.length, 0) <= 16 * 1024 * 1024);
  const before = reads;
  source.copyRange(new Uint8Array(1), 0, 0, 1);
  assert.equal(reads, before + 1);
});

test('overlapping COPY and source-to-target crossing follow RFC 3284', () => {
  const data = new Uint8Array([1, 2, 3, 4]);
  const source = new core.CompositeSource([{size: 4, data}], (f, at, n) => f.data.slice(at, at + n));
  const out = new Uint8Array(12);
  core.copy(source, out, 0, 0, {sourceLength: 4, sourcePosition: 0, targetWindowLength: 12, indicator: 1}, 0, 12);
  assert.deepEqual(Array.from(out), [1,2,3,4,1,2,3,4,1,2,3,4]);
  assert.throws(() => core.copy(source, out, 0, 0, {sourceLength: 0, targetWindowLength: 12}, 0, 2), /Invalid/);
});

test('VCD_TARGET reads only an earlier output window', () => {
  const out = new Uint8Array(12); out.set([1,2,3,4,5,6]);
  core.copy(null, out, 6, 0, {sourceLength: 3, sourcePosition: 1, targetWindowLength: 6, indicator: 2}, 0, 6);
  assert.deepEqual(Array.from(out), [1,2,3,4,5,6,2,3,4,2,3,4]);
});

test('wrong sizes are rejected before reading source data', () => {
  const s = setup(cases[0]); s.files[1].size--;
  assert.throws(() => core.assemble(s.profile, s.files, s.patch, () => assert.fail('must not read')), /wrong file size/);
});

test('wrong source revision, damaged patch, and short reads are rejected', () => {
  const s = setup(cases[0]); s.files[0].data[0] ^= 1;
  assert.throws(() => core.assemble(s.profile, s.files, s.patch, s.read), /checksum does not match/);
  s.patch[0] ^= 1;
  assert.throws(() => core.assemble(s.profile, s.files, s.patch, s.read), /release patch is damaged/);
  const good = setup(cases[0]);
  assert.throws(() => core.assemble(good.profile, good.files, good.patch, () => new Uint8Array(1)), /read completely/);
});

test('no verified output is returned for the wrong final hash', () => {
  const s = setup(cases[0]); s.profile.output.sha256 = '0'.repeat(64);
  assert.throws(() => core.assemble(s.profile, s.files, s.patch, s.read), /Finished ROM failed/);
});

test('truncated and oversized patch headers fail quickly', () => {
  const {patch, files, profile} = setup(cases[0]);
  const sourceSize = files.reduce((n, f) => n + f.size, 0);
  for (let at = 0; at < patch.length; at++) assert.throws(() => core.preflight(patch.subarray(0, at), sourceSize, profile.output.size));
  const bad = new Uint8Array([0xd6,0xc3,0xc4,0,0,5,255,255,255,255,255,255,255]);
  assert.throws(() => core.preflight(bad, sourceSize, profile.output.size), /large|range|Truncated/);
});

test('deterministic patch mutation never returns unverified data or hangs', {timeout: 30000}, () => {
  const s = setup(cases[0]);
  context.testFiles = s.files; context.testRead = s.read;
  for (let index = 0; index < s.patch.length; index++) {
    const changed = s.patch.slice(); changed[index] ^= 0x80;
    const profile = structuredClone(s.profile); profile.patch.sha256 = hash(changed);
    context.testProfile = profile; context.testPatch = changed;
    let result;
    try {
      result = vm.runInContext('SacredGoldCore.assemble(testProfile,testFiles,testPatch,testRead)', context, {timeout: 1000});
    } catch (error) {
      assert.ok(!String(error).includes('Script execution timed out'), `mutation ${index} hung`);
      continue;
    }
    assert.equal(hash(result.bytes), profile.output.sha256);
  }
});

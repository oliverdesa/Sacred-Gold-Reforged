/* Local assembly around RomPatcher.js by Marc Robledo and js-sha256 by Chen, Yi-Cyuan. */
(function (root) {
  'use strict';
  const CHUNK = 4 * 1024 * 1024;
  const PAGE = 64 * 1024;
  const CACHE_PAGES = 256;
  const MAX_ROM = 1024 * 1024 * 1024;
  const HEX = /^[a-f0-9]{64}$/;

  function fail(message) { throw new Error(message); }

  function spec(info) {
    if (!info || !Number.isSafeInteger(info.size) || info.size <= 0 || info.size > MAX_ROM ||
        !HEX.test(info.sha256)) fail('Invalid release file metadata.');
  }

  function readExact(read, file, start, length) {
    if (!Number.isSafeInteger(start) || !Number.isSafeInteger(length) || start < 0 || length < 0 ||
        start + length > file.size || length > CHUNK) fail('Patch requested an invalid file range.');
    const bytes = read(file, start, length);
    if (!(bytes instanceof Uint8Array) || bytes.byteLength !== length) fail('A selected file could not be read completely. Select it again.');
    return bytes;
  }

  function hashFile(file, read, progress = () => {}) {
    const hash = root.sha256.create();
    for (let at = 0; at < file.size; at += CHUNK) {
      hash.update(readExact(read, file, at, Math.min(CHUNK, file.size - at)));
      progress(Math.min(1, (at + CHUNK) / file.size));
    }
    return hash.hex();
  }

  function verifyFile(file, expected, label, read, progress) {
    spec(expected);
    if (!file || file.size !== expected.size) fail(`${label}: wrong file size. Choose the exact version listed under Input details.`);
    const actual = hashFile(file, read, progress);
    if (actual !== expected.sha256) fail(`${label}: checksum does not match. This may be another revision, a modified ROM, or a damaged file.`);
    return actual;
  }

  class CompositeSource {
    constructor(files, read) {
      this.files = files;
      this.read = read;
      this.cache = new Map();
      this.starts = [];
      this.fileSize = files.reduce((total, file) => { this.starts.push(total); return total + file.size; }, 0);
      if (this.fileSize > MAX_ROM) fail('Combined source is larger than this release supports.');
    }

    copyRange(target, targetOffset, sourceOffset, length) {
      if (![targetOffset, sourceOffset, length].every(Number.isSafeInteger) ||
          Math.min(targetOffset, sourceOffset, length) < 0 || sourceOffset + length > this.fileSize ||
          targetOffset + length > target.byteLength) fail('Patch copy is outside a verified source or output.');
      while (length) {
        let index = this.files.length - 1;
        while (sourceOffset < this.starts[index]) index--;
        const offset = sourceOffset - this.starts[index];
        const pageStart = Math.floor(offset / PAGE) * PAGE;
        const key = `${index}:${pageStart}`;
        let page = this.cache.get(key);
        if (!page) {
          page = readExact(this.read, this.files[index], pageStart, Math.min(PAGE, this.files[index].size - pageStart));
          if (this.cache.size === CACHE_PAGES) this.cache.delete(this.cache.keys().next().value);
        } else this.cache.delete(key);
        this.cache.set(key, page);
        const within = offset - pageStart;
        const count = Math.min(length, page.byteLength - within);
        target.set(page.subarray(within, within + count), targetOffset);
        sourceOffset += count;
        targetOffset += count;
        length -= count;
      }
    }
  }

  // Only the uncompressed standard-table VCDIFF format emitted by our release builder.
  function preflight(bytes, sourceSize, targetSize) {
    let at = 0;
    const byte = () => at < bytes.length ? bytes[at++] : fail('Truncated patch.');
    const integer = () => {
      let value = 0, part;
      do {
        part = byte();
        value = value * 128 + (part & 127);
        if (!Number.isSafeInteger(value) || value > MAX_ROM) fail('Patch integer is too large.');
      } while (part & 128);
      return value;
    };
    if (byte() !== 0xd6 || byte() !== 0xc3 || byte() !== 0xc4 || byte() !== 0) fail('Not a supported xdelta patch.');
    const header = byte();
    if (header & ~4) fail('This release does not use secondary compression or custom code tables.');
    if (header & 4) { const length = integer(); at += length; }
    let total = 0, windows = 0;
    while (at < bytes.length) {
      const flag = byte();
      if ((flag & ~7) || (flag & 3) === 3 || !(flag & 4)) fail('Unsupported patch window flags.');
      let sourceLength = 0;
      if (flag & 3) {
        sourceLength = integer();
        const position = integer();
        if (position + sourceLength > (flag & 1 ? sourceSize : total)) fail('Patch source window is out of range.');
      }
      const deltaLength = integer();
      const deltaStart = at;
      const windowSize = integer();
      if (!windowSize || windowSize > 8 * 1024 * 1024 || total + windowSize > targetSize) fail('Patch output window is out of range.');
      if (byte() !== 0) fail('Compressed patch sections are not supported by this release.');
      const data = integer(), instructions = integer(), addresses = integer();
      at += 4; // Adler-32, checked by the decoder as well as the final SHA-256.
      const end = at + data + instructions + addresses;
      if (end !== deltaStart + deltaLength || end > bytes.length) fail('Patch section lengths do not match.');
      at = end;
      total += windowSize;
      windows++;
    }
    if (at !== bytes.length || total !== targetSize || !windows) fail('Patch output size does not match this release.');
    return windows;
  }

  function assemble(profile, files, patchBytes, read, progress = () => {}) {
    if (!profile || !Array.isArray(profile.inputs) || !profile.inputs.length || profile.inputs.length > 5 ||
        !Array.isArray(files) || files.length !== profile.inputs.length) fail('Select all inputs for one build method.');
    spec(profile.output);
    spec(profile.patch);
    if (!(patchBytes instanceof Uint8Array) || patchBytes.byteLength !== profile.patch.size ||
        root.sha256(patchBytes) !== profile.patch.sha256) fail('The release patch is damaged. Download a fresh copy of the patcher.');
    // Reject all size errors before spending time hashing any large file.
    profile.inputs.forEach((input, index) => {
      spec(input);
      if (!files[index] || files[index].size !== input.size) fail(`${input.label}: wrong file size. Choose the exact version listed under Input details.`);
    });
    profile.inputs.forEach((input, index) => {
      verifyFile(files[index], {size: input.size, sha256: input.sha256}, input.label, read,
        fraction => progress({stage: 'checking', input: index, fraction}));
      progress({stage: 'checked', input: index, fraction: 1});
    });
    const source = new CompositeSource(files, read);
    preflight(patchBytes, source.fileSize, profile.output.size);
    progress({stage: 'building', fraction: 0});
    const result = root.VCDIFF.fromFile(new root.BinFile(patchBytes.slice().buffer)).apply(source, true,
      fraction => progress({stage: 'building', fraction}));
    if (result.fileSize !== profile.output.size) fail('Finished ROM has the wrong size. No download was created.');
    const hash = root.sha256.create();
    for (let at = 0; at < result.fileSize; at += CHUNK) {
      hash.update(result._u8array.subarray(at, at + CHUNK));
      progress({stage: 'verifying', fraction: Math.min(1, (at + CHUNK) / result.fileSize)});
    }
    if (hash.hex() !== profile.output.sha256) fail('Finished ROM failed its checksum. No download was created.');
    return {bytes: result._u8array, sha256: hash.hex()};
  }

  function copy(source, target, windowStart, offset, header, address, size) {
    if (!Number.isSafeInteger(address) || address < 0 || address >= header.sourceLength + offset ||
        !Number.isSafeInteger(size) || size < 0 || offset + size > header.targetWindowLength) fail('Invalid patch copy instruction.');
    let dest = windowStart + offset;
    if (address < header.sourceLength) {
      const count = Math.min(size, header.sourceLength - address);
      const from = header.sourcePosition + address;
      if (header.indicator & 1) source.copyRange(target, dest, from, count);
      else {
        if (from + count > windowStart) fail('Patch references output that has not been built.');
        target.set(target.subarray(from, from + count), dest);
      }
      dest += count;
      address += count;
      size -= count;
    }
    const from = windowStart + address - header.sourceLength;
    while (size) {
      if (from < windowStart || from >= dest) fail('Patch references output that has not been built.');
      // Grow overlapping copies from bytes already written; copyWithin uses memmove semantics.
      const count = Math.min(size, dest - from);
      target.copyWithin(dest, from, from + count);
      dest += count;
      size -= count;
    }
  }

  root.SacredGoldCore = {CHUNK, hashFile, verifyFile, CompositeSource, preflight, assemble, copy};
})(globalThis);

// zlib Adler-32, with the same initial value as xdelta's window checksums.
function adler32(file, start, length) {
  let a = 1, b = 0;
  const bytes = file._u8array;
  for (let at = start; at < start + length;) {
    const end = Math.min(at + 5552, start + length);
    while (at < end) { a += bytes[at++]; b += a; }
    a %= 65521;
    b %= 65521;
  }
  return ((b << 16) | a) >>> 0;
}

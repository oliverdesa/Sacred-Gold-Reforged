/* Runs only inside a disposable worker; source Files are read-only browser snapshots. */
self.onmessage = function ({data}) {
  const started = performance.now();
  try {
    if (typeof FileReaderSync !== 'function') throw new Error('This browser does not support local file reading in a worker. Try a current desktop browser.');
    const reader = new FileReaderSync();
    const stats = {readCalls: 0, bytesRead: 0, maxReadBytes: 0};
    const read = (file, start, length) => {
      stats.readCalls++;
      stats.bytesRead += length;
      stats.maxReadBytes = Math.max(stats.maxReadBytes, length);
      return new Uint8Array(reader.readAsArrayBuffer(file.slice(start, start + length)));
    };
    const result = SacredGoldCore.assemble(data.profile, data.files, data.patch, read,
      progress => self.postMessage({type: 'progress', ...progress}));
    self.postMessage({type: 'complete', ...result, stats, elapsedMs: performance.now() - started},
                     [result.bytes.buffer]);
  } catch (error) {
    // No filenames, paths, ROM contents or input digests in diagnostics.
    self.postMessage({type: 'error', message: error.message || 'The browser could not finish this build.',
                      elapsedMs: performance.now() - started});
  }
};

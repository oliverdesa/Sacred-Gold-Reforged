/* Runs only inside a disposable worker; source Files are read-only browser snapshots. */
class TemporaryStorageError extends Error {}

async function buildWithTemporaryStorage(data, read, assemble, stats) {
  if (!navigator.storage?.getDirectory || !navigator.locks?.request) return {fallback: 'unsupported'};
  const name = data.temporaryName;
  let entered = false;
  try {
    return await navigator.locks.request(name, {ifAvailable: true}, async lock => {
      if (!lock) return {fallback: 'busy'};
      entered = true;
      let directory, file, handle;
      const offsets = new Map();
      let size = 0;
      for (const source of data.files) {
        offsets.set(source, size);
        size += source.size;
      }
      try {
        try {
          directory = await navigator.storage.getDirectory();
          try { await directory.removeEntry(name); }
          catch (error) { if (error.name !== 'NotFoundError') throw error; }
          const estimate = await navigator.storage.estimate?.();
          if (estimate?.quota - estimate?.usage < size) return {fallback: 'space'};
          file = await directory.getFileHandle(name, {create: true});
          handle = await file.createSyncAccessHandle();
        } catch {
          return {fallback: 'storage'};
        }

        self.postMessage({type: 'strategy', method: 'temporary'});
        let patching = false;
        const result = assemble((source, start, length) => {
          const at = offsets.get(source) + start;
          const bytes = patching ? new Uint8Array(length) : read(source, start, length);
          try {
            const count = patching ? handle.read(bytes, {at}) : handle.write(bytes, {at});
            if (count !== length) throw new TemporaryStorageError();
          } catch {
            throw new TemporaryStorageError();
          }
          if (patching) stats.temporaryReads++;
          return bytes;
        }, () => { patching = true; });
        return {result};
      } catch (error) {
        if (error instanceof TemporaryStorageError) return {fallback: 'storage'};
        throw error;
      } finally {
        try { handle?.close(); } catch {}
        if (file) {
          // The page also sweeps the file after stopping the worker.
          try { await directory.removeEntry(name); } catch {}
        }
      }
    });
  } catch (error) {
    if (entered) throw error;
    return {fallback: 'storage'};
  }
}

self.onmessage = async function ({data}) {
  const started = performance.now();
  try {
    if (typeof FileReaderSync !== 'function') throw new Error('This browser does not support local file reading in a worker. Try a current desktop browser.');
    const reader = new FileReaderSync();
    const stats = {readCalls: 0, bytesRead: 0, maxReadBytes: 0, temporaryReads: 0};
    let nextReadReport = started;
    const read = (file, start, length) => {
      const now = performance.now();
      if (now >= nextReadReport) {
        // Send before the read so the page has a checkpoint even if the read blocks.
        self.postMessage({type: 'read', input: data.profile.inputs[data.files.indexOf(file)].id,
                          offset: start, length, elapsedMs: now - started, stats});
        nextReadReport = now + 1000;
      }
      stats.readCalls++;
      stats.bytesRead += length;
      stats.maxReadBytes = Math.max(stats.maxReadBytes, length);
      return new Uint8Array(reader.readAsArrayBuffer(file.slice(start, start + length)));
    };
    const assemble = (source, startPatching) => SacredGoldCore.assemble(data.profile, data.files, data.patch, source, progress => {
      if (progress.stage === 'building') startPatching?.();
      self.postMessage({type: 'progress', ...progress});
    });
    let result;
    if (data.temporaryName) {
      const temporary = await buildWithTemporaryStorage(data, read, assemble, stats);
      result = temporary.result;
      if (temporary.fallback) self.postMessage({type: 'strategy', method: 'direct', fallback: temporary.fallback});
    }
    if (!result) result = assemble(read);
    self.postMessage({type: 'complete', ...result, stats, elapsedMs: performance.now() - started},
                     [result.bytes.buffer]);
  } catch (error) {
    // No filenames, paths, ROM contents or input digests in diagnostics.
    self.postMessage({type: 'error', message: error.message || 'The browser could not finish this build.',
                      elapsedMs: performance.now() - started});
  }
};

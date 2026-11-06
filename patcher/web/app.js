/* Sacred Gold by Drayano; engine integration based on Platinum Reforged / Anvil by smoldice. */
(function () {
  'use strict';
  const el = id => document.getElementById(id);
  const files = {clean: {}, prepared: {}};
  let mode = 'clean', worker = null, workerUrl = null, gameUrl = null, reportUrl = null, currentInput = null;
  let generation = 0, phase = 'starting';
  let buildStarted = 0, lastProgress = 0, lastRead = null, stallTimer = null;
  let readMethod = 'direct', fallback = null;
  const temporaryName = /Android/i.test(navigator.userAgent) ? 'sacred-gold-patcher-scratch-v1' : null;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let spritesPlaying = !reducedMotion.matches;
  const rows = new Map();
  const supported = typeof Worker === 'function' && typeof Blob === 'function' && typeof URL.createObjectURL === 'function';
  const size = bytes => `${(bytes / 1024 ** 2).toFixed(bytes >= 1024 ** 2 ? 1 : 2)} MiB`;
  const profile = () => SG_RELEASE.profiles[mode];

  async function sweepTemporaryStorage(wait = false) {
    if (!temporaryName || !navigator.storage?.getDirectory || !navigator.locks?.request) return;
    try {
      await navigator.locks.request(temporaryName, {ifAvailable: !wait}, async lock => {
        if (!lock) return;
        const directory = await navigator.storage.getDirectory();
        for (let attempt = 0; attempt < 4; attempt++) {
          try { await directory.removeEntry(temporaryName); return; }
          catch (error) { if (error.name === 'NotFoundError') return; }
          // A terminated worker's file handle can take a moment to close.
          if (attempt < 3) await new Promise(resolve => setTimeout(resolve, 150));
        }
      });
    } catch {}
  }

  function clearDownloads() {
    if (gameUrl) URL.revokeObjectURL(gameUrl);
    if (reportUrl) URL.revokeObjectURL(reportUrl);
    gameUrl = reportUrl = null;
    ['download', 'report'].forEach(id => { el(id).hidden = true; el(id).removeAttribute('href'); });
  }

  function stopWorker() {
    generation++;
    clearTimeout(stallTimer);
    if (worker) {
      worker.terminate();
      sweepTemporaryStorage(true);
    }
    if (workerUrl) URL.revokeObjectURL(workerUrl);
    worker = workerUrl = null;
    currentInput = null;
    el('cancel').hidden = true;
    el('methods').disabled = false;
    document.querySelectorAll('#files input').forEach(input => { input.disabled = false; });
    updateButton();
  }

  function status(message, error = false) {
    if (el('status').textContent !== message) el('status').textContent = message;
    el('result').classList.toggle('error', error);
  }

  function updateButton() {
    el('build').disabled = !supported || !!worker ||
      !profile().inputs.every(input => files[mode][input.id]?.size === input.size);
    updateSprites();
  }

  function updateSprites() {
    const playing = spritesPlaying && !worker;
    document.querySelectorAll('.legendary').forEach(image => {
      const next = playing ? image.dataset.animated : image.dataset.still;
      if (image.getAttribute('src') !== next) image.src = next;
    });
    el('sprite-motion').textContent = worker ? 'Sprites paused during build' : playing ? 'Pause sprites' : 'Play sprites';
    el('sprite-motion').disabled = !!worker;
    el('sprite-motion').setAttribute('aria-pressed', String(playing));
  }

  function render() {
    clearDownloads();
    files.clean = {}; files.prepared = {};
    rows.clear();
    el('files').replaceChildren();
    el('input-details').replaceChildren();
    el('clean-guide').hidden = mode !== 'clean';
    el('prepared-guide').hidden = mode !== 'prepared';
    el('method-help').textContent = mode === 'clean'
      ? 'Start with your unmodified HeartGold, Platinum and Black 2 games. Add the two patch files linked below; this page handles the build for you.'
      : 'A shortcut for existing builds only: Sacred Gold Complete 1.05 + Platinum Reforged 0.1.0-alpha. Newer Reforged versions will not pass verification.';
    profile().inputs.forEach((input, index) => {
      if (mode === 'clean' && (index === 0 || input.id === 'sacred_gold_patch')) {
        const heading = document.createElement('h3');
        heading.textContent = index === 0 ? '1. Your three games' : '2. The two patch files';
        el('files').append(heading);
      }
      const row = document.createElement('div'); row.className = 'file-row';
      const label = document.createElement('label'); label.htmlFor = `file-${input.id}`; label.textContent = input.label;
      if (input.id === 'bundle') label.textContent = 'Anvil engine file · reforged.bundle';
      if (input.id === 'reforged') label.textContent = 'Platinum Reforged · 0.1.0-alpha';
      const meta = document.createElement('span'); meta.className = 'file-meta'; meta.textContent = `${size(input.size)} · exact revision`;
      label.append(meta);
      const state = document.createElement('div'); state.className = 'file-state';
      const picker = document.createElement('input'); picker.type = 'file'; picker.id = label.htmlFor;
      picker.accept = input.id === 'sacred_gold_patch' ? '.xdelta' : input.id === 'bundle' ? '.bundle' : '.nds';
      picker.addEventListener('change', () => {
        clearDownloads();
        const file = picker.files[0];
        if (file) files[mode][input.id] = file; else delete files[mode][input.id];
        state.className = 'file-state';
        if (file) {
          state.textContent = file.name;
          const note = document.createElement('span');
          note.textContent = file.size === input.size ? 'Ready to check' : `Wrong size: expected ${size(input.size)}`;
          state.append(note);
          if (file.size !== input.size) state.classList.add('error');
        } else state.textContent = '';
        el('progress').hidden = true;
        status('Choose all files, then build. Originals are read-only.');
        updateButton();
      });
      row.append(label, state, picker); el('files').append(row); rows.set(index, state);
      const detail = document.createElement('p'); detail.textContent = `${input.label}: ${input.size} bytes`;
      const hash = document.createElement('code'); hash.textContent = `SHA-256 ${input.sha256}`;
      detail.append(hash); el('input-details').append(detail);
    });
    status(supported ? 'Choose your files to begin.' : 'This browser cannot run the local patcher. Try a current desktop browser.', !supported);
    el('progress').hidden = true;
    updateButton();
  }

  function diagnostic(result, elapsedMs, stats) {
    // Keep file names, filesystem paths, source contents and input hashes out of reports.
    const report = {patcherVersion: 3, gameVersion: SG_RELEASE.version, mode, result, phase, readMethod, fallback,
                    input: currentInput === null ? null : profile().inputs[currentInput].id,
                    elapsedMs: Math.round(elapsedMs), expectedOutputSha256: profile().output.sha256,
                    progressPercent: Number((el('progress').value * 100).toFixed(2)),
                    secondsSinceProgress: Math.round((performance.now() - lastProgress) / 1000),
                    lastRead,
                    browser: navigator.userAgent, ...(stats ? {io: stats} : {})};
    if (reportUrl) URL.revokeObjectURL(reportUrl);
    reportUrl = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], {type: 'application/json'}));
    el('report').href = reportUrl; el('report').download = `SacredGold-${SG_RELEASE.version}-diagnostic.json`;
    el('report').hidden = false;
  }

  function watchProgress() {
    lastProgress = performance.now();
    clearTimeout(stallTimer);
    stallTimer = setTimeout(() => {
      const percent = Math.round(el('progress').value * 100);
      status(`Build is taking longer than expected at ${percent}%. Keep this tab open or save a diagnostic report before retrying.`);
      diagnostic('running', performance.now() - buildStarted);
    }, 20_000);
  }

  function failed(message, elapsedMs = performance.now() - buildStarted) {
    if (currentInput !== null) rows.get(currentInput)?.classList.add('error');
    status(message + '\nNo game download was created. Your source files have not been changed.', true);
    diagnostic('failed', elapsedMs);
    stopWorker();
  }

  el('build').addEventListener('click', () => {
    clearDownloads();
    const selected = profile();
    const sourceFiles = selected.inputs.map(input => files[mode][input.id]);
    if (!sourceFiles.every((file, index) => file?.size === selected.inputs[index].size)) return;
    const job = ++generation;
    phase = 'starting';
    readMethod = 'direct';
    fallback = null;
    buildStarted = performance.now();
    lastRead = null;
    el('progress').value = 0;
    watchProgress();
    document.querySelectorAll('video').forEach(video => video.pause());
    try {
      workerUrl = URL.createObjectURL(new Blob([SG_WORKER], {type: 'text/javascript'}));
      worker = new Worker(workerUrl);
      worker.onmessage = ({data}) => {
        if (job !== generation) return;
        if (data.type === 'strategy') {
          readMethod = data.method;
          fallback = data.fallback ?? null;
          if (fallback) status('Using direct file reads. This can take several minutes on Android.');
        } else if (data.type === 'read') {
          const {input, offset, length, elapsedMs, stats} = data;
          lastRead = {input, offset, length, elapsedMs: Math.round(elapsedMs), completedReads: stats.readCalls};
        } else if (data.type === 'progress') {
          phase = data.stage;
          let fraction;
          if (data.stage === 'checking' || data.stage === 'checked') {
            currentInput = data.input;
            const action = readMethod === 'temporary' ? 'Checking and preparing' : 'Checking';
            status(`${action} ${selected.inputs[data.input].label}… ${Math.floor(data.fraction * 100)}%`);
            fraction = .7 * (data.input + data.fraction) / selected.inputs.length;
            if (data.stage === 'checked') {
              const row = rows.get(data.input); row.classList.add('checked');
              const note = document.createElement('span'); note.textContent = 'Checksum verified'; row.replaceChildren(note);
            }
          } else {
            currentInput = null;
            fraction = (data.stage === 'building' ? .7 : .9) + data.fraction * (data.stage === 'building' ? .2 : .1);
            if (data.stage === 'building') {
              const note = fallback ? ' Direct file reads can take several minutes.' : '';
              status(`Building your game… ${Math.round(fraction * 100)}%.${note}`);
            } else status('Verifying the finished game…');
          }
          el('progress').value = fraction;
          watchProgress();
        } else if (data.type === 'complete') {
          phase = 'complete';
          try { gameUrl = URL.createObjectURL(new Blob([data.bytes], {type: 'application/octet-stream'})); }
          catch { failed('The browser could not prepare the download. Close unused tabs and try again.', data.elapsedMs); return; }
          el('download').href = gameUrl; el('download').download = `SacredGold-Reforged-${SG_RELEASE.version}.nds`;
          el('download').hidden = false;
          el('progress').value = 1;
          diagnostic('verified', data.elapsedMs, data.stats);
          status(`Your game is ready. Output checksum verified.\nBuilt in ${(data.elapsedMs / 1000).toFixed(1)} seconds. Save the new ROM below.`);
          stopWorker();
        } else if (data.type === 'error') failed(data.message, data.elapsedMs);
      };
      worker.onerror = event => { if (job !== generation) return; event.preventDefault(); failed('The browser could not finish this build. Close unused tabs and try again, or try another desktop browser.'); };
      worker.onmessageerror = () => { if (job === generation) failed('The browser could not pass the selected files to the patcher. Select them again.'); };
      el('methods').disabled = true;
      document.querySelectorAll('#files input').forEach(input => { input.disabled = true; });
      el('cancel').hidden = false; el('progress').hidden = false;
      rows.forEach(row => row.classList.remove('error', 'checked'));
      status('Checking source files…'); updateButton();
      diagnostic('running', 0);
      const {data, ...metadata} = selected;
      const patch = Uint8Array.from(atob(data), char => char.charCodeAt(0));
      worker.postMessage({profile: metadata, files: sourceFiles, patch, temporaryName}, [patch.buffer]);
    } catch (error) { failed(error.message || 'This browser could not start the patcher.'); }
  });
  el('report').addEventListener('click', () => {
    if (worker) diagnostic('running', performance.now() - buildStarted);
  });
  el('cancel').addEventListener('click', () => {
    diagnostic('cancelled', performance.now() - buildStarted);
    stopWorker(); el('progress').hidden = true;
    status('Build cancelled. Your source files have not been changed.');
  });
  el('sprite-motion').addEventListener('click', () => { spritesPlaying = !spritesPlaying; updateSprites(); });
  reducedMotion.addEventListener('change', event => { if (event.matches) spritesPlaying = false; updateSprites(); });
  document.querySelectorAll('input[name="mode"]').forEach(input => input.addEventListener('change', () => {
    if (worker) return; mode = input.value; render();
  }));
  window.addEventListener('pagehide', () => { if (worker) stopWorker(); });
  window.addEventListener('pageshow', event => { if (event.persisted) { stopWorker(); render(); sweepTemporaryStorage(); } });
  el('version').textContent = `${SG_RELEASE.version.toUpperCase()} · TEST BUILD`;
  render();
  sweepTemporaryStorage();
})();

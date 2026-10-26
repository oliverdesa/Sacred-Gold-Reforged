/* Sacred Gold by Drayano; engine integration based on Platinum Reforged / Anvil by smoldice. */
(function () {
  'use strict';
  const el = id => document.getElementById(id);
  const files = {clean: {}, prepared: {}};
  let mode = 'clean', worker = null, workerUrl = null, gameUrl = null, reportUrl = null, currentInput = null;
  let generation = 0, phase = 'starting';
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let spritesPlaying = !reducedMotion.matches;
  const rows = new Map();
  const supported = typeof Worker === 'function' && typeof Blob === 'function' && typeof URL.createObjectURL === 'function';
  const size = bytes => `${(bytes / 1024 ** 2).toFixed(bytes >= 1024 ** 2 ? 1 : 2)} MiB`;
  const profile = () => SG_RELEASE.profiles[mode];

  function clearDownloads() {
    if (gameUrl) URL.revokeObjectURL(gameUrl);
    if (reportUrl) URL.revokeObjectURL(reportUrl);
    gameUrl = reportUrl = null;
    ['download', 'report'].forEach(id => { el(id).hidden = true; el(id).removeAttribute('href'); });
  }

  function stopWorker() {
    generation++;
    if (worker) worker.terminate();
    if (workerUrl) URL.revokeObjectURL(workerUrl);
    worker = workerUrl = null;
    currentInput = null;
    el('cancel').hidden = true;
    el('methods').disabled = false;
    document.querySelectorAll('#files input').forEach(input => { input.disabled = false; });
    updateButton();
  }

  function status(message, error = false) {
    el('status').textContent = message;
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
    const report = {patcherVersion: 1, gameVersion: SG_RELEASE.version, mode, result, phase,
                    input: currentInput === null ? null : profile().inputs[currentInput].id,
                    elapsedMs: Math.round(elapsedMs || 0), expectedOutputSha256: profile().output.sha256,
                    browser: navigator.userAgent, ...(stats ? {io: stats} : {})};
    reportUrl = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], {type: 'application/json'}));
    el('report').href = reportUrl; el('report').download = `SacredGold-${SG_RELEASE.version}-diagnostic.json`;
    el('report').hidden = false;
  }

  function failed(message, elapsedMs = 0) {
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
    document.querySelectorAll('video').forEach(video => video.pause());
    try {
      workerUrl = URL.createObjectURL(new Blob([SG_WORKER], {type: 'text/javascript'}));
      worker = new Worker(workerUrl);
      worker.onmessage = ({data}) => {
        if (job !== generation) return;
        if (data.type === 'progress') {
          phase = data.stage;
          let fraction;
          if (data.stage === 'checking' || data.stage === 'checked') {
            currentInput = data.input;
            status(`Checking ${selected.inputs[data.input].label}… ${Math.floor(data.fraction * 100)}%`);
            fraction = .7 * (data.input + data.fraction) / selected.inputs.length;
            if (data.stage === 'checked') {
              const row = rows.get(data.input); row.classList.add('checked');
              const note = document.createElement('span'); note.textContent = 'Checksum verified'; row.replaceChildren(note);
            }
          } else {
            currentInput = null;
            status(data.stage === 'building' ? 'Building your game…' : 'Verifying the finished game…');
            fraction = (data.stage === 'building' ? .7 : .9) + data.fraction * (data.stage === 'building' ? .2 : .1);
          }
          el('progress').value = fraction;
        } else if (data.type === 'complete') {
          phase = 'complete';
          gameUrl = URL.createObjectURL(new Blob([data.bytes], {type: 'application/octet-stream'}));
          el('download').href = gameUrl; el('download').download = `SacredGold-Reforged-${SG_RELEASE.version}.nds`;
          el('download').hidden = false;
          diagnostic('verified', data.elapsedMs, data.stats);
          status(`Your game is ready. Output checksum verified.\nBuilt in ${(data.elapsedMs / 1000).toFixed(1)} seconds. Save the new ROM below.`);
          el('progress').value = 1;
          stopWorker();
        } else if (data.type === 'error') failed(data.message, data.elapsedMs);
      };
      worker.onerror = event => { if (job !== generation) return; event.preventDefault(); failed('The browser could not finish this build. Close unused tabs and try again, or try another desktop browser.'); };
      worker.onmessageerror = () => { if (job === generation) failed('The browser could not pass the selected files to the patcher. Select them again.'); };
      el('methods').disabled = true;
      document.querySelectorAll('#files input').forEach(input => { input.disabled = true; });
      el('cancel').hidden = false; el('progress').hidden = false; el('progress').value = 0;
      rows.forEach(row => row.classList.remove('error', 'checked'));
      status('Checking source files…'); updateButton();
      const {data, ...metadata} = selected;
      const patch = Uint8Array.from(atob(data), char => char.charCodeAt(0));
      worker.postMessage({profile: metadata, files: sourceFiles, patch}, [patch.buffer]);
    } catch (error) { failed(error.message || 'This browser could not start the patcher.'); }
  });
  el('cancel').addEventListener('click', () => {
    stopWorker(); clearDownloads(); el('progress').hidden = true;
    status('Build cancelled. Your source files have not been changed.');
  });
  el('sprite-motion').addEventListener('click', () => { spritesPlaying = !spritesPlaying; updateSprites(); });
  reducedMotion.addEventListener('change', event => { if (event.matches) spritesPlaying = false; updateSprites(); });
  document.querySelectorAll('input[name="mode"]').forEach(input => input.addEventListener('change', () => {
    if (worker) return; mode = input.value; render();
  }));
  window.addEventListener('pagehide', () => { if (worker) stopWorker(); });
  window.addEventListener('pageshow', event => { if (event.persisted) { stopWorker(); render(); } });
  el('version').textContent = `${SG_RELEASE.version.toUpperCase()} · TEST BUILD`;
  render();
})();

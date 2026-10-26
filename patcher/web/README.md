# Sacred Gold Reforged — browser patcher

Sacred Gold by **Drayano**; Gen V engine integration based on **Platinum Reforged
/ Anvil by smoldice**. The local browser decoder is based on **Marc Robledo's
RomPatcher.js**, with checksums from **Chen, Yi-Cyuan's js-sha256**. See CREDITS.txt
in the site package, or CREDITS.md in the source directory, for full attribution.

This is a browser installer for the existing Alpha 4s testing ROM. It does not
change game balance, repair additional gameplay bugs, or open the Frontier early.

## Use the patcher

Open index.html in a current desktop browser, locally or from the hosted site.
No installation, account, Python, native xdelta executable or Anvil source
checkout is needed. The same page works offline once loaded.

Choose one starting method, select the required local files, then click Build.
The patcher checks every input, builds in a disposable worker, verifies the
complete output and offers a new .nds download. It never opens a source file
for writing. It has no upload endpoint, analytics, cookies or external runtime
dependency. The page's Content Security Policy forbids script network connections.
Local paths cannot be pasted into a web page: browser file pickers grant access
only to the files you select.

### Clean ROMs (recommended)

Select:

1. Pokemon HeartGold, USA revision 0, 134217728 bytes.
2. Pokemon Platinum, USA revision 0, 134217728 bytes.
3. Pokemon Black Version 2, USA/Europe revision 0, 536870912 bytes.
4. Drayano's modern SacredGold105.xdelta, Complete 1.05, 15023442 bytes.
5. smoldice's original Anvil alpha reforged.bundle, 630876 bytes.

The release.json file and the page's Input details section give the exact SHA-256
checksums. Different revisions, trimmed dumps, optional patches, Storm Silver,
Classic or Fairy addons are not accepted by this release. The original games
and upstream patch files are not supplied in this package.

Official sources:

- Drayano / Sacred Gold: https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/
- Drayano's HGSS downloads: https://drive.google.com/drive/folders/0B-zmEVN0Mas6VlhJNHc0YWx3UUk?resourcekey=0-RYApzpdEIcGIkiTfKxyKqw
- smoldice / original Anvil bundle: https://github.com/smoldice/platinum-reforged-anvil/releases/tag/v1.0.0-alpha

The direct browser delta references those five source files. It gives the same
result as the longer Python/Anvil assembly route without executing Anvil on the
player's device. Do not substitute the latest Reforged release.

### Prepared ROMs

Alternatively select Sacred Gold Complete 1.05 and the original Platinum
Reforged Anvil alpha ROM. The exact donor hashes are in release.json. This mode
does not take the current Sacred Gold Reforged playthrough ROM or a save.

No Renegade Platinum, Following Renegade or Redux input is required in either
method. This package only targets Sacred Gold.

## Memory, progress and cancellation

File reads are limited to 4 MiB chunks; the browser does not concatenate all
three game dumps into an 800 MiB array. The 256 MiB output and the browser's
download buffering still require free memory. This is intended for desktop
browsers; mobile/low-memory support must not be assumed without testing.

The HeartGold-inspired layout features a 24-second crop of the owner's Chuck
fifth-badge recording. It loads on demand, has no audio, and pauses when a build
starts. Ho-Oh and Lugia use the original Gen V animations from the Pokémon
Showdown sprite archive, with Nintendo / Game Freak attribution in CREDITS.txt.
Use “Pause sprites” to stop them; reduced-motion preferences select static images
by default. Sprites also pause while patching.

Checksums and patching run off the page thread, so the controls stay responsive.
Cancel terminates the worker and creates no output. Changing inputs or build
method removes any previous output link to avoid downloading a stale build.
Input selection is kept in memory, not saved in browser storage. Switching build
method clears the selections. Returning from a browser history cache resets the
form so stale file selections and old worker messages cannot be reused.

## Result and reports

The output is 268435456 bytes, SHA-256:
627ec717edd9dc40d1bdf8088c7470de435c6f63fc933e43d403396220b74917

Back up your ordinary in-game save before changing ROM versions. Avoid carrying
emulator savestates across versions. The patcher does not access your emulator
or any saves. Read KNOWN_ISSUES.txt before playing.

The optional diagnostic download is created locally. It records game/patcher
version, starting method, result, elapsed time, browser and I/O counts, but no
ROM contents, selected filenames or filesystem paths. It is never sent anywhere.

## Hosting

The site is static. Serve this directory over HTTPS or use it as a GitHub Pages
artifact; no backend, database, build server or upload service is needed.
index.html includes its small patch-engine code and encoded deltas so it also
opens directly from disk. Relative document links work under a repository
subpath. .nojekyll keeps Pages from rewriting the package.

The source export includes a manual Pages deployment workflow and synthetic
tests. Keep source ROMs, saves, official upstream patches/bundles and private
test fixtures out of any repository. Only approved project release deltas belong
in release assets. Do not publish the entire game-development workspace.

This is a local prototype. Review upstream runtime/art redistribution terms
before publishing a game-bearing site or release. CREDITS.txt preserves the
distinction between open-source tools and the original games/other authors' work.

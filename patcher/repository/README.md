# Sacred Gold Reforged patcher

Sacred Gold by **Drayano**. Gen V engine integration based on **Platinum
Reforged / Anvil by smoldice**. Browser patching uses **RomPatcher.js by Marc
Robledo** and **js-sha256 by Chen, Yi-Cyuan**. Full acknowledgements and licence
boundaries are in [CREDITS](patcher/web/CREDITS.md) and THIRD_PARTY_NOTICES.md.

This source repository builds a static, offline-capable Sacred Gold browser
patcher. Selected source games stay on the player's device. It creates a new
verified ROM without changing the inputs or accessing emulator saves.

The website uses a HeartGold-inspired palette and owner-provided extended gameplay
footage. Original screen recordings, game dumps, saves, Anvil bundles and
official hack patches are excluded from this repository. Curated preview media
is separate from the patch engine.

## Development

Requires Python 3.11+ and Node 22+. Native installer checks additionally use
xdelta3. There are no npm dependencies or frontend framework.

```sh
python3 -m unittest discover -s tests -p test_sacred_gold_patcher.py -v
node --test tests/test_web_patcher.mjs
python3 -m unittest discover -s tests -p test_web_patcher_package.py -v
```

The checked-in fixtures contain synthetic byte patterns only. Native xdelta
generated and independently round-tripped them. No ROMs are needed by CI.
The browser engine reads 4 MiB chunks with a cache capped at 16 MiB, then verifies
the entire 256 MiB output. Cancellation disposes the worker; no upload API exists.

## Build the site

Obtain the two project deltas from an approved release, then run:

```sh
python3 tools/package_sacred_gold_web.py --clean-patch release-inputs/SacredGold-alpha5a-clean.xdelta --prepared-patch release-inputs/SacredGold-Reforged-alpha5a.xdelta --out dist
```

Both deltas must match the checksums pinned in the source. The generated dist/
directory contains the self-contained page, curated media, instructions,
testing notes, metadata and licences. Its ZIP is a deployment/download artifact,
not a full game ROM. Player instructions are in patcher/web/README.md.

## GitHub Pages

1. Put this source in its own repository, rather than uploading the game-development workspace.
2. Run the included test workflow.
3. After reviewing upstream game/runtime/art terms, attach the two approved project
   deltas to a GitHub release using the exact asset filenames above.
4. In Settings → Pages, choose GitHub Actions.
5. Run the manual “Deploy browser patcher” workflow and supply that release tag.

The workflow downloads only those two project deltas, verifies their pins, builds
the site from this source and deploys the static directory. It never asks for
source ROMs, official upstream patches, saves or a server. It is deliberately a
manual deployment; committing source does not publish the game-bearing site.

The workflow has been prepared locally; a live GitHub Actions/Pages run is not
claimed until it has actually run in the destination repository. Review upstream
terms before public release. Open-source tool licences do not cover the original
games or all of Anvil's runtime and art.

# Sacred Gold Reforged — creators and licences

Sacred Gold is by **Drayano**. The Gen V battle engine integration is based on
**Platinum Reforged / Anvil by smoldice**. This compatibility/testing project is
independent of both authors and is not presented as their official release.

## Games and engine integration

- **Drayano** — Sacred Gold & Storm Silver Complete 1.05, its campaign changes,
  Pokémon/trainer data, and original documentation. The original documentation
  contains additional contributor credits, which remain applicable.
  https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/
- **smoldice** — Platinum Reforged and its Anvil builder/converters, the upstream
  Gen V integration used as the engine donor for this project.
  https://github.com/smoldice/platinum-reforged-anvil
- **Nintendo, Game Freak, Creatures and The Pokémon Company** — original games,
  characters, code, music, models and artwork. Their material is not licensed
  under the tool licences listed below. Players supply their own source games.

## Gameplay preview and legendary sprites

The extended gameplay recording was captured by the project playtester and used
at their request. The website preserves the full 4:3 game picture and gameplay
audio, with recording metadata removed; the original recording is preserved.
Preview encoding uses FFmpeg (https://ffmpeg.org/), a development tool which is
not included in the website runtime or download.

The animated Ho-Oh and Lugia images are the Gen V sprites supplied by the
Pokémon Showdown / Smogon sprite repository:
https://play.pokemonshowdown.com/sprites/gen5ani/hooh.gif
https://play.pokemonshowdown.com/sprites/gen5ani/lugia.gif
https://github.com/smogon/sprites

The original sprites remain property of Nintendo / Game Freak / The Pokémon
Company, as the sprite repository states. They are not covered by the MIT tool
licences. Static first-frame alternatives support reduced motion and pausing.
No Showdown client or simulator code is included in this patcher.

## Browser patching tools

- **Marc Robledo** — RomPatcher.js VCDIFF decoder and BinFile.js. MIT licence.
  The upstream source includes additional credit to **Victor Alexiev** for the
  MIT-licensed MiscUtil VCDIFF address-cache/default-table port. Those inline
  attributions are retained.
  https://github.com/marcrobledo/RomPatcher.js
- **Joshua MacDonald** — xdelta3, used to generate and independently verify the
  release deltas. The RomPatcher.js secondary decoder also credits his xdelta
  code. Apache License 2.0; the full notice is included even though our release
  deltas use no secondary compression.
  https://github.com/jmacd/xdelta
- **Chen, Yi-Cyuan (emn178)** — js-sha256 0.11.1, used for local incremental
  checksums. MIT licence.
  https://github.com/emn178/js-sha256

This project adapts the browser decoder to read source ranges in chunks, check
bounds and report progress. The exact vendored originals, hashes and documented
adaptations are in the source repository. The patcher itself makes no network
connections; only the hosting page and its static documents need serving.

## QoL implementation references and game research

- **Kalaay / KalaayPT**, **Yako**, and the other **G4Patcher contributors** —
  references for QoL tools including IV viewing, shortcut/menu tools and candies.
  Source-specific acknowledgements also include Mixone, Mikelan98, Nomura and the
  pokeplatinum team where credited by those upstream references.
  https://github.com/KalaayPT/G4Patcher
- **pret/pokeheartgold**, **pret/pokeplatinum**, and **fuddlesworth/pokebw2** and
  their contributors — native API, file-format, callback and engine research.
  https://github.com/pret/pokeheartgold
  https://github.com/pret/pokeplatinum
  https://github.com/fuddlesworth/pokebw2

No Redux or Following Renegade patch is required by this Sacred Gold patcher.
Their separate contributions to the Renegade Platinum project are not claimed
as features included here.

## Scope of permission

Included tool licence texts:

- licenses/RomPatcher-LICENSE.txt
- licenses/SHA256-LICENSE.txt
- licenses/Apache-2.0.txt
- licenses/G4Patcher-LICENSE.txt

Anvil's MIT tool licence explicitly excludes its runtime bundle, name/art and
custom sprite designs. Supplying an upstream input locally does not grant
permission to redistribute its other contents. Original game material retains
its own rights. Credits do not substitute for permission. Public redistribution
of this testing build has not been cleared by these notes.

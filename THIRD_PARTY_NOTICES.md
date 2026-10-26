# QoL implementation references

## Platinum Reforged and Anvil

**Platinum Reforged and its Anvil builder are by smoldice.** Their Gen V engine
integration and converters provide the pinned donor used by this project's
Sacred Gold compatibility work. This project is independent of smoldice and
Drayano, the creator of Sacred Gold. See
[smoldice/platinum-reforged-anvil](https://github.com/smoldice/platinum-reforged-anvil).
Anvil's MIT tool licence explicitly excludes its game/runtime bundle, name/art
and custom sprite designs; no blanket licence for those materials is asserted.

The browser installer uses **RomPatcher.js / BinFile.js by Marc Robledo**,
**js-sha256 by Chen, Yi-Cyuan**, and release deltas generated with **xdelta3 by
Joshua MacDonald**. Original inline notices, Victor Alexiev's cited VCDIFF
contribution, pinned provenance and full tool licences are retained under
`patcher/web/vendor/`; player-facing acknowledgements are in
[browser credits](patcher/web/CREDITS.md).

## Sacred Gold and HeartGold engine research

Sacred Gold Complete 1.05 is Drayano's ROM hack. The official patch and its
Pokémon, item, evolution and event documentation are used as the local campaign
reference. See [release thread](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/)
and [download hashes](docs/sacred-gold-provenance.json). Original documentation
contains the author's additional contributor credits. The optional community
Fairy addon credits Mikelan98 and MeroMero; it is not included in this build.

The locally cloned pret HeartGold and Black 2 research sources were used to
identify native APIs, application layouts, callbacks and evolution behavior.
The Gen V engine and assets come from the already pinned Platinum Reforged
donor. All downloaded patches, ROMs and extracted assets remain local; no
open-source license for these proprietary materials is asserted. Conversion,
relocation, compatibility code and checks are implemented in this workspace.

## Portable QoL references

The overworld shortcut, EXP edging and status tools were adapted using
[KalaayPT/G4Patcher](https://github.com/KalaayPT/G4Patcher) as an implementation
reference. Credits: Kalaay (shortcut and EXP edging), Yako (overworld status
setter), and individual G4Patcher contributors. Reforged-specific allocations,
guards, menus and builds are implemented in this workspace. The
[pret/pokeplatinum](https://github.com/pret/pokeplatinum) decompilation was used
to identify native APIs and field-script semantics; proprietary ROM resources
remain local and are not included in the project source.

The HeartGold adaptation also uses [pret/pokeheartgold](https://github.com/pret/pokeheartgold)
for native command widths, input structures, Move Reminder flags, storage tasks
and save APIs. `heartgold_script_commands.json` records its command widths with
variable-width corrections checked against the native handlers. Sacred Gold QoL
1.8.6 by Kalaay was downloaded as a local research reference; its balance edits
and proprietary resources are not redistributed or merged wholesale.

Sacred Gold Alpha 3's R-button IV viewer uses Kalaay's `EVIV_HG_SS.asm` as a
reference for the native summary input/refresh hooks. Its two-mode stat loop,
per-summary state, reclaimed EV-add space, and EV accessor/save changes are
implemented here using the native Pokémon layouts documented by pokeheartgold.

Renegade Reforged Alpha 7c uses Kalaay's `EVIV_PLAT.asm` as a reference for
Platinum's summary input/refresh hooks. It adapts the same two-mode, per-summary
viewer and EV accessor/save policy used for Sacred Gold, with layouts checked
against pret/pokeplatinum. The G4Patcher MIT notice below applies.

Renegade Reforged Alpha 7d researches Drayano's optional `SpeedUpPatch.xdelta`
(including Kaphotics' instant-text work) on a separate local Renegade reference.
The toggleable native frame reset and instant text/gauges adaptation is implemented
here using pret/pokeplatinum and the local pokebw2 decompilation. The original
binary patch is not merged wholesale; its original native gauge routines differ
from Reforged's imported Gen V implementation.

Sacred Gold Alpha 3b adapts Yako's `chain_candy_HG_SS.asm` from G4Patcher.
The original credits Kalaay, Mixone, the pokeplatinum team, Mikelan98 and Nomura.
This implementation uses a resident helper in the redundant no-EV summing code
instead of the original expanded ARM9/synthetic overlay allocation.

Sacred Gold Alpha 3d uses the two branch edits documented in G4Patcher's
`infinite_TMs_HG_SS.asm`. That reference credits Drayano, Mikelan98, NextWorld
and BagBoy. Native teaching paths and the bag layout were checked against
pret/pokeheartgold; this build reinstalls the compressed bag overlay safely.

Sacred Gold Alpha 3e adapts the native edits in G4Patcher's
`forgettable_HMs_HG_SS.asm`, which credits AdAstra's research. Gen V integration
additionally changes the two source-identified `BPlistMain_IsHMMove` UI guards
using the local pokebw2 reference and the audited engine provenance.

Platinum Alpha 7f adapts Yako's `chain_candy_PLAT.asm` from G4Patcher for the
current Reforged addresses. Credits also include Kalaay, Mixone, pret/pokeplatinum,
Mikelan98 and Nomura as identified in that routine. Native tutor and scrolling
menu command behavior was checked against pret/pokeplatinum; the supplied
Kalaay QoL README provides the Maylene unlock rule. The MIT notice below applies.

## G4Patcher license

MIT License

Copyright (c) Individual contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Following Pokémon

Following Pokémon code, graphics and integration resources are extracted locally
from the Following Renegade patch by Chensquared, based on Following Platinum by
Mikelan98 and AdAstra/LD3005, and Renegade Platinum by Drayano.
[Project page](https://www.pokehacking.com/fangames/following-renegade/).
[Download provenance](docs/following-provenance.json).

The downloaded patches, donor ROM and extracted runtime/assets remain ignored
local files. This project does not assert an open-source license for those
materials. The Reforged-specific loader and address/table merge tooling are
implemented in this workspace.

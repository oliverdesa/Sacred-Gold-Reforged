# Sacred Gold Reforged Alpha 4x — testing status

Sacred Gold by **Drayano**; Gen V engine integration based on **Platinum Reforged
/ Anvil by smoldice**. This independent testing build is not an official release
from either creator. Combined by [Oliver De Sa](https://github.com/oliverdesa).
See the package credits for all contributors and licences.

This is a work-in-progress game build. The installer reproduces Alpha 4x.

- Alpha 4x includes guards for the null allocation-debug filename and absent
  graphics-heap queries found during melonDS testing. Tests cover heap setup,
  live allocation and deletion; see the recorded gameplay results for runtime scope.
- Alpha 4x removes a donor-only low-HP music option query that crashed when
  a Pokémon reached red HP. A fixed doubles replay passed that trigger, berry
  healing, fainting/replacement, move learning, winnings and field return.
- Optional Callie/Kassandra double and single triggers passed; their runtime AI
  flags are 0x81 in doubles and 0x01 in singles. An empty foe slot can still look
  selectable in the target menu; use the named, occupied target.
- Valid party eggs become ready on one walking step and enter the native hatch
  sequence on the next eligible step. Ordinary friendship and breeding generation
  are unchanged. Two eggs completed hatch animations and survived save/reload. Other event/gift
  paths still need broader playtesting.
- Factory's Gen V command menu currently omits Bag. The reported expectation is
  a visible Bag button with an items-disabled message. This UI issue is not fixed.

- Normal campaign access to the Battle Frontier remains blocked until Jasmine.
  No debug save, early-access flag, free rental party or personal save is included.
- Factory single-battle Gen V rendering and an initial themed-scene turn were
  exercised. Full streak handoffs, Factory doubles and Thorton need more testing.
- Alpha 4r's graphics-memory fix addresses the diagnosed Thunder-in-rain failure.
  The exact reported move/weather sequence still needs gameplay retesting.
- Alpha 4s assigns scenes to all 16 Gym Leaders, the Elite Four, Champion and
  their mapped rooms. Focused code checks passed; live verification of all those
  battles is pending.
- Earlier callbacks, capture handoffs and field/menu fixes have focused checks
  and some user testing. They do not constitute a complete campaign regression.
- The recorded melonDS 1.1 and DeSmuME tests are limited regression checks.
  Hardware, flashcart, Delta and complete campaign compatibility remain unverified. Keep in-game save backups.
- The installer backend is verified separately from gameplay. See the workspace
  packaging verification report for the actual installation checks performed.
- Native Windows/macOS application packaging, signing and GUI testing across
  platforms remain future work. Python and xdelta3 are required by this prototype.

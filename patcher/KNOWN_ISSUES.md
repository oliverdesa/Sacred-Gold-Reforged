# Sacred Gold Reforged Alpha 5a — testing status

Sacred Gold by **Drayano**; Gen V engine integration based on **Platinum Reforged
/ Anvil by smoldice**. This independent testing build is not an official release
from either creator. Combined by [Oliver De Sa](https://github.com/oliverdesa).
See the package credits for all contributors and licences.

This is a work-in-progress game build. The installer reproduces Alpha 5a.

- Alpha 5a retains independent instant field/battle text and HP/EXP bar options
  in native Options (R or touch the title to switch pages). Field timing is
  separate and leaves music timing unchanged. Experimental battle speed-up is
  vaulted after a reported battle-entry black screen; native battle timing is
  restored to Alpha 4ab. Nuzlockers passed double-battle entry and a complete
  turn; 22 focused game-code checks passed. The Alpha 5a melonDS battle check
  remains unverified because the test-save import was not recognized.
- Alpha 4ab fixes Safari partner healing-dialog cleanup before unloading the
  field heap, and unlocks the portable Move Reminder after talking to the
  Cianwood reminder. Full campaign regression remains incomplete.

- Alpha 4aa fixes the shared particle-resource reader: if the requested graphics
  allocation fails, it can borrow available logic memory; a read is never sent
  to a null destination. Installed-code checks reproduce both Mira crashes and
  cover Tri Attack's three concurrent effects. Native cleanup follows allocation
  ownership. Animation scripts and move mechanics are unchanged. Live retest pending.

- Alpha 4z reclaims unused networking memory in offline NPC tag battles for
  graphics. It addresses the diagnosed particle-allocation failure in the Mira
  gauntlet crash while retaining the three-trainer AI budget. Captured-state and
  helper checks passed; Tri Attack still failed, prompting the 4aa reader fix.

- Alpha 4y enables all scripted campaign NPC tag-team trainer battles (including
  the Safari Rocket gauntlet), with separate parties, doubles AI for all three
  NPC trainers and native partner portraits. Automated code checks passed; live
  tag-battle entry, turns, replacements, item use and story return remain unverified.
  Partner wild captures and other facilities retain their previous routing.

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

Alpha 5a fixes the portable Frontier tutor menu setup and cancellation, merges the three tutor pools into one compatible move list, and preserves normal BP prices. Save layout and battle timing are unchanged. Tutor list, paging, no-BP, cancellation, teaching, and normal party summary were checked in DeSmuME Nuzlockers; melonDS has not been tested for this change.

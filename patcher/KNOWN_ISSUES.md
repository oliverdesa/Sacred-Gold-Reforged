# Sacred Gold Reforged Alpha 4s — testing status

Sacred Gold by **Drayano**; Gen V engine integration based on **Platinum Reforged
/ Anvil by smoldice**. This independent testing build is not an official release
from either creator. See the package credits for all contributors and licences.

This is a work-in-progress game build. The installer reproduces Alpha 4s; it does
not repair additional gameplay bugs.

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
- Hardware, flashcart and emulator compatibility beyond the recorded DeSmuME
  sessions has not been established. Keep in-game save backups.
- The installer backend is verified separately from gameplay. See the workspace
  packaging verification report for the actual installation checks performed.
- Native Windows/macOS application packaging, signing and GUI testing across
  platforms remain future work. Python and xdelta3 are required by this prototype.

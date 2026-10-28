# Sacred Gold Reforged Alpha 5a — local installer prototype

Sacred Gold by **Drayano**; Gen V engine integration based on **Platinum Reforged
/ Anvil by smoldice**. See THIRD_PARTY_NOTICES.md in the workspace, or CREDITS.txt
in the installer package, for contributor and licence details.

This installer builds Sacred Gold Reforged Alpha 5a, including the Factory engine,
opponent-themed Factory scenes, Gym/League backgrounds, melonDS battle guards
and fast egg hatching. It reproduces the
normal campaign ROM: Frontier access still requires Jasmine. It includes no
ROMs, saves, debug access flags, official hack patches or Reforged bundle.

This is a local packaging prototype, not a public release cleared for redistribution.
Read KNOWN_ISSUES.txt before playing. Packaging verification does not establish
that every part of the game works.

Alpha 5a moves speed controls into the in-game Options screen. Press R or touch
the title to switch pages. Field text, field timing, battle text and HP/EXP bars
are independent; Confirm applies them and Quit cancels. Save normally to keep
them. Experimental battle speed-up is vaulted and battle timing matches Alpha
4ab. Alpha 4ab's Safari partner cleanup fix and Cianwood Move Reminder unlock
(after speaking to the reminder) are included.

## Setup

- Install Python 3.11 or newer. The file picker also needs Tk (included with the
  normal python.org Windows/macOS installer; commonly python3-tk on Linux).
- Install xdelta3, or select its executable in the installer. The tested encoder
  and decoder is xdelta3 3.2.2: https://github.com/jmacd/xdelta/releases/tag/v3.2.2
  It is not bundled. Keep xdelta's applicable licence with any binary you redistribute.
- For Clean ROMs mode, also install Pillow in that Python environment:
  `python3 -m pip install Pillow`.
- Extract the whole ZIP into a folder. Keep release.json and its .xdelta beside
  sacred_gold_patcher.py. Run `python3 sacred_gold_patcher.py` to open the file picker.
  Windows can use Start Patcher.bat; macOS can use Start Patcher.command once
  Python is installed. This prototype is Python source, not a native executable.

The installer performs no downloads and makes no network requests. Your ROMs
stay on your computer. It does not search for, read or modify emulator saves.
Choose a new .nds output filename; existing files are never replaced. Temporary
files are removed on success or handled failure. Allow about 1.1 GiB free space
for a clean build, or 0.7 GiB for a prepared build, plus space for your source files.
After an operating-system crash or force-quit, an abandoned .sacred-gold-build-*
temporary folder can be removed when no installer is running.

## Clean ROMs mode

Select these six inputs:

1. Pokemon HeartGold, USA, revision 0 (134217728 bytes).
2. Pokemon Platinum, USA, revision 0 (134217728 bytes).
3. Pokemon Black Version 2, USA/Europe, revision 0 (536870912 bytes).
4. The official modern Complete 1.05 patch named SacredGold105.xdelta
   (15023442 bytes). Not the Fairy addon, Storm Silver, Classic, an optional
   patch, or another repack of the original release.
5. The extracted Platinum Reforged Anvil source folder at commit
   89e6cfe11420dd8823d0ecfb7885f3a528ad18f1. Select its top-level folder containing
   anvil/, tools/ and game/. Every Python source used by the builder is checked
   against the pinned release before execution.
6. The original Anvil v0.1.0-alpha reforged.bundle (630876 bytes).

Obtain official inputs from their authors:

- Sacred Gold / Storm Silver: https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/
- Drayano's HGSS folder: https://drive.google.com/drive/folders/0B-zmEVN0Mas6VlhJNHc0YWx3UUk?resourcekey=0-RYApzpdEIcGIkiTfKxyKqw
- Pinned Anvil source: https://github.com/smoldice/platinum-reforged-anvil/archive/89e6cfe11420dd8823d0ecfb7885f3a528ad18f1.zip
- Pinned bundle: https://github.com/smoldice/platinum-reforged-anvil/releases/download/v0.1.0-alpha/reforged.bundle

Do not substitute the latest Anvil release: this build uses its original alpha.
Use your own cartridge dumps. No Redux, Renegade Platinum or Following Renegade
patch is needed for this Sacred Gold installer. This first version accepts only
the exact source dumps listed in release.json; trimmed or alternate revisions
are rejected, even if another patcher might accept them.

The installer applies Sacred Gold, builds its Reforged donor from your Platinum
and Black 2, and applies our patch against those two prepared files. Each stage
must match the pinned checksum. The composite source is temporary and never
included in the package.

## Prepared ROMs mode

If you already built the two upstream inputs, choose:

- Sacred Gold Complete 1.05: 131037664 bytes,
  SHA-256 49f29848878406990ea288f26872d4355c92c4a2677f56973750bbf2566c13c1.
- Original Platinum Reforged Anvil alpha donor: 268435456 bytes,
  SHA-256 17afd998421183ab1421c0419bf9a6d545c034dc6c9ee3fa62779d8aa342ca77.

This mode needs Python and xdelta3, but no Pillow or Anvil source folder.
Do not use Renegade Reforged, a newer Platinum Reforged, or an older Sacred Gold
Reforged ROM in these slots. You are supplying upstream build inputs, not your
current playthrough ROM or save.

## Command line

Prepared inputs:

```sh
python3 sacred_gold_patcher.py --sacred-gold "SacredGold-Complete.nds" --reforged "Platinum-Reforged-original-alpha.nds" --xdelta3 "/path/to/xdelta3" --out "SacredGold-Reforged-alpha5a.nds"
```

Clean inputs:

```sh
python3 sacred_gold_patcher.py --heartgold "HeartGold.nds" --platinum "Platinum.nds" --black2 "Black2.nds" --sacred-gold-patch "SacredGold105.xdelta" --anvil-source "/path/to/pinned-anvil" --bundle "reforged.bundle" --xdelta3 "/path/to/xdelta3" --out "SacredGold-Reforged-alpha5a.nds"
```

Omit --xdelta3 if xdelta3 is on PATH. On Windows, use `py -3` instead of python3.
The output must be 268435456 bytes with SHA-256:
7401754e880b386c73c7eb354a08fd717b9b9f7745994b6f367b726262346cdc

## Saves and bug reports

Back up your in-game battery save before changing ROM versions. Use the new ROM
with an ordinary in-game save; avoid carrying emulator savestates across builds.
The installer does not import saves or change emulator settings. Save
compatibility from arbitrary other hacks has not been established.

For a bug report include Alpha 5a, emulator name/version, location, single/double/
Factory battle, the exact action or move, screenshot/error text, and a nearby
in-game save if available. Share the save privately; do not attach full ROMs.

## Distribution status

The package contains our installer source, metadata and a delta against BOTH
prepared donors. This avoids packaging the donors themselves, but a delta is not
an automatic permission to redistribute other authors' work. Review upstream
terms before public distribution, especially Anvil's explicit exclusion of its
runtime bundle and custom art from its MIT tool licence. Obtain those upstream
inputs separately; they are not bundled here. Credits are in CREDITS.txt.

Alpha 4x also fixes the low-HP music preference crash found in melonDS doubles testing.
Factory streak and weather testing remains in progress; see KNOWN_ISSUES for scope.

Alpha 4y enables all scripted campaign NPC tag-team trainer battles, including
the Safari Zone Rocket gauntlet, with doubles AI for the ally and both opponents.
Native partner portraits are converted as well. Automated routing, AI, portrait
and result-handoff checks passed; tag-team gameplay still needs testing.

Alpha 4z reclaims unused offline tag-battle networking memory for graphics,
addressing the diagnosed Mira particle-allocation crash. Live retesting is pending.

Alpha 4aa adds safe particle-resource allocation with a fallback from graphics
to available battle logic memory. This addresses Tri Attack's concurrent effect
loads without changing its animation or mechanics. Captured-state checks pass;
live retesting remains pending.

Alpha 5a fixes the portable Frontier tutor menu setup and cancellation, merges the three tutor pools into one compatible move list, and preserves normal BP prices. Save layout and battle timing are unchanged. Tutor list, paging, no-BP, cancellation, teaching, and normal party summary were checked in DeSmuME Nuzlockers; melonDS has not been tested for this change.

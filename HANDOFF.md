# HANDOFF — GAME-Emulator

**Last updated: 2026-11-22 (America/New_York).**
**Repo:** `mhvnsnt/GAME-Emulator` (PUBLIC), default branch `main`.
**Purpose of this file:** any agent that picks up work here reads this FIRST, then the linked docs. It states what we've done, where we're at, and what we're working toward — so the owner can say "go to this repo, pick up the work" and you just know. Update this file in the same PR whenever the state changes (add, don't delete).

## 1. What this repo is

GAME: Emulator — a local-first intake and library manager for game files you are authorized to use. It starts with the local import/catalog pipeline migrated from the temporary Bannon staging branch. It is **not yet a full emulator frontend**: native Libretro FFI, isolated core execution, real test-ROM smoke tests, and reversible mod overlays remain gated follow-up work.

At ~334 KB it is a Python project (`src/`, `tests/`, `pyproject.toml`, `imports/`, `docs/`). It is the intake/catalog half of the owner's emulator plan — the thing that takes game files in, catalogs them, and keeps them straight — while the actual emulation (universal-emulator, chimera-emulator-hub) lives in the sibling repos.

## 2. Where we're at

### DONE
- **Intake/catalog pipeline migrated:** the local import/catalog pipeline from the temporary Bannon staging branch now lives here (`src/`, `imports/`).
- **Anti-clobber laws merged (2026-10-17, PR #4):** the owner's anti-clobber laws are in `AGENTS.md`.
- **Working method stated (2026-10-27):** commits `a994983` / `b743d9d`, `WORKING-METHOD.md` at root.
- **Last push 2026-11-20** (repo metadata; no new content commits after Oct 27 — the push reflects repo-level activity).

### IN PROGRESS
- **Three open PRs:** PR #7 — "Docs: pre-made parts first rule" (2026-11-20, `docs/premade-parts-first`); PR #6 — "Docs: sourcing rule" (2026-11-19, `docs/sourcing-rule`); PR #1 — "Add isolated Libretro ctypes worker and OS sandbox gate" (`feat/libretro-isolated-worker`) — the real work PR, the first step toward actual emulation (isolated core execution behind an OS sandbox gate). Next step: a merge call on #1, #6, #7 — #1 is the one that matters most.
- **Gated follow-ups (not started, per the README):** native Libretro FFI, isolated core execution, real test-ROM smoke tests, reversible mod overlays. Gated means: not yet approved to build, not just unstarted.

### BLOCKED
- **Nothing recorded as blocked in the repo state read 2026-11-22.** No blocked item is named in this repo. The open PRs are awaiting a merge decision, not unblocked work. The gated follow-ups are gated by the owner (see §6), not blocked by a technical failure.

## 3. What we're working toward

**The goal:** a local-first library that takes game files in, catalogs them, and eventually plays them — full emulator frontend with isolated Libretro cores, test-ROM smoke tests, and reversible mod overlays — built on the intake pipeline already here.

**The bar (owner, general):** REAL-SOURCE-ONLY — real parts, wired in, no hand-tooled lookalikes; the work proves itself running, never a text-only "done". For the emulator work specifically: isolated core execution behind a sandbox gate (PR #1) before any core runs untrusted code.

**In order:** (1) merge or close PRs #1, #6, #7; (2) owner un-gates the next follow-up (Libretro FFI / isolated execution / test-ROM smoke tests / mod overlays); (3) build the un-gated piece, proven with real test ROMs.

## 4. Standing rules that apply here

- **Branch → PR → merge, always.** Never push to main directly. Add-only, zero-conflict PRs, no force pushes.
- **Checkpoint-and-save law:** CHECKPOINT.md first, update after every step; the repo is the save; resume, never restart.
- **No-temp-storage law:** nothing in /tmp or any wipeable location, ever. Everything goes straight into the repo or a durable folder the second it exists.
- **Real-source-only:** every part comes from the actual source code and files, wired up fully. No hand-tooled lookalikes, no fake panels.
- **Anti-clobber law (owner 2026-10-17):** do not clobber other lanes' work. Add, don't overwrite. (Merged as PR #4.)
- **Never-delete-game-files / store-verify-clear:** game files are NEVER auto-deleted; they leave local disk only after verified 100% on GitHub OR TeraBox with retrievability proven. (This repo catalogs game files you are authorized to use — authorization matters here.)
- **No-gaps / solve-it law:** a gap or block is never the end of the work — route-switch until it's done or every reasonable route is exhausted with exact errors recorded.
- **Licence-not-a-gate:** licence status never gates pulling in material that helps; licence/source is still logged honestly next to the item.

## 5. Key files and paths

| What | Where |
|---|---|
| Emulator overview + gated scope (start here) | `README.md` |
| Source | `src/` |
| Tests | `tests/` |
| Project config | `pyproject.toml` |
| Imports / intake | `imports/` |
| Agent notes / working method | `AGENTS.md`, `WORKING-METHOD.md` |
| Docs | `docs/` |
| Open PRs | #1 (isolated Libretro ctypes worker + OS sandbox gate), #6 (sourcing rule), #7 (pre-made parts first rule) |
| Merged PR | #4 (anti-clobber laws, 2026-10-17) |
| Sibling repos | `mhvnsnt/universal-emulator` (plan), `mhvnsnt/chimera-emulator-hub` (playable hub) |

There are no releases in this repo. Only game files the owner is authorized to use go through this intake.

## 6. Open decisions needing the owner

- **Merge PRs #1, #6, #7?** #1 is the isolated Libretro worker + sandbox gate — the first real emulation step. #6/#7 are docs rules. Merging #1 starts the emulation work; leaving it open leaves the repo as intake-only. His call — lanes do not decide merges.
- **Un-gate the follow-ups?** Native Libretro FFI, isolated core execution, real test-ROM smoke tests, reversible mod overlays are all gated. Which one gets un-gated first, and when, is his call — a lane cannot un-gate them.
- **No other owner decision is recorded as open in this repo's state.**

## 7. How to pick up

1. Read this HANDOFF.md first, then `README.md` (the gated scope is in there), `AGENTS.md`, and `WORKING-METHOD.md`.
2. Check the three open PRs (#1, #6, #7) — leave them alone unless told to merge. Do NOT build the gated follow-ups until the owner un-gates them.
3. Only authorized game files go through this intake. Never pull in files the owner isn't authorized to use.
4. Resume from the stated next step — never restart, never re-derive finished work.
5. Land work branch → PR → merge, add-only. Update this HANDOFF.md in the same PR when the state changes. Prove emulation work with real test-ROM smoke tests, not descriptions.

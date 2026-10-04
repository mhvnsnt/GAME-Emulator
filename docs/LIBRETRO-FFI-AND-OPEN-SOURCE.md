# Libretro FFI and open-source integration plan

## Decision: keep the host language-neutral

The Libretro ABI is a C API. A host can call it through C# P/Invoke, Rust libloading/FFI, or Python ctypes/cffi; no C++ rewrite is required just to load a compatible core. Keep a small, versioned host contract and put each language binding behind an adapter. The existing Python application remains the intake/catalog/test harness. For production real-time emulation, use a maintained frontend (RetroArch) first; only build a custom host when a tested requirement cannot be met by that frontend.

## Correctness constraints

- Loading an arbitrary native core is code execution. Never ctypes.CDLL() a user-supplied library in the dashboard or importer process. Native-core probing and execution need a separately launched, resource-limited worker and a clear trust/install step.
- The core API exposes callbacks for video, audio, input, environment, and lifecycle. The host must retain callback references for the entire core lifetime, match C ABI widths/packing, handle pixel formats and audio batches, and shut down deterministically.
- retro_run() advances an emulated frame. A host's wall-clock delta is not passed into retro_run(); pacing synchronizes the frontend's frame cadence/audio/video. Avoid multiple concurrent calls into one core unless that core explicitly supports it.
- Core RAM is not universally available for arbitrary edits. retro_get_memory_data() / retro_get_memory_size() expose only memory regions that a particular core elects to expose. A null pointer or zero size means no usable region. Treat memory pointers as borrowed, invalidate them across unload/reset where required, and bound-check every access.
- IPS/BPS patches describe changes to a content image, not generic RAM addresses. Apply a patch to a copy/overlay before loading when compatible. Runtime RAM patches need an explicit per-game, per-version, per-region address map and assertions; never infer offsets from a different ROM revision.
- There is no universal safe mod mix for arbitrary consoles. Use ordered, reversible per-game layers and conflict rules that understand each mod's target (file patch, asset replacement, emulator cheat, or documented RAM patch). Unknown overlap fails closed.
- Do not load BIOS/keys/firmware from an internet search or bundle them. Let a legally obtained, user-installed emulator/core validate its own requirements.

## Proposed stages and acceptance gates

1. Gate A — import CI: Ruff and pytest pass on the current PR; synthetic fixtures only.
2. Gate B — adapter inventory: record OS, architecture, frontend path/version, core path/version, core license, supported systems, firmware requirements, and hash. Do not load a native library during import.
3. Gate C — isolated core probe: start a separate worker with explicit user confirmation; impose CPU/memory/time limits; call only ABI discovery/lifecycle functions in a disposable process; worker crash must not crash the dashboard or corrupt the library.
4. Gate D — single-frame smoke test: with a known homebrew/test ROM, verify callback registration, environment negotiation, retro_load_game, one retro_run, valid video/audio callback bounds, then unload/deinit. Save a redacted diagnostic report.
5. Gate E — launch profiles: explicit core selection and per-game overrides; no automatic guessing for ambiguous disc formats.
6. Gate F — mod profiles: manifest schema, base content hash, patch format, target region, ordering, conflicts, rollback and before/after hashes. RAM patches disabled unless the selected core exposes a verified region and a matching versioned address map.
7. Gate G — regression lab: homebrew/public-domain fixtures, deterministic save-state and input replay where supported, crash isolation, fuzzed manifests, and per-core capability tests.

## Open-source component assessment

| Component | Use | Decision / caveat |
|---|---|---|
| libretro/RetroArch | Mature frontend/core host | Prefer launching installed RetroArch for initial real-world playback. GPL-3.0; keep integration via process/CLI unless licensing obligations are reviewed. |
| Libretro API headers/docs | ABI contract and callback definitions | Use the upstream API contract; pin a known revision and test structure sizes/callback signatures. |
| mgba-emu/mgba | GBA emulator, debugger/GDB support | Useful as an optional GBA-specific adapter and test target. MPL-2.0; build/configuration is platform-dependent. Do not assume a stable general-purpose Python API exists in every build. |
| libretro/libretro-database | Hash/name metadata and DATs | Optional, offline metadata matching only. CC-BY-SA-4.0; track attribution/share-alike obligations and pin the data revision. It does not provide game files or guarantee a match for every dump. |
| chaoticgd/ghidra-emotionengine-reloaded | PS2 / Emotion Engine Ghidra support | Optional manual analysis plugin, Apache-2.0. Not required to run games and not a safe automatic intake step. |
| abelbriggs1/ghidra-ps2sdk | Proposed PS2 SDK signatures | Repository was not found at the supplied GitHub path during verification; do not depend on it until a canonical project URL and license are verified. |
| libretropy/libretro.py | Proposed Python binding | Repository was not found at the supplied GitHub path during verification. Do not add a dependency based on that name. Use official C headers plus a small audited ctypes binding only inside an isolated worker if Python FFI is needed. |
| Rust libretro-rs | Rust host wrapper | Verify exact upstream, maintenance, API coverage, and license before adoption; keep as a candidate, not a hard dependency. |
| Kermalis/Retro.Net / Unity wrapper | .NET binding | Verify the exact repository and license/maintenance before selecting. The current project does not require .NET to launch through RetroArch. |
| loot/libloot | Bethesda-specific plugin sorting metadata | GPL-3.0 and domain-specific. Do not treat it as a universal binary/RAM collision resolver. Reuse only if a future supported mod format genuinely matches its model and license review approves. |
| Sir-Walrus/Flips | IPS/BPS patch reference/tool | Supplied repository is archived and its API response did not assert a license. Do not vendor code until license is established. Use a maintained, license-verified patch library or isolated CLI and keep patching on copies/overlays. |
| Ghidra / radare2 | Optional reverse engineering | Separate, explicit analysis tools only. Never automatically turn proprietary decompiler output into replacement code. |
| Playwright | Test the dashboard/UI | UI automation only; not a ROM discovery/downloader or protection bypass. |

## Required mod manifest (first draft)

Each mod should declare: stable ID/version, author/source/license, target system/title ID, exact base-content SHA-256 or accepted revision set, operation type, patch-file hash, target region/address map where applicable, dependencies, conflicts, priority, and rollback artifact. Unknown fields, mismatched base hashes, overlapping unresolvable operations, and untrusted native plugins should block activation.

## Scope of this PR

The current branch implements local file intake/catalog and a launch handoff to an already-installed RetroArch/core. It does not yet implement native Libretro FFI callbacks, sandboxed core execution, per-core controller/save-state integration, or mod overlays. Those should land behind the gates above rather than pretending that an arbitrary DLL/SO can safely and universally expose writable RAM.

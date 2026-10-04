# Architecture and boundaries

## Implemented local flow

```text
User selects local source folder
  -> recursive scan / extension allowlist / size and symlink checks
  -> SHA-256 source fingerprint and stability check
  -> classify by known extension and parent-folder labels
  -> copy to content-addressed library
  -> hash verification of stored copy
  -> SQLite metadata + deduplication
  -> local loopback dashboard / CLI catalog
```

The source remains unchanged. The app never unpacks archives, executes imported content, downloads missing firmware, or sends game files to GitHub/cloud services. The local dashboard binds to loopback only and is not a general-purpose file server.

## System identification

Extensions are hints, not proof. Shared extensions such as ISO/BIN/PKG/ELF remain ambiguous unless the directory label supplies a clear system. A later metadata adapter can offer likely matches but should retain confidence and never silently assert a guess as fact.

## Next integration stages

1. Continuous folder/removable-drive watcher with safe handling of partially copied files.
2. Metadata adapters with opt-in network access to legitimate catalog sources.
3. Capability registry for installed emulator frontends/cores, licenses, system coverage and firmware prerequisites.
4. Expand the explicit RetroArch launch handoff into a capability-tested frontend/core registry, save/state isolation, controller mapping and test evidence.
5. Reversible per-game mod profiles, load order, conflict detection and rollback. Mixing must be format/game-specific; unrelated console binaries cannot be generically blended.
6. Optional isolated analysis adapters with explicit invocation, audit logs, and resource ceilings.

## Analysis tools

Ghidra and radare2 are optional, separately invoked analysis tools—not default intake steps. AssetStudio is not a universal package extractor. Playwright tests this app's UI. Browser automation must not defeat anti-bot protections or fetch protected binaries. Do not automatically translate proprietary decompiler output into a substitute implementation.

## Threat model

Treat filenames and binaries as untrusted. Never shell-interpolate filenames. Do not expose the library to the web server or network. Keep reports free of file contents and secrets. Before enabling third-party analysis workers, add OS/container isolation and malware scanning.

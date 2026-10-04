# Isolated Libretro worker

The native core is loaded only inside a disposable child process. The dashboard,
catalog, and parent orchestration process never calls `ctypes.CDLL()`.

## Process boundary

The parent uses Python `multiprocessing`, explicitly selecting the `spawn`
context so the worker does not inherit the parent's ordinary process state and
file descriptors. The IPC pipe is created before the worker starts and is the
only intended control channel.

This is **fault isolation**, not a security boundary by itself.

## OS security boundary

Before the first `ctypes.CDLL()` / `dlopen()`, the worker receives both the
native core path and content path and applies an OS policy.

### Linux

Linux strict mode uses Landlock plus `PR_SET_NO_NEW_PRIVS`:

- native shared libraries and required system library trees are read/execute only;
- the core directory is read/execute only;
- the content directory is read-only;
- filesystem writes, creation, deletion, and truncation handled by the
  available Landlock ABI are denied;
- TCP/UDP bind/connect operations supported by the installed Landlock ABI are
  denied because no network rules are granted;
- abstract UNIX-socket connections are scoped when the ABI supports it;
- CPU, address-space, file-size, descriptor-count, process-count, and core-dump
  limits are lowered with POSIX resource limits.

The policy is **fail-closed** if Landlock is unavailable. It does not claim to
be a complete container: system calls not covered by Landlock remain subject to
normal kernel permissions. A future Linux launcher can add bubblewrap/seccomp
for an even smaller syscall/namespace surface.

### Windows

The current worker can apply a Windows Job Object for process-count and memory
limits, but strict filesystem/network isolation is **not** claimed here.
Windows AppContainer/LPAC must be established when the worker process is
created, so the next Windows implementation should launch the native worker
through an AppContainer/LPAC-aware launcher rather than pretending a Job Object
is equivalent.

### macOS

Strict mode is intentionally fail-closed. Seatbelt/App Sandbox must be applied
at process launch; the existing in-process worker does not silently downgrade
to an unrestricted native core.

## Protocol

The worker sends `READY`, then accepts `LOAD`, `TICK`, and `SHUTDOWN`.
`LOAD` reports the sandbox policy that actually succeeded. `TICK` performs
exactly one `retro_run()` and reports whether video refresh fired.

The parent treats EOF, a dead child, timeout, or unexpected exit as a worker
failure. A native crash therefore terminates the worker rather than the main
application.

## ABI ordering

All Libretro callbacks are installed before `retro_init()`. This matters
because a core may call the environment callback during initialization,
including `RETRO_ENVIRONMENT_SET_PIXEL_FORMAT`. Callback objects are retained
on the worker instance for the native-core lifetime.

## Explicit development escape hatch

`GAME_EMULATOR_ALLOW_UNSANDBOXED_CORE=1` exists only for development/debugging.
Strict worker execution does not use it. Production code should never set it.

## Real one-frame integration test

The opt-in test uses `GAME_EMULATOR_TEST_CORE` and
`GAME_EMULATOR_TEST_CONTENT`, pointing only to locally installed/authorized
artifacts. No ROMs, BIOS files, keys, firmware, or native cores are downloaded.

A passing test proves the installed core can execute one frame through the
current ABI and sandbox policy; it does not certify arbitrary third-party cores
as safe.

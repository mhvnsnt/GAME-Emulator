# Isolated Libretro worker

The native core is loaded only inside a disposable child process. The dashboard,
catalog, and parent orchestration process never calls `ctypes.CDLL()`.

## Process boundary

The parent uses Python `multiprocessing` with the `spawn` context. Spawn is
useful for avoiding a forked copy of the parent's memory, but it still inherits
the process environment and is **not a security boundary by itself**.

The worker control pipe uses bounded UTF-8 JSON bytes. It deliberately does not
use `Connection.send()` / `recv()` or pickle: a compromised native core must
not be able to send a crafted pickle that executes code when the parent decodes
a worker response. Malformed or oversized messages fail closed.

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
- strict mode requires Landlock ABI >= 8 for thread-synchronized TCP restrictions and installs a
  seccomp-BPF filter that denies socket/network syscalls, including UDP on older
  kernels; no TCP/UDP network rules are granted by Landlock;
- pathname UNIX-socket resolution and abstract UNIX-socket/signal scoping are
  restricted when supported by the ABI;
- CPU, address-space, file-size, descriptor-count, process-count, and core-dump
  limits are lowered with POSIX resource limits.

The policy is **fail-closed** if Landlock is unavailable/below ABI 8 or seccomp
cannot be installed. This is not a complete container: system calls outside the
network filter and Landlock policy remain subject to normal kernel permissions.
CI's host-isolation test will exercise this path when its kernel permits the
Landlock/seccomp policy; a future launcher can add bubblewrap/namespaces for a
smaller filesystem and syscall surface.

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

`GAME_EMULATOR_ALLOW_UNSANDBOXED_CORE=1` can only request a non-strict
development path. Strict worker execution rejects this override and cannot be
downgraded by setting the environment variable. Production code should never set it.

## Real one-frame integration test

The opt-in test uses `GAME_EMULATOR_TEST_CORE` and
`GAME_EMULATOR_TEST_CONTENT`, pointing only to locally installed/authorized
artifacts. No ROMs, BIOS files, keys, firmware, or native cores are downloaded.

A passing test proves the installed core can execute one frame through the
current ABI and sandbox policy; it does not certify arbitrary third-party cores
as safe.

# Isolated Libretro worker

The native core is loaded only inside a disposable child process. The dashboard, catalog, and parent orchestration process never calls `ctypes.CDLL()`.

## Protocol

The worker sends `READY`, then accepts `LOAD`, `TICK`, and `SHUTDOWN`. `TICK` performs exactly one `retro_run()` and reports whether video refresh fired.

The parent treats EOF, a dead child, timeout, or unexpected exit as a worker failure. A native crash therefore terminates the worker rather than the main application.

## ABI ordering

All Libretro callbacks are installed before `retro_init()`. This matters because a core may call the environment callback during initialization, including `RETRO_ENVIRONMENT_SET_PIXEL_FORMAT`. Callback objects are retained on the worker instance for the native-core lifetime.

## Safety status

A subprocess is crash containment, not a complete OS sandbox. Resource limits, platform-specific sandboxing, path restrictions, and privilege reduction remain required before treating arbitrary native cores as untrusted code.

The real one-frame integration test is opt-in through `GAME_EMULATOR_TEST_CORE` and `GAME_EMULATOR_TEST_CONTENT`, pointing only to locally installed/authorized artifacts. No ROMs, BIOS files, keys, firmware, or native cores are downloaded.

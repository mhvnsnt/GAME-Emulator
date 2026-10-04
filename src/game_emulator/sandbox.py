"""OS-level restrictions for the native Libretro worker.

The sandbox is applied in the worker immediately before ctypes loads the native core.
It is deliberately fail-closed in strict mode: unsupported platforms do not silently
pretend to provide a filesystem/network security boundary.

Linux uses Landlock for filesystem/network policy plus no_new_privs and Unix resource
limits. Windows currently applies a Job Object resource/process boundary; the full
AppContainer/LPAC launch path remains a separate launcher because AppContainer must
be established when the process is created. macOS likewise requires a launch-time
Seatbelt/App Sandbox wrapper.
"""
from __future__ import annotations

import ctypes
import os
import platform

try:
    import resource
except ImportError:  # pragma: no cover - Windows
    resource = None
from dataclasses import dataclass
from pathlib import Path


class SandboxError(RuntimeError):
    """Raised when the requested native-core security boundary cannot be established."""


@dataclass(frozen=True)
class SandboxPolicy:
    strict: bool = True
    max_cpu_seconds: int = 10
    max_address_space: int = 2 * 1024 * 1024 * 1024
    max_file_size: int = 8 * 1024 * 1024
    max_open_files: int = 256
    max_processes: int = 64
    read_only_paths: tuple[Path, ...] = ()


# Linux Landlock constants.  The syscall numbers are stable for the supported
# Linux architectures; unsupported architectures fail closed.
_LANDLOCK_CREATE_RULESET_VERSION = 1
_LANDLOCK_RULE_PATH_BENEATH = 1
_LANDLOCK_RESTRICT_SELF_TSYNC = 1 << 3
_LANDLOCK_CREATE_RULESET_VERSION_FLAG = 1

_LANDLOCK_ACCESS_FS_EXECUTE = 1 << 0
_LANDLOCK_ACCESS_FS_WRITE_FILE = 1 << 1
_LANDLOCK_ACCESS_FS_READ_FILE = 1 << 2
_LANDLOCK_ACCESS_FS_READ_DIR = 1 << 3
_LANDLOCK_ACCESS_FS_REMOVE_DIR = 1 << 4
_LANDLOCK_ACCESS_FS_REMOVE_FILE = 1 << 5
_LANDLOCK_ACCESS_FS_MAKE_CHAR = 1 << 6
_LANDLOCK_ACCESS_FS_MAKE_DIR = 1 << 7
_LANDLOCK_ACCESS_FS_MAKE_REG = 1 << 8
_LANDLOCK_ACCESS_FS_MAKE_SOCK = 1 << 9
_LANDLOCK_ACCESS_FS_MAKE_FIFO = 1 << 10
_LANDLOCK_ACCESS_FS_MAKE_BLOCK = 1 << 11
_LANDLOCK_ACCESS_FS_MAKE_SYM = 1 << 12
_LANDLOCK_ACCESS_FS_REFER = 1 << 13
_LANDLOCK_ACCESS_FS_TRUNCATE = 1 << 14
_LANDLOCK_ACCESS_FS_IOCTL_DEV = 1 << 15
_LANDLOCK_ACCESS_FS_RESOLVE_UNIX = 1 << 16

_LANDLOCK_ACCESS_NET_BIND_TCP = 1 << 0
_LANDLOCK_ACCESS_NET_CONNECT_TCP = 1 << 1
_LANDLOCK_ACCESS_NET_BIND_UDP = 1 << 2
_LANDLOCK_ACCESS_NET_CONNECT_SEND_UDP = 1 << 3

_LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET = 1 << 0
_LANDLOCK_SCOPE_SIGNAL = 1 << 1

_PR_SET_NO_NEW_PRIVS = 38
_PR_SET_SECCOMP = 22
_SECCOMP_MODE_FILTER = 2
_SECCOMP_SET_MODE_FILTER = 1
_SECCOMP_FILTER_FLAG_TSYNC = 1
_SECCOMP_RET_KILL_PROCESS = 0x80000000
_SECCOMP_RET_ERRNO = 0x00050000
_SECCOMP_RET_ALLOW = 0x7FFF0000
_BPF_LD_W_ABS = 0x20
_BPF_JMP_JEQ_K = 0x15
_BPF_RET_K = 0x06

# Landlock was added at syscall numbers 444..446 on the architectures we
# support explicitly here.
_LANDLOCK_SYSCALLS = {
    "x86_64": (444, 445, 446),
    "amd64": (444, 445, 446),
    "aarch64": (444, 445, 446),
    "arm64": (444, 445, 446),
    "riscv64": (444, 445, 446),
    "ppc64le": (444, 445, 446),
}

# Linux syscall numbers denied in the strict worker seccomp policy.
# This blocks network access, cross-process memory access, kernel BPF/perf
# surfaces, namespace/mount changes, and io_uring. Unsupported architectures fail closed.
_DENIED_SYSCALLS = {
    "x86_64": (
        41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55,
        101, 155, 165, 166, 248, 249, 250, 272, 288, 298, 299, 304, 307,
        308, 310, 311, 312, 321, 323, 425, 426, 427, 434, 438, 440,
    ),
    "amd64": (
        41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55,
        101, 155, 165, 166, 248, 249, 250, 272, 288, 298, 299, 304, 307,
        308, 310, 311, 312, 321, 323, 425, 426, 427, 434, 438, 440,
    ),
    "aarch64": (
        39, 40, 41, 97, 117, 198, 199, 200, 201, 202, 203, 204, 205,
        206, 207, 208, 209, 210, 211, 212, 217, 218, 219, 241, 242, 243,
        265, 268, 270, 271, 272, 277, 280, 282, 425, 426, 427, 434, 438, 440,
    ),
    "arm64": (
        39, 40, 41, 97, 117, 198, 199, 200, 201, 202, 203, 204, 205,
        206, 207, 208, 209, 210, 211, 212, 217, 218, 219, 241, 242, 243,
        265, 268, 270, 271, 272, 277, 280, 282, 425, 426, 427, 434, 438, 440,
    ),
    "riscv64": (
        39, 40, 41, 97, 117, 198, 199, 200, 201, 202, 203, 204, 205,
        206, 207, 208, 209, 210, 211, 212, 217, 218, 219, 241, 242, 243,
        265, 268, 270, 271, 272, 277, 280, 282, 425, 426, 427, 434, 438, 440,
    ),
}
_SECCOMP_SYSCALLS = {
    "x86_64": 317,
    "amd64": 317,
    "aarch64": 277,
    "arm64": 277,
    "riscv64": 277,
}
_AUDIT_ARCH = {
    "x86_64": 0xC000003E,
    "amd64": 0xC000003E,
    "aarch64": 0xC00000B7,
    "arm64": 0xC00000B7,
    "riscv64": 0xC00000F3,
}


class _SockFilter(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_ushort),
        ("jt", ctypes.c_ubyte),
        ("jf", ctypes.c_ubyte),
        ("k", ctypes.c_uint32),
    ]


class _SockFprog(ctypes.Structure):
    _fields_ = [
        ("len", ctypes.c_ushort),
        ("filter", ctypes.POINTER(_SockFilter)),
    ]


class _RulesetAttr(ctypes.Structure):
    _fields_ = [
        ("handled_access_fs", ctypes.c_uint64),
        ("handled_access_net", ctypes.c_uint64),
        ("scoped", ctypes.c_uint64),
    ]


class _PathBeneathAttr(ctypes.Structure):
    _fields_ = [
        ("allowed_access", ctypes.c_uint64),
        ("parent_fd", ctypes.c_int32),
        ("_padding", ctypes.c_uint32),
    ]


def _libc() -> ctypes.CDLL:
    return ctypes.CDLL(None, use_errno=True)


def _syscall_numbers() -> tuple[int, int, int]:
    try:
        return _LANDLOCK_SYSCALLS[platform.machine().lower()]
    except KeyError as exc:
        raise SandboxError(
            f"Landlock syscall numbers are not defined for {platform.machine()}"
        ) from exc


def _syscall(number: int, *args: object) -> int:
    libc = _libc()
    libc.syscall.restype = ctypes.c_long
    return int(libc.syscall(number, *args))


def _set_no_new_privs() -> None:
    if _syscall(_PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0, 0) != 0:
        err = ctypes.get_errno()
        raise SandboxError(f"PR_SET_NO_NEW_PRIVS failed: {os.strerror(err)}")


def _landlock_abi() -> tuple[int, tuple[int, int, int]]:
    create, _, _ = _syscall_numbers()
    abi = _syscall(create, None, 0, _LANDLOCK_CREATE_RULESET_VERSION_FLAG)
    if abi < 0:
        err = ctypes.get_errno()
        raise SandboxError(f"Landlock unavailable: {os.strerror(err)}")
    return abi, (create, *_syscall_numbers()[1:])


def _readable_system_roots() -> list[Path]:
    roots = [Path("/usr"), Path("/lib"), Path("/lib64"), Path("/usr/local/lib")]
    return [root for root in roots if root.exists()]


def _readable_system_files() -> list[Path]:
    # The dynamic loader may consult this cache while resolving a core's
    # shared-library dependencies after Landlock is enforced.
    files = [Path("/etc/ld.so.cache")]
    return [path for path in files if path.is_file() and not path.is_symlink()]


def _add_path_rule(
    add_rule_syscall: int, ruleset_fd: int, path: Path, allowed_access: int
) -> None:
    flags = os.O_PATH | os.O_CLOEXEC
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise SandboxError(f"cannot open sandbox path {path}: {exc}") from exc
    try:
        rule = _PathBeneathAttr(
            allowed_access=allowed_access,
            parent_fd=fd,
            _padding=0,
        )
        result = _syscall(
            add_rule_syscall,
            ruleset_fd,
            _LANDLOCK_RULE_PATH_BENEATH,
            ctypes.byref(rule),
            0,
        )
        if result != 0:
            err = ctypes.get_errno()
            raise SandboxError(f"Landlock rule for {path} failed: {os.strerror(err)}")
    finally:
        os.close(fd)


def _apply_linux_landlock(
    core_path: Path,
    content_path: Path,
    read_only_paths: tuple[Path, ...] = (),
) -> int:
    abi, (create, add_rule, restrict) = _landlock_abi()
    # Landlock ABI 4 provides TCP restrictions. Seccomp below blocks socket
    # creation and network syscalls including UDP on older kernels.
    if abi < 8:
        raise SandboxError(
            "Linux strict mode requires Landlock ABI >= 8 for process-wide thread synchronization"
        )

    fs = (
        _LANDLOCK_ACCESS_FS_EXECUTE
        | _LANDLOCK_ACCESS_FS_READ_FILE
        | _LANDLOCK_ACCESS_FS_READ_DIR
    )
    # Handle every filesystem write/create/delete operation supported by this
    # kernel ABI.  No rule grants any of them, so they are denied by default.
    fs |= (
        _LANDLOCK_ACCESS_FS_WRITE_FILE
        | _LANDLOCK_ACCESS_FS_REMOVE_DIR
        | _LANDLOCK_ACCESS_FS_REMOVE_FILE
        | _LANDLOCK_ACCESS_FS_MAKE_CHAR
        | _LANDLOCK_ACCESS_FS_MAKE_DIR
        | _LANDLOCK_ACCESS_FS_MAKE_REG
        | _LANDLOCK_ACCESS_FS_MAKE_SOCK
        | _LANDLOCK_ACCESS_FS_MAKE_FIFO
        | _LANDLOCK_ACCESS_FS_MAKE_BLOCK
        | _LANDLOCK_ACCESS_FS_MAKE_SYM
    )
    if abi >= 2:
        fs |= _LANDLOCK_ACCESS_FS_REFER
    if abi >= 3:
        fs |= _LANDLOCK_ACCESS_FS_TRUNCATE
    if abi >= 5:
        fs |= _LANDLOCK_ACCESS_FS_IOCTL_DEV
    if abi >= 9:
        fs |= _LANDLOCK_ACCESS_FS_RESOLVE_UNIX

    net = _LANDLOCK_ACCESS_NET_BIND_TCP | _LANDLOCK_ACCESS_NET_CONNECT_TCP
    if abi >= 10:
        net |= _LANDLOCK_ACCESS_NET_BIND_UDP | _LANDLOCK_ACCESS_NET_CONNECT_SEND_UDP

    # IPC scoping was introduced in ABI 6.
    scoped = 0
    if abi >= 6:
        scoped = _LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET | _LANDLOCK_SCOPE_SIGNAL

    attr = _RulesetAttr(handled_access_fs=fs, handled_access_net=net, scoped=scoped)
    ruleset_fd = _syscall(
        create,
        ctypes.byref(attr),
        ctypes.sizeof(attr),
        0,
    )
    if ruleset_fd < 0:
        err = ctypes.get_errno()
        raise SandboxError(f"Landlock ruleset creation failed: {os.strerror(err)}")

    try:
        read_access = _LANDLOCK_ACCESS_FS_READ_FILE | _LANDLOCK_ACCESS_FS_READ_DIR
        execute_access = _LANDLOCK_ACCESS_FS_EXECUTE

        # Native shared libraries may need the dynamic loader and libc. They are
        # read-only and executable; no write access is ever granted.
        for root in _readable_system_roots():
            _add_path_rule(add_rule, ruleset_fd, root, read_access | execute_access)
        for system_file in _readable_system_files():
            _add_path_rule(add_rule, ruleset_fd, system_file, _LANDLOCK_ACCESS_FS_READ_FILE)
        for extra_path in read_only_paths:
            if extra_path.is_dir():
                _add_path_rule(add_rule, ruleset_fd, extra_path, read_access)
            else:
                _add_path_rule(
                    add_rule, ruleset_fd, extra_path, _LANDLOCK_ACCESS_FS_READ_FILE
                )

        # The core directory is exposed read/execute only. Content is exposed
        # read-only through its containing directory so normal path resolution
        # works for cores that inspect adjacent metadata.
        _add_path_rule(
            add_rule,
            ruleset_fd,
            core_path.parent,
            read_access | execute_access,
        )
        _add_path_rule(
            add_rule,
            ruleset_fd,
            content_path.parent,
            read_access,
        )

        _set_no_new_privs()
        if _syscall(restrict, ruleset_fd, _LANDLOCK_RESTRICT_SELF_TSYNC) != 0:
            err = ctypes.get_errno()
            raise SandboxError(f"Landlock enforcement failed: {os.strerror(err)}")
    finally:
        os.close(ruleset_fd)
    return abi


def _apply_linux_network_seccomp(*, synchronize_threads: bool = True) -> None:
    """Deny network and selected high-risk process/kernel syscalls.

    Production uses seccomp TSYNC to cover every worker thread. The single-threaded
    integration test can disable TSYNC only to validate the filter in restricted CI
    containers that reject the seccomp() syscall entirely.
    """
    architecture = platform.machine().lower()
    try:
        syscalls = _DENIED_SYSCALLS[architecture]
        seccomp_syscall = _SECCOMP_SYSCALLS[architecture]
        audit_arch = _AUDIT_ARCH[architecture]
    except KeyError as exc:
        raise SandboxError(
            f"seccomp syscall policy is not defined for {architecture}"
        ) from exc

    # x32 syscall numbers share x86_64's table with __X32_SYSCALL_BIT set.
    if architecture in {"x86_64", "amd64"}:
        syscalls = tuple(sorted(set(syscalls) | {number | 0x40000000 for number in syscalls}))

    # Reject alternate syscall ABIs before checking syscall numbers, so a
    # compat ABI cannot bypass the network-denial list.
    instructions = [
        _SockFilter(_BPF_LD_W_ABS, 0, 0, 4),
        _SockFilter(_BPF_JMP_JEQ_K, 1, 0, audit_arch),
        _SockFilter(_BPF_RET_K, 0, 0, _SECCOMP_RET_KILL_PROCESS),
        _SockFilter(_BPF_LD_W_ABS, 0, 0, 0),
    ]
    for number in syscalls:
        instructions.append(_SockFilter(_BPF_JMP_JEQ_K, 0, 1, number))
        instructions.append(_SockFilter(_BPF_RET_K, 0, 0, _SECCOMP_RET_ERRNO | 1))
    instructions.append(_SockFilter(_BPF_RET_K, 0, 0, _SECCOMP_RET_ALLOW))
    filters = (_SockFilter * len(instructions))(*instructions)
    program = _SockFprog(
        len=len(instructions),
        filter=ctypes.cast(filters, ctypes.POINTER(_SockFilter)),
    )
    # Landlock setup has already applied PR_SET_NO_NEW_PRIVS, required by
    # unprivileged seccomp filters. No syscall may create/use network sockets.
    if synchronize_threads:
        result = _syscall(
            seccomp_syscall,
            _SECCOMP_SET_MODE_FILTER,
            _SECCOMP_FILTER_FLAG_TSYNC,
            ctypes.byref(program),
        )
        if result > 0:
            raise SandboxError(
                f"seccomp TSYNC could not synchronize thread id {result}"
            )
    else:
        result = _syscall(
            _PR_SET_SECCOMP,
            _SECCOMP_MODE_FILTER,
            ctypes.byref(program),
            0,
            0,
        )
    if result != 0:
        err = ctypes.get_errno()
        raise SandboxError(f"seccomp filter failed: {os.strerror(err)}")


def _apply_unix_limits(policy: SandboxPolicy) -> None:
    if resource is None:
        raise SandboxError("POSIX resource limits are unavailable on this platform")
    limits = (
        ("RLIMIT_CPU", policy.max_cpu_seconds),
        ("RLIMIT_FSIZE", policy.max_file_size),
        ("RLIMIT_NOFILE", policy.max_open_files),
        ("RLIMIT_NPROC", policy.max_processes),
        ("RLIMIT_AS", policy.max_address_space),
    )
    for name, value in limits:
        resource_id = getattr(resource, name, None)
        if resource_id is None:
            continue
        try:
            resource.setrlimit(resource_id, (value, value))
        except (OSError, ValueError) as exc:
            raise SandboxError(f"{name} limit failed: {exc}") from exc
    core_limit = getattr(resource, "RLIMIT_CORE", None)
    if core_limit is not None:
        resource.setrlimit(core_limit, (0, 0))


def _apply_windows_job_limits(policy: SandboxPolicy) -> None:
    # This is intentionally limited to a Job Object boundary. Windows
    # filesystem/network isolation requires AppContainer/LPAC at process
    # creation time and cannot be retrofitted safely into an already-running
    # multiprocessing child.
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise SandboxError(
            f"CreateJobObjectW failed: {ctypes.get_last_error()}"
        )

    JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
    JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200

    class BasicLimitInfo(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", ctypes.c_uint32),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.c_uint32),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", ctypes.c_uint32),
            ("SchedulingClass", ctypes.c_uint32),
        ]

    class ExtendedLimitInfo(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BasicLimitInfo),
            ("IoInfo", ctypes.c_uint64 * 6),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    limits = ExtendedLimitInfo()
    limits.BasicLimitInformation.LimitFlags = (
        JOB_OBJECT_LIMIT_ACTIVE_PROCESS
        | JOB_OBJECT_LIMIT_PROCESS_MEMORY
        | JOB_OBJECT_LIMIT_JOB_MEMORY
        | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    )
    limits.BasicLimitInformation.ActiveProcessLimit = policy.max_processes
    limits.ProcessMemoryLimit = policy.max_address_space
    limits.JobMemoryLimit = policy.max_address_space

    JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
    if not kernel32.SetInformationJobObject(
        job,
        JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
        ctypes.byref(limits),
        ctypes.sizeof(limits),
    ):
        err = ctypes.get_last_error()
        kernel32.CloseHandle(job)
        raise SandboxError(f"SetInformationJobObject failed: {err}")

    if not kernel32.AssignProcessToJobObject(job, kernel32.GetCurrentProcess()):
        err = ctypes.get_last_error()
        kernel32.CloseHandle(job)
        raise SandboxError(f"AssignProcessToJobObject failed: {err}")

    # Keep the job handle alive for the lifetime of the worker.
    global _WINDOWS_JOB_HANDLE
    _WINDOWS_JOB_HANDLE = job


def apply_native_core_sandbox(
    core_path: Path,
    content_path: Path,
    policy: SandboxPolicy | None = None,
) -> dict[str, object]:
    """Apply restrictions before native loading.

    Strict mode is fail-closed. An explicit development override may be used
    only by setting GAME_EMULATOR_ALLOW_UNSANDBOXED_CORE=1.
    """
    policy = policy or SandboxPolicy()
    core_path = Path(core_path).resolve(strict=True)
    content_path = Path(content_path).resolve(strict=True)
    read_only_paths: list[Path] = []
    for raw_path in policy.read_only_paths:
        candidate = Path(raw_path).expanduser()
        if candidate.is_symlink():
            raise SandboxError(f"additional read-only path may not be a symlink: {candidate}")
        resolved = candidate.resolve(strict=True)
        if not resolved.is_file() and not resolved.is_dir():
            raise SandboxError(f"additional read-only path is not a file or directory: {resolved}")
        read_only_paths.append(resolved)

    if os.environ.get("GAME_EMULATOR_ALLOW_UNSANDBOXED_CORE") == "1":
        if policy.strict:
            raise SandboxError(
                "strict native-core sandbox cannot be bypassed by the development override"
            )
        return {"platform": platform.system(), "strict": False, "override": True}

    system = platform.system()
    _apply_unix_limits(policy) if system in {"Linux", "Darwin"} else None

    if system == "Linux":
        abi = _apply_linux_landlock(core_path, content_path, tuple(read_only_paths))
        _apply_linux_network_seccomp()
        return {
            "platform": system,
            "strict": True,
            "landlock": True,
            "landlock_abi": abi,
            "network": "socket_syscalls_denied_by_process_wide_seccomp_and_tcp_by_landlock",
            "udp_restricted_by_landlock": abi >= 10,
            "scoped_abstract_unix_sockets": abi >= 6,
            "scoped_signals": abi >= 6,
            "seccomp_network_filter": True,
        }
    if system == "Windows":
        _apply_windows_job_limits(policy)
        if policy.strict:
            raise SandboxError(
                "Windows strict mode requires launch-time AppContainer/LPAC; "
                "Job Objects alone are not a filesystem/network sandbox"
            )
        return {"platform": system, "strict": False, "job_object": True}
    if system == "Darwin":
        if policy.strict:
            raise SandboxError(
                "macOS strict mode requires a launch-time Seatbelt/App Sandbox wrapper"
            )
        return {"platform": system, "strict": False}

    if policy.strict:
        raise SandboxError(f"No strict native-core sandbox is implemented for {system}")
    return {"platform": system, "strict": False}


_WINDOWS_JOB_HANDLE = None

"""Deterministic, legal hybrid-game composition primitives.

A hybrid project composes *runtime outputs and declared adapters*, not arbitrary
console machine code. Each source is a local/authorized artifact already known
to the library. A profile explicitly declares how inputs and frame outputs are
combined. Unknown transformations fail closed.

This is the first creator-layer seam: two independently sandboxed runtimes can
be driven by one normalized input stream and their video outputs can be
composed into a new presentation. Later adapters can add save-state, asset,
memory, or game-specific transformation support when a backend proves it.
"""
from dataclasses import dataclass, field
from typing import Literal


BlendMode = Literal["side_by_side", "overlay", "picture_in_picture"]


@dataclass(frozen=True)
class RuntimeSource:
    source_id: str
    library_id: str
    backend_id: str
    system: str


@dataclass(frozen=True)
class HybridProfile:
    name: str
    sources: tuple[RuntimeSource, ...]
    blend_mode: BlendMode = "side_by_side"
    input_routes: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("hybrid profile needs a name")
        if len(self.sources) < 2:
            raise ValueError("hybrid profile requires at least two runtime sources")
        ids = [source.source_id for source in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("runtime source ids must be unique")
        if self.blend_mode not in {"side_by_side", "overlay", "picture_in_picture"}:
            raise ValueError(f"unsupported blend mode: {self.blend_mode}")
        known = set(ids)
        for action, routes in self.input_routes.items():
            if not action.strip():
                raise ValueError("input action names cannot be empty")
            unknown = set(routes) - known
            if unknown:
                raise ValueError(
                    f"input route {action!r} references unknown sources: "
                    + ", ".join(sorted(unknown))
                )


def compose_frame(
    frames: dict[str, bytes],
    profile: HybridProfile,
) -> bytes:
    """Compose already-rendered frame payloads for deterministic tests.

    Real video surfaces will be handled by backend adapters. This function
    deliberately does not decode or reinterpret arbitrary game memory.
    """
    profile.validate()
    missing = [source.source_id for source in profile.sources if source.source_id not in frames]
    if missing:
        raise ValueError("missing runtime frame(s): " + ", ".join(missing))

    ordered = [frames[source.source_id] for source in profile.sources]
    if profile.blend_mode == "side_by_side":
        return b"HYBRID:SIDE_BY_SIDE:" + b"|".join(ordered)
    if profile.blend_mode == "overlay":
        return b"HYBRID:OVERLAY:" + b"|".join(ordered)
    return b"HYBRID:PICTURE_IN_PICTURE:" + b"|".join(ordered)

import pytest

from game_emulator.hybrid import HybridProfile, RuntimeSource, compose_frame


def test_first_hybrid_composition_is_explicit_and_deterministic():
    profile = HybridProfile(
        name="first-hybrid",
        sources=(
            RuntimeSource("game_a", "sha256:a", "libretro", "system-a"),
            RuntimeSource("game_b", "sha256:b", "libretro", "system-b"),
        ),
        blend_mode="side_by_side",
        input_routes={"jump": ("game_a", "game_b")},
    )

    assert compose_frame(
        {"game_a": b"A_FRAME", "game_b": b"B_FRAME"},
        profile,
    ) == b"HYBRID:SIDE_BY_SIDE:A_FRAME|B_FRAME"


def test_hybrid_rejects_unknown_input_route():
    profile = HybridProfile(
        name="bad",
        sources=(
            RuntimeSource("game_a", "a", "libretro", "a"),
            RuntimeSource("game_b", "b", "libretro", "b"),
        ),
        input_routes={"attack": ("game_c",)},
    )
    with pytest.raises(ValueError, match="unknown sources"):
        profile.validate()


def test_hybrid_requires_two_sources():
    profile = HybridProfile(
        name="one",
        sources=(RuntimeSource("game_a", "a", "libretro", "a"),),
    )
    with pytest.raises(ValueError, match="at least two"):
        profile.validate()

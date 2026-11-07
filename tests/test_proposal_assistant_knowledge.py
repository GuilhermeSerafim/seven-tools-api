import pytest

from app.modules.ai.knowledge import (
    KNOWLEDGE_DIR,
    PROFILES,
    load_caloni_knowledge,
)


@pytest.fixture(autouse=True)
def setup_db():
    yield


def test_load_full_profile_returns_concatenated_files():
    full = load_caloni_knowledge("full")
    assert len(full) > 50_000  # corpus inteiro tem ~96KB
    assert "objecoes" in full.lower()


def test_load_proposal_assistant_profile_filters_by_prefix():
    body = load_caloni_knowledge("proposal_assistant")
    expected_prefixes = PROFILES["proposal_assistant"]
    assert expected_prefixes is not None
    included_files = [
        f
        for f in sorted(KNOWLEDGE_DIR.glob("*.md"))
        if any(f.name.startswith(prefix + "_") for prefix in expected_prefixes)
    ]
    excluded_files = [
        f
        for f in sorted(KNOWLEDGE_DIR.glob("*.md"))
        if not any(f.name.startswith(prefix + "_") for prefix in expected_prefixes)
    ]
    assert included_files
    assert excluded_files
    assert len(body) > 10_000  # ~50KB de subset
    assert body == "\n\n---\n\n".join(f.read_text(encoding="utf-8") for f in included_files)
    # Deve ser menor que full
    full = load_caloni_knowledge("full")
    assert len(body) < len(full)


@pytest.mark.parametrize(
    ("profile", "expected_prefixes"),
    [
        ("proposal_validation", ["00", "10", "11", "13", "21", "22", "30", "32", "33", "41"]),
        ("lead_qualification", ["00", "10", "11", "13", "20", "21", "31", "33", "40"]),
    ],
)
def test_named_tool_profiles_are_available_and_filtered(profile, expected_prefixes):
    assert PROFILES[profile] == expected_prefixes
    body = load_caloni_knowledge(profile)
    full = load_caloni_knowledge("full")
    assert len(body) > 10_000
    assert len(body) < len(full)


def test_unknown_profile_raises_value_error():
    with pytest.raises(ValueError, match="unknown profile"):
        load_caloni_knowledge("nonexistent")


def test_lru_cache_returns_identical_string():
    first = load_caloni_knowledge("proposal_assistant")
    second = load_caloni_knowledge("proposal_assistant")
    assert first is second  # cache hit, mesma referência

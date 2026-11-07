from functools import lru_cache
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent.parent.parent.parent / "knowledge" / "caloni"

PROFILES: dict[str, list[str] | None] = {
    "full": None,
    "proposal_assistant": ["00", "10", "11", "21", "22", "30", "32", "33", "41"],
    "proposal_validation": ["00", "10", "11", "13", "21", "22", "30", "32", "33", "41"],
    "diagnostic": ["00", "10", "11", "12", "13", "20", "21", "33", "40"],
    "lead_qualification": ["00", "10", "11", "13", "20", "21", "31", "33", "40"],
}


@lru_cache(maxsize=16)
def load_caloni_knowledge(profile: str = "full") -> str:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile: {profile}")
    prefixes = PROFILES[profile]
    md_files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    if prefixes is not None:
        md_files = [f for f in md_files if any(f.name.startswith(p + "_") for p in prefixes)]
    if not md_files:
        raise FileNotFoundError(f"No knowledge files found for profile {profile}")
    return "\n\n---\n\n".join(f.read_text(encoding="utf-8") for f in md_files)

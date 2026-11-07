from __future__ import annotations

from dataclasses import dataclass

from app.models.lead_qualification import LeadAction, LeadQualificationConfig, LeadTier

MATCHING_TIMINGS = {"imediato", "30_dias"}
HIGH_MATCH_VALUES = {"alta"}


@dataclass(frozen=True)
class ScoringResult:
    score: int
    tier: LeadTier
    recommended_action: LeadAction
    matches: dict[str, bool]


def _normalize_discrete_value(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _matches_config_value(value: str, configured_values: list[str]) -> bool:
    normalized_value = value.strip().casefold()
    return any(
        normalized_value == configured_value.strip().casefold()
        for configured_value in configured_values
    )


def validate_config(config: LeadQualificationConfig) -> None:
    weights = (
        config.weight_segment,
        config.weight_company_size,
        config.weight_role,
        config.weight_urgency,
        config.weight_timing,
        config.weight_pain_level,
    )
    if any(weight < 0 for weight in weights):
        raise ValueError("Lead qualification config weights must be non-negative")

    if not (
        0 <= config.bronze_max < config.silver_max < config.gold_max <= 100
    ):
        raise ValueError("Lead qualification config thresholds must be ordered within 0..100")


def score_lead(config: LeadQualificationConfig, lead_data: dict[str, str]) -> ScoringResult:
    validate_config(config)

    normalized_urgency = _normalize_discrete_value(lead_data["urgency"])
    normalized_timing = _normalize_discrete_value(lead_data["timing"])
    normalized_pain_level = _normalize_discrete_value(lead_data["pain_level"])

    matches = {
        "segment": _matches_config_value(lead_data["segment"], config.ideal_segments),
        "company_size": _matches_config_value(
            lead_data["company_size"],
            config.ideal_company_sizes,
        ),
        "contact_role": _matches_config_value(lead_data["contact_role"], config.ideal_roles),
        "urgency": normalized_urgency in HIGH_MATCH_VALUES,
        "timing": normalized_timing in MATCHING_TIMINGS,
        "pain_level": normalized_pain_level in HIGH_MATCH_VALUES,
    }

    score = 0
    if matches["segment"]:
        score += config.weight_segment
    if matches["company_size"]:
        score += config.weight_company_size
    if matches["contact_role"]:
        score += config.weight_role
    if matches["urgency"]:
        score += config.weight_urgency
    if matches["timing"]:
        score += config.weight_timing
    if matches["pain_level"]:
        score += config.weight_pain_level

    score = min(score, 100)

    if score <= config.bronze_max:
        tier = LeadTier.bronze
        recommended_action = config.bronze_action
    elif score <= config.silver_max:
        tier = LeadTier.silver
        recommended_action = config.silver_action
    elif score <= config.gold_max:
        tier = LeadTier.gold
        recommended_action = config.gold_action
    else:
        tier = LeadTier.diamond
        recommended_action = config.diamond_action

    return ScoringResult(
        score=score,
        tier=tier,
        recommended_action=recommended_action,
        matches=matches,
    )

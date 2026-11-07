import uuid
from datetime import datetime, timedelta, timezone

from app.models.lead_qualification import (
    LeadAction,
    LeadQualificationConfig,
    LeadStatus,
    LeadTier,
)
from app.models.session import Session
from app.models.user import ApprovalSource, Role, User, ValidationStatus
from app.utils.security import generate_token, hash_password


def _create_company_member(db, company_id: uuid.UUID, name: str, email: str) -> tuple[User, str]:
    user = User(
        id=uuid.uuid4(),
        company_id=company_id,
        name=name,
        email=email,
        password_hash=hash_password("password123"),
        role=Role.user,
        validation_status=ValidationStatus.approved,
        approval_source=ApprovalSource.seed,
    )
    db.add(user)
    db.flush()

    token = generate_token()
    db.add(
        Session(
            id=uuid.uuid4(),
            user_id=user.id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
    )
    db.commit()
    return user, token


def test_lead_qualification_requires_config(client, auth_headers):
    response = client.post(
        "/api/v1/lead-qualification/leads",
        headers=auth_headers,
        json={
            "contact_name": "Ana Silva",
            "company_name": "ACME Ltda",
            "contact_role": "Founder",
            "segment": "Tech",
            "company_size": "11-50",
            "urgency": "alta",
            "timing": "30 dias",
            "pain_level": "elevado",
            "notes": "Initial outreach",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Configuração de qualificação de leads não configurada."


def test_shared_queue_is_visible_to_company_members(client, db, sample_user, auth_headers):
    config = LeadQualificationConfig(
        id=uuid.uuid4(),
        company_id=sample_user.company_id,
        ideal_segments=["Tech", "SaaS"],
        ideal_company_sizes=["11-50", "51-200"],
        ideal_roles=["Founder", "Head of Growth"],
        weight_segment=20,
        weight_company_size=15,
        weight_role=15,
        weight_urgency=20,
        weight_timing=15,
        weight_pain_level=15,
        bronze_max=25,
        silver_max=50,
        gold_max=75,
        bronze_action=LeadAction.nutrir,
        silver_action=LeadAction.revisar_manualmente,
        gold_action=LeadAction.abordar_agora,
        diamond_action=LeadAction.abordar_agora,
    )
    db.add(config)
    db.commit()

    _, second_token = _create_company_member(
        db,
        sample_user.company_id,
        name="Other User",
        email="other@example.com",
    )
    second_headers = {"Authorization": f"Bearer {second_token}"}

    create_response = client.post(
        "/api/v1/lead-qualification/leads",
        headers=auth_headers,
        json={
            "contact_name": "Joao Pedro",
            "company_name": "Beta Studio",
            "contact_role": "Founder",
            "segment": "Tech",
            "company_size": "11-50",
            "urgency": "media",
            "timing": "45 dias",
            "pain_level": "alto",
            "notes": "Warm inbound lead",
        },
    )

    assert create_response.status_code == 201
    lead_id = create_response.json()["id"]

    list_response = client.get("/api/v1/lead-qualification/leads", headers=second_headers)

    assert list_response.status_code == 200
    data = list_response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["per_page"] == 20
    assert data["items"][0]["id"] == lead_id
    assert data["items"][0]["company_name"] == "Beta Studio"
    assert data["items"][0]["status"] == LeadStatus.novo.value
    assert data["items"][0]["tier"] == LeadTier.silver.value
    assert data["items"][0]["recommended_action"] == LeadAction.revisar_manualmente.value
    assert "scoring_snapshot" in data["items"][0]


def test_create_lead_returns_score_tier_and_action(client, db, sample_user, auth_headers):
    config = LeadQualificationConfig(
        id=uuid.uuid4(),
        company_id=sample_user.company_id,
        ideal_segments=["Tech", "SaaS"],
        ideal_company_sizes=["11-50", "51-200"],
        ideal_roles=["Founder", "Head of Growth"],
        weight_segment=20,
        weight_company_size=15,
        weight_role=15,
        weight_urgency=20,
        weight_timing=15,
        weight_pain_level=15,
        bronze_max=25,
        silver_max=50,
        gold_max=75,
        bronze_action=LeadAction.nutrir,
        silver_action=LeadAction.revisar_manualmente,
        gold_action=LeadAction.abordar_agora,
        diamond_action=LeadAction.abordar_agora,
    )
    db.add(config)
    db.commit()

    response = client.post(
        "/api/v1/lead-qualification/leads",
        headers=auth_headers,
        json={
            "contact_name": "Ana Silva",
            "company_name": "ACME Ltda",
            "contact_role": "Founder",
            "segment": "Tech",
            "company_size": "11-50",
            "urgency": "alta",
            "timing": "imediato",
            "pain_level": "alta",
            "notes": "Hot inbound lead",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["score"] == 100
    assert data["tier"] == LeadTier.diamond.value
    assert data["recommended_action"] == LeadAction.abordar_agora.value
    assert data["status"] == LeadStatus.novo.value
    assert data["scoring_snapshot"]["matches"]["segment"] is True


def test_create_lead_normalizes_human_readable_scoring_inputs(client, db, sample_user, auth_headers):
    config = LeadQualificationConfig(
        id=uuid.uuid4(),
        company_id=sample_user.company_id,
        ideal_segments=["Tech", "SaaS"],
        ideal_company_sizes=["11-50", "51-200"],
        ideal_roles=["Founder", "Head of Growth"],
        weight_segment=20,
        weight_company_size=15,
        weight_role=15,
        weight_urgency=20,
        weight_timing=15,
        weight_pain_level=15,
        bronze_max=25,
        silver_max=50,
        gold_max=75,
        bronze_action=LeadAction.nutrir,
        silver_action=LeadAction.revisar_manualmente,
        gold_action=LeadAction.abordar_agora,
        diamond_action=LeadAction.abordar_agora,
    )
    db.add(config)
    db.commit()

    response = client.post(
        "/api/v1/lead-qualification/leads",
        headers=auth_headers,
        json={
            "contact_name": "Ana Silva",
            "company_name": "ACME Ltda",
            "contact_role": " founder ",
            "segment": "saas",
            "company_size": "11-50",
            "urgency": "Alta",
            "timing": "30 dias",
            "pain_level": "alta",
            "notes": "Hot inbound lead",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["score"] == 100
    assert data["tier"] == LeadTier.diamond.value
    assert data["recommended_action"] == LeadAction.abordar_agora.value


def test_create_lead_caps_score_at_100(client, db, sample_user, auth_headers):
    config = LeadQualificationConfig(
        id=uuid.uuid4(),
        company_id=sample_user.company_id,
        ideal_segments=["Tech"],
        ideal_company_sizes=["11-50"],
        ideal_roles=["Founder"],
        weight_segment=30,
        weight_company_size=20,
        weight_role=20,
        weight_urgency=20,
        weight_timing=20,
        weight_pain_level=20,
        bronze_max=25,
        silver_max=50,
        gold_max=75,
        bronze_action=LeadAction.nutrir,
        silver_action=LeadAction.revisar_manualmente,
        gold_action=LeadAction.abordar_agora,
        diamond_action=LeadAction.abordar_agora,
    )
    db.add(config)
    db.commit()

    response = client.post(
        "/api/v1/lead-qualification/leads",
        headers=auth_headers,
        json={
            "contact_name": "Ana Silva",
            "company_name": "ACME Ltda",
            "contact_role": "Founder",
            "segment": "Tech",
            "company_size": "11-50",
            "urgency": "alta",
            "timing": "imediato",
            "pain_level": "alta",
            "notes": "Hot inbound lead",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["score"] == 100
    assert data["tier"] == LeadTier.diamond.value


def test_put_config_rejects_thresholds_above_100(client, auth_headers):
    response = client.put(
        "/api/v1/lead-qualification/config",
        headers=auth_headers,
        json={
            "ideal_segments": ["Tech"],
            "ideal_company_sizes": ["11-50"],
            "ideal_roles": ["Founder"],
            "weight_segment": 20,
            "weight_company_size": 20,
            "weight_role": 20,
            "weight_urgency": 20,
            "weight_timing": 20,
            "weight_pain_level": 20,
            "bronze_max": 10,
            "silver_max": 60,
            "gold_max": 101,
            "bronze_action": LeadAction.nutrir.value,
            "silver_action": LeadAction.revisar_manualmente.value,
            "gold_action": LeadAction.abordar_agora.value,
            "diamond_action": LeadAction.abordar_agora.value,
        },
    )

    assert response.status_code == 422


def test_put_config_rejects_unordered_thresholds(client, auth_headers):
    response = client.put(
        "/api/v1/lead-qualification/config",
        headers=auth_headers,
        json={
            "ideal_segments": ["Tech"],
            "ideal_company_sizes": ["11-50"],
            "ideal_roles": ["Founder"],
            "weight_segment": 20,
            "weight_company_size": 20,
            "weight_role": 20,
            "weight_urgency": 20,
            "weight_timing": 20,
            "weight_pain_level": 20,
            "bronze_max": 50,
            "silver_max": 40,
            "gold_max": 75,
            "bronze_action": LeadAction.nutrir.value,
            "silver_action": LeadAction.revisar_manualmente.value,
            "gold_action": LeadAction.abordar_agora.value,
            "diamond_action": LeadAction.abordar_agora.value,
        },
    )

    assert response.status_code == 422

from datetime import datetime, timezone

import pytest

from app.models.company import Company
from app.modules.clickup.service import fetch_clickup_companies
from app.modules.companies.service import sync_clickup_directory


def test_registration_options_returns_only_clickup_companies_sorted(client, db):
    clickup_companies = [
        Company(name="Zeta Labs", source="clickup", clickup_task_id="t1"),
        Company(name="alpha studio", source="clickup", clickup_task_id="t2"),
        Company(name="Beta Works", source="clickup", clickup_task_id="t3"),
    ]
    manual_companies = [
        Company(name="Manual Corp", source="manual"),
        Company(name="Test Inc"),
    ]
    db.add_all(clickup_companies + manual_companies)
    db.commit()
    for company in clickup_companies:
        db.refresh(company)

    response = client.get("/api/v1/companies/registration-options")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"id": str(clickup_companies[1].id), "name": "alpha studio"},
            {"id": str(clickup_companies[2].id), "name": "Beta Works"},
            {"id": str(clickup_companies[0].id), "name": "Zeta Labs"},
        ]
    }


def test_registration_options_syncs_clickup_directory_when_empty(client, db, monkeypatch):
    monkeypatch.setattr(
        "app.modules.companies.service.fetch_clickup_companies",
        lambda: [
            {
                "clickup_task_id": "task-1",
                "name": "Zeta Labs",
                "contact_email": "CONTATO@ZETA.COM",
                "partner_1_name": "Alice",
                "partner_2_name": None,
                "has_contract": True,
                "clickup_status": "active",
                "clickup_tags": ["vip"],
            },
            {
                "clickup_task_id": "task-2",
                "name": "Beta Works",
                "contact_email": "SALES@BETA.COM",
                "partner_1_name": "Carol",
                "partner_2_name": None,
                "has_contract": False,
                "clickup_status": "inactive",
                "clickup_tags": ["trial"],
            },
        ],
    )

    response = client.get("/api/v1/companies/registration-options")
    beta_company = db.query(Company).filter(Company.clickup_task_id == "task-2").one()
    zeta_company = db.query(Company).filter(Company.clickup_task_id == "task-1").one()

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"id": str(beta_company.id), "name": "Beta Works"},
            {"id": str(zeta_company.id), "name": "Zeta Labs"},
        ]
    }


def test_registration_options_returns_clear_error_when_clickup_env_missing(client, monkeypatch):
    monkeypatch.setattr("app.modules.clickup.service.settings.clickup_api_token", "")
    monkeypatch.setattr("app.modules.clickup.service.settings.clickup_clients_list_id", "")

    response = client.get("/api/v1/companies/registration-options")

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "detail": (
                "Integracao ClickUp nao configurada. Defina CLICKUP_API_TOKEN e "
                "CLICKUP_CLIENTS_LIST_ID no ambiente da API."
            ),
            "code": "CLICKUP_CONFIG_MISSING",
            "missing_envs": ["CLICKUP_API_TOKEN", "CLICKUP_CLIENTS_LIST_ID"],
        }
    }


def test_fetch_clickup_companies_requires_clickup_env(monkeypatch):
    class FailingClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("ClickUp should not be called without required envs.")

    monkeypatch.setattr("app.modules.clickup.service.httpx.Client", FailingClient)
    monkeypatch.setattr("app.modules.clickup.service.settings.clickup_api_token", "")
    monkeypatch.setattr("app.modules.clickup.service.settings.clickup_clients_list_id", "")

    with pytest.raises(RuntimeError, match="CLICKUP_API_TOKEN.*CLICKUP_CLIENTS_LIST_ID"):
        fetch_clickup_companies()


def test_fetch_clickup_companies_paginates_and_normalizes(monkeypatch):
    payloads = {
        0: {
            "tasks": [
                {
                    "id": "task-1",
                    "name": "Zeta Labs",
                    "status": {"status": "active"},
                    "tags": [{"name": "vip"}],
                    "custom_fields": [
                        {"name": "📩 e-mail", "value": "  CONTATO@ZETA.COM "},
                        {"name": "🙋 Socio 1", "value": "Alice"},
                        {"name": "🙋‍♂️ Socio 2", "value": "Bob"},
                        {"name": "📝 Contrato", "value": "Assinado"},
                    ],
                }
            ],
            "last_page": False,
        },
        1: {
            "tasks": [
                {
                    "id": "task-2",
                    "name": "Beta Works",
                    "status": {"status": "inactive"},
                    "tags": [{"name": "trial"}, {"name": "b2b"}],
                    "custom_fields": [
                        {"name": "📩 e-mail", "value": " SALES@BETA.COM"},
                        {"name": "🙋 Socio 1", "value": "Carol"},
                        {"name": "📝 Contrato", "value": ""},
                    ],
                }
            ],
            "last_page": True,
        },
    }
    calls = []

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url, headers=None, params=None):
            calls.append({"url": url, "headers": headers, "params": params})
            return FakeResponse(payloads[params["page"]])

    monkeypatch.setattr("app.modules.clickup.service.httpx.Client", FakeClient)
    monkeypatch.setattr("app.modules.clickup.service.settings.clickup_api_token", "token-test")
    monkeypatch.setattr("app.modules.clickup.service.settings.clickup_clients_list_id", "901325270216")

    companies = fetch_clickup_companies()

    assert [call["params"]["page"] for call in calls] == [0, 1]
    assert all(call["params"]["include_closed"] == "true" for call in calls)
    assert all(call["params"]["include_timl"] == "true" for call in calls)
    assert companies == [
        {
            "clickup_task_id": "task-1",
            "name": "Zeta Labs",
            "contact_email": "contato@zeta.com",
            "partner_1_name": "Alice",
            "partner_2_name": "Bob",
            "has_contract": True,
            "clickup_status": "active",
            "clickup_tags": ["vip"],
        },
        {
            "clickup_task_id": "task-2",
            "name": "Beta Works",
            "contact_email": "sales@beta.com",
            "partner_1_name": "Carol",
            "partner_2_name": None,
            "has_contract": False,
            "clickup_status": "inactive",
            "clickup_tags": ["trial", "b2b"],
        },
    ]


def test_sync_clickup_directory_upserts_and_updates_last_synced_at(db, monkeypatch):
    existing = Company(
        name="Old Name",
        source="manual",
        clickup_task_id="task-1",
        contact_email="legacy@example.com",
        partner_1_name="Legacy Partner",
        has_contract=False,
        clickup_status="old-status",
        clickup_tags=["legacy"],
        last_synced_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    db.add(existing)
    db.commit()
    db.refresh(existing)
    original_last_synced_at = existing.last_synced_at

    monkeypatch.setattr(
        "app.modules.companies.service.fetch_clickup_companies",
        lambda: [
            {
                "clickup_task_id": "task-1",
                "name": "Updated Name",
                "contact_email": "  UPDATED@EXAMPLE.COM ",
                "partner_1_name": "Alice",
                "partner_2_name": "Bob",
                "has_contract": True,
                "clickup_status": "active",
                "clickup_tags": ["vip"],
            },
            {
                "clickup_task_id": "task-2",
                "name": "New Company",
                "contact_email": " NEW@EXAMPLE.COM ",
                "partner_1_name": "Carol",
                "partner_2_name": None,
                "has_contract": False,
                "clickup_status": "prospect",
                "clickup_tags": ["new"],
            },
        ],
    )

    synced_count = sync_clickup_directory(db)
    db.refresh(existing)
    created = db.query(Company).filter(Company.clickup_task_id == "task-2").one()

    assert synced_count == 2
    assert existing.name == "Updated Name"
    assert existing.source == "clickup"
    assert existing.contact_email == "updated@example.com"
    assert existing.partner_1_name == "Alice"
    assert existing.partner_2_name == "Bob"
    assert existing.has_contract is True
    assert existing.clickup_status == "active"
    assert existing.clickup_tags == ["vip"]
    assert existing.last_synced_at is not None
    assert existing.last_synced_at != original_last_synced_at

    assert created.name == "New Company"
    assert created.source == "clickup"
    assert created.contact_email == "new@example.com"
    assert created.partner_1_name == "Carol"
    assert created.partner_2_name is None
    assert created.has_contract is False
    assert created.clickup_status == "prospect"
    assert created.clickup_tags == ["new"]
    assert created.last_synced_at is not None


def test_sync_clickup_directory_skips_entries_without_clickup_task_id(db, monkeypatch):
    manual_company = Company(
        name="Manual Company",
        source="manual",
        contact_email="manual@example.com",
        partner_1_name="Manual Partner",
        has_contract=False,
    )
    db.add(manual_company)
    db.commit()
    db.refresh(manual_company)
    original_id = manual_company.id

    monkeypatch.setattr(
        "app.modules.companies.service.fetch_clickup_companies",
        lambda: [
            {
                "clickup_task_id": None,
                "name": "Should Be Ignored",
                "contact_email": "ignored@example.com",
                "partner_1_name": "Ignored",
                "partner_2_name": "Ignored Too",
                "has_contract": True,
                "clickup_status": "active",
                "clickup_tags": ["ignored"],
            },
            {
                "clickup_task_id": "   ",
                "name": "Also Ignored",
                "contact_email": "also-ignored@example.com",
                "partner_1_name": "Ignored Again",
                "partner_2_name": None,
                "has_contract": True,
                "clickup_status": "active",
                "clickup_tags": ["ignored-again"],
            },
        ],
    )

    synced_count = sync_clickup_directory(db)
    db.refresh(manual_company)
    companies = db.query(Company).all()

    assert synced_count == 0
    assert len(companies) == 1
    assert manual_company.id == original_id
    assert manual_company.name == "Manual Company"
    assert manual_company.source == "manual"
    assert manual_company.contact_email == "manual@example.com"
    assert manual_company.partner_1_name == "Manual Partner"
    assert manual_company.clickup_task_id is None

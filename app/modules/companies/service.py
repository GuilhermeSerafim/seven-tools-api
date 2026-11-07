from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session as DbSession

from app.models.company import Company
from app.modules.clickup.service import fetch_clickup_companies


def _clean_text(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_email(value) -> str | None:
    text = _clean_text(value)
    if text is None:
        return None
    return text.lower()


def sync_clickup_directory(db: DbSession) -> int:
    synced_at = datetime.now(timezone.utc)
    companies = fetch_clickup_companies()
    synced_count = 0

    for payload in companies:
        clickup_task_id = _clean_text(payload.get("clickup_task_id"))
        if clickup_task_id is None:
            continue

        company = db.query(Company).filter(Company.clickup_task_id == clickup_task_id).first()

        if company is None:
            company = Company(clickup_task_id=clickup_task_id)
            db.add(company)

        company.name = _clean_text(payload.get("name"))
        company.source = "clickup"
        company.contact_email = _normalize_email(payload.get("contact_email"))
        company.partner_1_name = _clean_text(payload.get("partner_1_name"))
        company.partner_2_name = _clean_text(payload.get("partner_2_name"))
        company.has_contract = bool(payload.get("has_contract"))
        company.clickup_status = _clean_text(payload.get("clickup_status"))
        company.clickup_tags = payload.get("clickup_tags")
        company.last_synced_at = synced_at
        synced_count += 1

    db.commit()
    return synced_count


def list_registration_companies(db: DbSession) -> list[Company]:
    return (
        db.query(Company)
        .filter(Company.source == "clickup")
        .order_by(func.lower(Company.name), Company.name)
        .all()
    )


def list_registration_companies_with_sync(db: DbSession) -> list[Company]:
    companies = list_registration_companies(db)
    if companies:
        return companies

    sync_clickup_directory(db)
    return list_registration_companies(db)

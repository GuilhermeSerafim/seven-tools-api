import unicodedata

import httpx

from app.config import settings

CLICKUP_API_BASE_URL = "https://api.clickup.com/api/v2"
CLICKUP_CONFIG_MESSAGE = (
    "Integracao ClickUp nao configurada. Defina CLICKUP_API_TOKEN e "
    "CLICKUP_CLIENTS_LIST_ID no ambiente da API."
)


class ClickupConfigurationError(RuntimeError):
    def __init__(self, missing_envs: list[str]):
        self.missing_envs = missing_envs
        super().__init__(CLICKUP_CONFIG_MESSAGE)


class ClickupFetchError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


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


def _normalize_field_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = normalized.lower().replace("-", " ")
    normalized = "".join(char if char.isalnum() or char.isspace() else " " for char in normalized)
    return " ".join(normalized.split())


def _extract_string(value) -> str | None:
    if isinstance(value, dict):
        for key in ("value", "label", "name", "text"):
            candidate = value.get(key)
            if candidate is not None:
                return _extract_string(candidate)
        return None
    return _clean_text(value)


def _has_contract(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)

    text = _extract_string(value)
    if text is None:
        return False

    normalized = _normalize_field_name(text)
    return normalized in {"sim", "yes", "true", "signed", "1", "ok"} or "assin" in normalized


def _extract_custom_fields(task: dict) -> dict[str, object]:
    fields = {}
    for field in task.get("custom_fields", []):
        name = field.get("name")
        if not name:
            continue
        fields[_normalize_field_name(name)] = field.get("value")
    return fields


def _extract_status(task: dict) -> str | None:
    status = task.get("status")
    if isinstance(status, dict):
        return _extract_string(status.get("status") or status.get("label") or status.get("type"))
    return _extract_string(status)


def _extract_tags(task: dict) -> list[str] | None:
    names = []
    for tag in task.get("tags", []):
        if isinstance(tag, dict):
            name = _extract_string(tag.get("name"))
        else:
            name = _extract_string(tag)
        if name is not None:
            names.append(name)
    return names or None


def _require_clickup_settings() -> tuple[str, str]:
    api_token = _clean_text(settings.clickup_api_token)
    list_id = _clean_text(settings.clickup_clients_list_id)
    missing_envs = []

    if api_token is None:
        missing_envs.append("CLICKUP_API_TOKEN")
    if list_id is None:
        missing_envs.append("CLICKUP_CLIENTS_LIST_ID")

    if missing_envs:
        raise ClickupConfigurationError(missing_envs)

    return api_token, list_id


def fetch_clickup_companies() -> list[dict]:
    api_token, list_id = _require_clickup_settings()
    url = f"{CLICKUP_API_BASE_URL}/list/{list_id}/task"
    headers = {"Authorization": api_token}

    companies = []
    page = 0

    try:
        with httpx.Client(timeout=30.0) as client:
            while True:
                response = client.get(
                    url,
                    headers=headers,
                    params={
                        "page": page,
                        "include_closed": "true",
                        "include_timl": "true",
                    },
                )
                response.raise_for_status()
                payload = response.json()

                for task in payload.get("tasks", []):
                    custom_fields = _extract_custom_fields(task)
                    email_value = custom_fields.get("e mail") or custom_fields.get("email")
                    companies.append(
                        {
                            "clickup_task_id": _extract_string(task.get("id")),
                            "name": _extract_string(task.get("name")),
                            "contact_email": _normalize_email(_extract_string(email_value)),
                            "partner_1_name": _extract_string(custom_fields.get("socio 1")),
                            "partner_2_name": _extract_string(custom_fields.get("socio 2")),
                            "has_contract": _has_contract(custom_fields.get("contrato")),
                            "clickup_status": _extract_status(task),
                            "clickup_tags": _extract_tags(task),
                        }
                    )

                if payload.get("last_page", True):
                    break
                page += 1
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        raise ClickupFetchError(
            f"ClickUp retornou erro {status_code} ao sincronizar empresas.",
            status_code=status_code,
        ) from exc
    except httpx.HTTPError as exc:
        raise ClickupFetchError("Nao foi possivel conectar ao ClickUp para sincronizar empresas.") from exc

    return companies

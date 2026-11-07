import uuid
from datetime import datetime, timedelta, timezone

from app.models.company import Company
from app.models.session import Session as AuthSession
from app.models.tool_chat import ToolChatSession
from app.models.user import ApprovalSource, User, ValidationStatus
from app.utils.security import generate_token, hash_password


def create_approved_user_headers(db, email: str) -> dict[str, str]:
    company = Company(id=uuid.uuid4(), name=f"Company {email}", segment="Tech", city="Sao Paulo")
    db.add(company)
    db.flush()

    user = User(
        id=uuid.uuid4(),
        company_id=company.id,
        name=f"User {email}",
        email=email,
        password_hash=hash_password("password123"),
        role="user",
        validation_status=ValidationStatus.approved,
        approval_source=ApprovalSource.seed,
    )
    db.add(user)
    db.flush()

    token = generate_token()
    db.add(
        AuthSession(
            id=uuid.uuid4(),
            user_id=user.id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
    )
    db.commit()
    return {"Authorization": f"Bearer {token}"}


def create_session(client, headers, title="Novo chat", tool_slug="proposta-comercial-smart"):
    response = client.post(
        "/api/v1/tool-chat/sessions",
        headers=headers,
        json={"tool_slug": tool_slug, "title": title, "metadata": {"origin": "test"}},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_list_tool_chat_session(client, auth_headers):
    created = create_session(client, auth_headers, title="Proposta Aurora")

    assert created["tool_slug"] == "proposta-comercial-smart"
    assert created["title"] == "Proposta Aurora"
    assert created["metadata"] == {"origin": "test"}
    assert created["archived_at"] is None

    response = client.get(
        "/api/v1/tool-chat/sessions?tool_slug=proposta-comercial-smart",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == created["id"]
    assert data["items"][0]["title"] == "Proposta Aurora"


def assert_utc_timestamp(value: str):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timedelta(0)


def test_tool_chat_timestamps_are_serialized_as_utc(client, auth_headers):
    created = create_session(client, auth_headers, title="Proposta Aurora")
    assert_utc_timestamp(created["created_at"])
    assert_utc_timestamp(created["updated_at"])

    message_response = client.post(
        f"/api/v1/tool-chat/sessions/{created['id']}/messages",
        headers=auth_headers,
        json={"role": "user", "content": "Quero uma proposta para a Clinica Aurora"},
    )
    assert message_response.status_code == 201, message_response.text
    assert_utc_timestamp(message_response.json()["created_at"])

    list_response = client.get(
        "/api/v1/tool-chat/sessions?tool_slug=proposta-comercial-smart",
        headers=auth_headers,
    )
    assert list_response.status_code == 200
    listed = list_response.json()["items"][0]
    assert_utc_timestamp(listed["created_at"])
    assert_utc_timestamp(listed["updated_at"])


def test_list_filters_by_tool_slug_and_search_title(client, auth_headers):
    create_session(client, auth_headers, title="Proposta Aurora", tool_slug="proposta-comercial-smart")
    create_session(client, auth_headers, title="Diagnostico Aurora", tool_slug="diagnostico-comercial-caloni")
    create_session(client, auth_headers, title="Proposta Boreal", tool_slug="proposta-comercial-smart")

    response = client.get(
        "/api/v1/tool-chat/sessions?tool_slug=proposta-comercial-smart&q=aurora",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Proposta Aurora"
    assert data["items"][0]["tool_slug"] == "proposta-comercial-smart"


def test_messages_persist_payload_and_update_session_timestamp(client, auth_headers):
    created = create_session(client, auth_headers)

    session_before_response = client.get(
        f"/api/v1/tool-chat/sessions/{created['id']}",
        headers=auth_headers,
    )
    assert session_before_response.status_code == 200
    session_before = session_before_response.json()

    user_response = client.post(
        f"/api/v1/tool-chat/sessions/{created['id']}/messages",
        headers=auth_headers,
        json={"role": "user", "content": "Quero uma proposta para a Clinica Aurora"},
    )
    assert user_response.status_code == 201, user_response.text
    assert user_response.json()["content"] == "Quero uma proposta para a Clinica Aurora"

    assistant_response = client.post(
        f"/api/v1/tool-chat/sessions/{created['id']}/messages",
        headers=auth_headers,
        json={
            "role": "assistant",
            "content": "Atualizei o rascunho.",
            "payload": {
                "kind": "proposal_draft_patch",
                "patch": {"clientName": "Maria Aurora"},
            },
            "variant": "default",
        },
    )
    assert assistant_response.status_code == 201, assistant_response.text

    messages_response = client.get(
        f"/api/v1/tool-chat/sessions/{created['id']}/messages",
        headers=auth_headers,
    )
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[1]["payload"] == {
        "kind": "proposal_draft_patch",
        "patch": {"clientName": "Maria Aurora"},
    }

    session_after_response = client.get(
        f"/api/v1/tool-chat/sessions/{created['id']}",
        headers=auth_headers,
    )
    assert session_after_response.status_code == 200
    session_after = session_after_response.json()
    assert session_after["title"] == "Quero uma proposta para a Clinica Aurora"
    session_before_updated_at = datetime.fromisoformat(
        session_before["updated_at"].replace("Z", "+00:00")
    )
    session_after_updated_at = datetime.fromisoformat(
        session_after["updated_at"].replace("Z", "+00:00")
    )
    assert session_after_updated_at > session_before_updated_at


def test_patch_session_metadata(client, auth_headers):
    created = create_session(client, auth_headers)

    response = client.patch(
        f"/api/v1/tool-chat/sessions/{created['id']}",
        headers=auth_headers,
        json={"metadata": {"proposal_id": "p_123"}, "title": "Proposta final"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Proposta final"
    assert data["metadata"] == {"origin": "test", "proposal_id": "p_123"}


def test_blank_session_title_falls_back_to_default(client, auth_headers):
    created = create_session(client, auth_headers, title="   ")

    assert created["title"] == "Novo chat"


def test_overlong_session_title_is_rejected(client, auth_headers):
    response = client.post(
        "/api/v1/tool-chat/sessions",
        headers=auth_headers,
        json={
            "tool_slug": "proposta-comercial-smart",
            "title": "a" * 256,
            "metadata": {"origin": "test"},
        },
    )

    assert response.status_code == 422


def test_overlong_session_patch_title_is_rejected(client, auth_headers):
    created = create_session(client, auth_headers)

    response = client.patch(
        f"/api/v1/tool-chat/sessions/{created['id']}",
        headers=auth_headers,
        json={"title": "a" * 256},
    )

    assert response.status_code == 422


def test_overlong_message_variant_is_rejected(client, auth_headers):
    created = create_session(client, auth_headers)

    response = client.post(
        f"/api/v1/tool-chat/sessions/{created['id']}/messages",
        headers=auth_headers,
        json={"role": "assistant", "content": "Rascunho atualizado.", "variant": "a" * 51},
    )

    assert response.status_code == 422


def test_archived_session_is_hidden_from_session_endpoints(client, db, auth_headers):
    created = create_session(client, auth_headers, title="Conversa arquivada")

    session = db.get(ToolChatSession, uuid.UUID(created["id"]))
    session.archived_at = datetime.now(timezone.utc)
    db.add(session)
    db.commit()

    list_response = client.get(
        "/api/v1/tool-chat/sessions?tool_slug=proposta-comercial-smart",
        headers=auth_headers,
    )
    get_response = client.get(
        f"/api/v1/tool-chat/sessions/{created['id']}",
        headers=auth_headers,
    )
    messages_response = client.get(
        f"/api/v1/tool-chat/sessions/{created['id']}/messages",
        headers=auth_headers,
    )

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 0
    assert get_response.status_code == 404
    assert messages_response.status_code == 404


def test_user_cannot_access_other_user_session(client, db, auth_headers):
    other_headers = create_approved_user_headers(db, "other@example.com")
    created = create_session(client, other_headers, title="Conversa privada")

    get_response = client.get(
        f"/api/v1/tool-chat/sessions/{created['id']}",
        headers=auth_headers,
    )
    messages_response = client.get(
        f"/api/v1/tool-chat/sessions/{created['id']}/messages",
        headers=auth_headers,
    )

    assert get_response.status_code == 404
    assert messages_response.status_code == 404


def test_session_detail_and_messages_require_matching_tool_slug(client, auth_headers):
    created = create_session(
        client,
        auth_headers,
        title="Proposta Aurora",
        tool_slug="proposta-comercial-smart",
    )

    get_response = client.get(
        f"/api/v1/tool-chat/sessions/{created['id']}",
        headers=auth_headers,
        params={"tool_slug": "diagnostico-comercial-caloni"},
    )
    messages_response = client.get(
        f"/api/v1/tool-chat/sessions/{created['id']}/messages",
        headers=auth_headers,
        params={"tool_slug": "diagnostico-comercial-caloni"},
    )
    create_message_response = client.post(
        f"/api/v1/tool-chat/sessions/{created['id']}/messages",
        headers=auth_headers,
        params={"tool_slug": "diagnostico-comercial-caloni"},
        json={"role": "user", "content": "Continuar no Raio-X"},
    )

    assert get_response.status_code == 404
    assert messages_response.status_code == 404
    assert create_message_response.status_code == 404


def test_invalid_tool_slug_is_rejected(client, auth_headers):
    response = client.post(
        "/api/v1/tool-chat/sessions",
        headers=auth_headers,
        json={
            "tool_slug": "ferramenta-inexistente",
            "title": "Ferramenta invalida",
            "metadata": {"origin": "test"},
        },
    )

    assert response.status_code == 422
    assert "tool_slug" in response.text or "Unsupported tool_slug" in response.text

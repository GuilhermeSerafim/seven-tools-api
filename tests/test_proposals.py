# seven_tools_api/tests/test_proposals.py
import uuid


def test_create_proposal(client, auth_headers):
    response = client.post("/api/v1/proposals", headers=auth_headers, json={
        "title": "Proposta para Empresa X",
        "client_name": "Maria Silva",
        "client_company": "Empresa X",
        "client_email": "maria@empresax.com",
        "value": "15000",
        "status": "draft",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Proposta para Empresa X"
    assert data["client_name"] == "Maria Silva"
    assert data["status"] == "draft"
    assert "id" in data


def test_list_proposals_empty(client, auth_headers):
    response = client.get("/api/v1/proposals", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["per_page"] == 20


def test_list_proposals_with_pagination(client, auth_headers):
    # Create 3 proposals
    for i in range(3):
        client.post("/api/v1/proposals", headers=auth_headers, json={
            "title": f"Proposta {i}",
            "client_name": f"Client {i}",
        })

    # Page 1 with per_page=2
    response = client.get("/api/v1/proposals?page=1&per_page=2", headers=auth_headers)
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["per_page"] == 2

    # Page 2
    response = client.get("/api/v1/proposals?page=2&per_page=2", headers=auth_headers)
    data = response.json()
    assert len(data["items"]) == 1
    assert data["page"] == 2


def test_get_proposal(client, auth_headers):
    create_resp = client.post("/api/v1/proposals", headers=auth_headers, json={
        "title": "Test Proposal",
        "client_name": "Client A",
    })
    proposal_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/proposals/{proposal_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Test Proposal"


def test_get_proposal_not_found(client, auth_headers):
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/proposals/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


def test_patch_proposal(client, auth_headers):
    create_resp = client.post("/api/v1/proposals", headers=auth_headers, json={
        "title": "Original Title",
        "client_name": "Client A",
    })
    proposal_id = create_resp.json()["id"]

    response = client.patch(f"/api/v1/proposals/{proposal_id}", headers=auth_headers, json={
        "status": "ready",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["title"] == "Original Title"


def test_delete_proposal(client, auth_headers):
    create_resp = client.post("/api/v1/proposals", headers=auth_headers, json={
        "title": "To Delete",
        "client_name": "Client A",
    })
    proposal_id = create_resp.json()["id"]

    response = client.delete(f"/api/v1/proposals/{proposal_id}", headers=auth_headers)
    assert response.status_code == 200

    response = client.get(f"/api/v1/proposals/{proposal_id}", headers=auth_headers)
    assert response.status_code == 404


def test_cannot_access_other_users_proposal(client, db, auth_headers):
    from app.models.proposal import Proposal
    from app.models.user import User
    from app.utils.security import hash_password

    other_user = User(
        id=uuid.uuid4(),
        name="Other",
        email="other@example.com",
        password_hash=hash_password("pass"),
    )
    db.add(other_user)
    db.flush()

    other_proposal = Proposal(
        id=uuid.uuid4(),
        user_id=other_user.id,
        title="Other's Proposal",
        client_name="Private Client",
    )
    db.add(other_proposal)
    db.commit()

    response = client.get(f"/api/v1/proposals/{other_proposal.id}", headers=auth_headers)
    assert response.status_code == 404

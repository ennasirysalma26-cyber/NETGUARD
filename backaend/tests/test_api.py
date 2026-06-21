"""
Tests d'intégration — API NetAdmin
Lancer avec : pytest tests/ -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.models import User, Device

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine_test      = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine_test, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Créer un utilisateur admin de test
    async with TestSessionLocal() as session:
        admin = User(
            username="admin",
            email="admin@test.lan",
            password_hash=hash_password("adminpass"),
            role="admin",
        )
        session.add(admin)
        await session.commit()
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client):
    resp = await client.post("/api/v1/auth/login", json={
        "username": "admin", "password": "adminpass"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ─── AUTH TESTS ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client):
    resp = await client.post("/api/v1/auth/login", json={
        "username": "admin", "password": "adminpass"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token"  in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post("/api/v1/auth/login", json={
        "username": "admin", "password": "wrong"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me(client, auth_headers):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"


@pytest.mark.asyncio
async def test_me_unauthorized(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403  # HTTPBearer returns 403 when no credentials


# ─── DEVICE TESTS ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_device(client, auth_headers):
    resp = await client.post("/api/v1/devices", headers=auth_headers, json={
        "name":       "SW-TEST-01",
        "type":       "Switch",
        "model":      "Cisco Catalyst 2960",
        "ip_address": "10.99.0.1",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "SW-TEST-01"
    assert data["status"] == "Actif"


@pytest.mark.asyncio
async def test_create_device_duplicate_ip(client, auth_headers):
    payload = {"name": "SW-A", "type": "Switch", "ip_address": "10.99.0.2"}
    await client.post("/api/v1/devices", headers=auth_headers, json=payload)
    resp = await client.post("/api/v1/devices", headers=auth_headers, json={
        "name": "SW-B", "type": "Switch", "ip_address": "10.99.0.2"
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_devices(client, auth_headers):
    for i in range(3):
        await client.post("/api/v1/devices", headers=auth_headers, json={
            "name": f"PC-{i:02d}", "type": "Ordinateur", "ip_address": f"192.168.1.{i+10}"
        })
    resp = await client.get("/api/v1/devices", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] == 3


@pytest.mark.asyncio
async def test_update_device(client, auth_headers):
    create = await client.post("/api/v1/devices", headers=auth_headers, json={
        "name": "RT-TEST", "type": "Routeur", "ip_address": "10.50.0.1"
    })
    device_id = create.json()["id"]
    resp = await client.put(f"/api/v1/devices/{device_id}", headers=auth_headers, json={
        "status": "Maintenance"
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "Maintenance"


@pytest.mark.asyncio
async def test_delete_device(client, auth_headers):
    create = await client.post("/api/v1/devices", headers=auth_headers, json={
        "name": "AP-DEL", "type": "AP", "ip_address": "172.16.0.1"
    })
    device_id = create.json()["id"]
    resp = await client.delete(f"/api/v1/devices/{device_id}", headers=auth_headers)
    assert resp.status_code == 200

    get_resp = await client.get(f"/api/v1/devices/{device_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_invalid_ip_format(client, auth_headers):
    resp = await client.post("/api/v1/devices", headers=auth_headers, json={
        "name": "BAD-IP", "type": "Switch", "ip_address": "999.999.999.999"
    })
    assert resp.status_code == 422

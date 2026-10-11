"""System probes and auth gateway behavior (MT-2, SC-1, AP-2, AP-4)."""


def test_healthz_open(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_readyz_open(client):
    assert client.get("/readyz").status_code == 200


def test_root_links(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["links"]["docs"] == "/docs"


def test_missing_auth_rejected(client):
    resp = client.get("/v1/agents")
    assert resp.status_code == 401
    assert resp.json()["title"] == "Unauthorized"


def test_wrong_token_rejected(client):
    resp = client.get(
        "/v1/agents",
        headers={"Authorization": "Bearer wrong", "X-Tenant-ID": "tenant-test-01"},
    )
    assert resp.status_code == 401


def test_missing_tenant_header_rejected(client, auth):
    headers = {k: v for k, v in auth.items() if k != "X-Tenant-ID"}
    resp = client.get("/v1/agents", headers=headers)
    assert resp.status_code == 403


def test_tenant_mismatch_rejected(client, auth):
    headers = dict(auth, **{"X-Tenant-ID": "tenant-other-99"})
    resp = client.get("/v1/agents", headers=headers)
    assert resp.status_code == 403


def test_correlation_id_echoed(client):
    resp = client.get("/healthz", headers={"X-Correlation-ID": "corr-123"})
    assert resp.headers["X-Correlation-ID"] == "corr-123"

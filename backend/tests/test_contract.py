"""Contract test: every route in the app must be in openapi.yaml and vice versa (AP-8)."""

from pathlib import Path

import yaml


def _spec():
    root = Path(__file__).resolve().parent.parent.parent
    return yaml.safe_load((root / "openapi.yaml").read_text())


def test_openapi_valid_contract():
    spec = _spec()
    assert spec["openapi"].startswith("3.")
    assert spec["info"]["title"] == "Services AI Platform API"
    for path, ops in spec["paths"].items():
        assert ops, f"{path} has no operations"


def test_app_routes_match_spec():
    import os

    os.environ.setdefault("AUTH_MODE", "dev")
    os.environ.setdefault("DEV_TOKEN", "x")
    os.environ.setdefault("DEV_TENANT", "t")
    from app.config import Settings
    from app.factory import create_app

    settings = Settings(
        env="local",
        auth_mode="dev",
        dev_token="x",
        dev_tenant="t",
        audit_log_path="/tmp/audit.jsonl",
    )
    app = create_app(settings)
    app.openapi()
    spec_paths = set(_spec()["paths"].keys())
    app_paths: set[str] = set()
    for route in app.routes:
        if type(route).__name__ == "_IncludedRouter":
            prefix = route.include_context.prefix or ""
            for inner in route.original_router.routes:
                app_paths.add((prefix + inner.path).replace("//", "/"))
        elif hasattr(route, "path") and hasattr(route, "methods"):
            app_paths.add(route.path)
    app_paths -= {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
    assert app_paths == spec_paths, (
        f"drift: app-only={app_paths - spec_paths} spec-only={spec_paths - app_paths}"
    )

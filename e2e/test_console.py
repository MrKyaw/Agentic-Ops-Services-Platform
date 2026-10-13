"""Browser journeys against the composed console (Playwright, system Chrome).

Requires the compose stack with seeded tenant-local-01 and DEV_TOKEN set.
Skips cleanly when the stack is unreachable.
"""

import os

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

WEB_URL = os.environ.get("E2E_WEB_URL", "http://localhost:4201")
API_URL = os.environ.get("E2E_API_URL", "http://localhost:8000")
API_TOKEN = os.environ.get("E2E_TOKEN", "")
TENANT = os.environ.get("E2E_TENANT", "tenant-local-01")

pytestmark = pytest.mark.skipif(not API_TOKEN, reason="E2E_TOKEN unset")


@pytest.fixture(scope="module", autouse=True)
def warmup():
    """Cold containers need model downloads + lazy init; warm them before timing-sensitive tests."""
    import json
    import urllib.request

    base = API_URL
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "X-Tenant-ID": TENANT,
        "Content-Type": "application/json",
    }
    for path, body in (
        ("/healthz", None),
        ("/v1/kb/query", {"kb_id": "kb-policy", "query": "warmup", "top_k": 1}),
    ):
        try:
            req = urllib.request.Request(
                base + path,
                data=json.dumps(body).encode() if body else None,
                headers=headers,
                method="POST" if body else "GET",
            )
            urllib.request.urlopen(req, timeout=180)
        except Exception:
            pass


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        launched = playwright.chromium.launch(channel="chrome", headless=True)
        yield launched
        launched.close()


@pytest.fixture()
def page(browser: Browser):
    context = browser.new_context()
    context.add_init_script(
        f"localStorage.setItem('sap.token', '{API_TOKEN}'); localStorage.setItem('sap.tenant', '{TENANT}');"
    )
    sheet = context.new_page()
    yield sheet
    context.close()


def test_login_redirects_when_disconnected(browser: Browser):
    context = browser.new_context()
    sheet = context.new_page()
    sheet.goto(f"{WEB_URL}/runs")
    sheet.wait_for_url("**/login", timeout=10000)
    context.close()


def test_run_journey_with_trace(page: Page):
    page.goto(f"{WEB_URL}/runs")
    page.get_by_placeholder("Ask something…").fill("Why was invoice 88123 flagged?")
    page.get_by_role("button", name="Submit").click()
    page.wait_for_selector("text=succeeded", timeout=120000)
    links = page.locator("ul li a")
    assert links.count() >= 1
    links.first.click()
    page.wait_for_selector("text=Steps", timeout=60000)
    page.wait_for_selector("text=intent", timeout=60000)


def test_approval_journey(page: Page):
    page.goto(f"{WEB_URL}/runs")
    page.get_by_placeholder("Ask something…").fill(
        "Please open a case for invoice 1024"
    )
    page.get_by_role("button", name="Submit").click()
    page.wait_for_selector("text=waiting_approval", timeout=120000)
    page.goto(f"{WEB_URL}/approvals")
    page.wait_for_selector("text=case.create", timeout=60000)
    page.get_by_role("button", name="Approve").first.click()
    page.wait_for_selector("text=approved", timeout=60000)


def test_playground_grounded(page: Page):
    page.goto(f"{WEB_URL}/playground")
    page.get_by_placeholder("Ask a grounded question…").fill(
        "What are the themes across escalation policies?"
    )
    page.get_by_role("button", name="Submit").click()
    page.wait_for_selector("text=Sources", timeout=120000)

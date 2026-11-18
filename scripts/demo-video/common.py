"""Shared helpers: the URLs of the apps, the OpenShift OAuth login, English + light theme for the frontend."""
import os
import re

APPS = os.environ["APPS_DOMAIN"]                       # the cluster's apps domain: apps.<cluster>.<base domain>
IDP_NAME = os.environ.get("IDP_NAME", "local-users")   # the OpenShift identity provider to log in with
FRONTEND = f"https://frontend-multi-agents.{APPS}"
RHOAI = f"https://rh-ai.{APPS}"
CONSOLE = f"https://console-openshift-console.{APPS}"
W, H = 1920, 1080

INIT_JS = """
try {
  localStorage.setItem('app-locale','en'); localStorage.setItem('app-theme','light');
  localStorage.setItem('nav-collapsed','false'); localStorage.setItem('chat-a2a-open','true');
  localStorage.setItem('chat-left-open','true'); localStorage.removeItem('chat-last-session-id');
} catch (e) {}
"""


def new_context(browser, **kw):
    ctx = browser.new_context(viewport={"width": W, "height": H}, locale="en-US", color_scheme="light",
                              ignore_https_errors=True, **kw)
    ctx.add_init_script(INIT_JS)
    return ctx


def settle(page, ms=10_000):
    try:
        page.wait_for_load_state("networkidle", timeout=ms)
    except Exception:
        pass


def _visible(loc):
    return loc.count() > 0 and loc.first.is_visible()


def oauth_login(page, user, password):
    """Walks the OpenShift login (proxy button, identity provider, credentials, consent) until the app is back
    (two checks in a row, as the console redirects to the login by JavaScript after its first load)."""
    stable = 0
    for _ in range(30):
        settle(page)
        url = page.url
        proxy_btn = page.get_by_role("button", name=re.compile(r"log ?in with openshift", re.I))
        idp = page.get_by_role("link", name=re.compile(re.escape(IDP_NAME), re.I))
        allow = page.get_by_role("button", name=re.compile(r"allow selected permissions", re.I))
        if _visible(proxy_btn):
            proxy_btn.first.click()
        elif _visible(idp):
            idp.first.click()
        elif page.locator("#inputUsername").count():
            page.fill("#inputUsername", user)
            page.fill("#inputPassword", password)
            page.locator("button[type=submit]").click()
            settle(page)
            if page.get_by_text(re.compile(r"invalid (login|username) or password", re.I)).count():
                raise SystemExit(f"LOGIN FAILED for {user}")
        elif _visible(allow):
            allow.first.click()
        elif "oauth-openshift" in url or "/oauth/" in url or "/auth/login" in url:
            page.wait_for_timeout(1000)          # still redirecting
        else:
            stable += 1
            if stable >= 2:
                return
            page.wait_for_timeout(2500)
            continue
        stable = 0
    raise SystemExit(f"LOGIN LOOP for {user}: stuck on {page.url}")


def dismiss_dialogs(page):
    """Welcome / guided-tour modals of the console and RHOAI."""
    for _ in range(3):
        dialog = page.get_by_role("dialog")
        if not _visible(dialog):
            return
        btn = dialog.get_by_role("button", name=re.compile(r"^(skip tour|close|got it|not now|cancel)$", re.I))
        if not _visible(btn):
            return
        btn.last.click()
        page.wait_for_timeout(600)


def close_rhoai_welcome(page):
    """The 'Welcome to OpenShift AI 3.5!' tour modal."""
    dialog = page.get_by_role("dialog")
    if _visible(dialog):
        close = dialog.get_by_role("button", name=re.compile(r"^close$", re.I))
        if _visible(close):
            close.last.click()
            page.wait_for_timeout(500)

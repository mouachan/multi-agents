"""Records the demo: one video per scene (one browser page each), plus marks.json (seconds since each page
opened, used by montage.py to cut the clips).

Side effects on the demo: it starts 3 real processings (CLAIM, TENDER, POSTAL must be pending), one chat turn,
one question to an agent and one human decision (Admin > Reset database restores the cases). The frontend
scenes run as FRONTEND_USER, the OpenShift AI / MLflow / console scenes as PLATFORM_USER. Logins happen off
camera. SCENES=... records only some scenes (comma list, see the main block).
"""
import json
import os
import re
import time
import traceback

from playwright.sync_api import sync_playwright

from common import (CONSOLE, FRONTEND, RHOAI, H, W, close_rhoai_welcome, dismiss_dialogs, new_context,
                    oauth_login, settle)

OUT = os.environ.get("OUT", "/work/out/rec")
os.makedirs(OUT, exist_ok=True)
CASES = {
    "claims": os.environ.get("CLAIM", "CLM-2024-0030"),
    "tenders": os.environ.get("TENDER", "AO-2026-0071"),
    "postal": os.environ.get("POSTAL", "RECL-2025-0028"),
}
CASE_DOMAINS = os.environ.get("CASE_DOMAINS", "claims,tenders,postal").split(",")
CHAT_PROMPT = os.environ.get("CHAT_PROMPT", "Compute the payout of claim CLM-2024-0020")
SCENES = os.environ.get("SCENES", "cases,maasmodels,maassubs,agentdetail,mcpdetail,home,chat,admin,console,"
                        "sandbox,results,review,mlflow").split(",")
MLFLOW_URL = os.environ.get("MLFLOW_URL")             # to re-record the MLflow scene alone
FRONTEND_USER = os.environ.get("FRONTEND_USER", "demo-admin")   # a user of the admin profile (sees all domains)
PLATFORM_USER = os.environ.get("PLATFORM_USER", "")             # a cluster user who sees OpenShift AI, MLflow, the console
# Admin page: user names left readable (prefixes); the others are blurred on screen
KEEP_USERS = [u for u in [PLATFORM_USER, *os.environ.get("KEEP_USERS", "demo-").split(",")] if u]

CURSOR_JS = """
(() => {
  if (window.top !== window.self) return;        // never in iframes (the PDF viewer): no stale copies
  let c = null, x = -100, y = -100, sc = 1;
  const upd = () => { if (c) c.style.transform = `translate(${x}px,${y}px) scale(${sc})`; };
  const add = () => {
    if (document.getElementById('__demo_cursor')) return;
    c = document.createElement('div'); c.id = '__demo_cursor';
    c.style.cssText = 'position:fixed;left:0;top:0;width:24px;height:24px;margin:-12px 0 0 -12px;border-radius:50%;'
      + 'background:rgba(238,0,0,.30);border:2px solid rgba(238,0,0,.95);box-shadow:0 0 0 4px rgba(238,0,0,.12);'
      + 'z-index:2147483647;pointer-events:none;transition:transform .05s linear;transform:translate(-100px,-100px)';
    document.documentElement.appendChild(c); upd();
  };
  window.__demoCursor = (nx, ny, ns) => { x = nx; y = ny; if (ns !== undefined) sc = ns; add(); upd(); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', add); else add();
})();
"""

marks = {}
info = {}


class Scene:
    def __init__(self, ctx, name):
        self.name = name
        self.page = ctx.new_page()
        self.t0 = time.time()
        marks[name] = {"marks": {}, "video": os.path.relpath(self.page.video.path(), OUT)}

    def mark(self, label):
        t = round(time.time() - self.t0, 2)
        marks[self.name]["marks"][label] = t
        print(f"[{self.name}] {label} @ {t}s", flush=True)

    def shot(self, label):
        self.page.screenshot(path=f"{OUT}/{self.name}-{label}.png")

    def close(self):
        self.page.close()


# ---------- gestures (the fake cursor follows the real mouse)

POS = {}


def cursor(page, x, y, scale=None):
    try:
        page.evaluate("([x, y, s]) => window.__demoCursor && window.__demoCursor(x, y, s === null ? undefined : s)", [x, y, scale])
    except Exception:
        pass


def move_to(page, x, y, steps=28):
    x0, y0 = POS.get(id(page), (x, y))
    for i in range(1, steps + 1):
        px, py = x0 + (x - x0) * i / steps, y0 + (y - y0) * i / steps
        page.mouse.move(px, py)
        cursor(page, px, py)
    POS[id(page)] = (x, y)


def glide(page, loc, steps=28, pause=300):
    loc.scroll_into_view_if_needed()
    b = loc.bounding_box()
    move_to(page, b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, steps=steps)
    page.wait_for_timeout(pause)


def click(page, loc, **kw):
    glide(page, loc, **kw)
    x, y = POS[id(page)]
    cursor(page, x, y, 0.65)
    loc.click()
    page.wait_for_timeout(120)
    cursor(page, x, y, 1)


def type_in(page, loc, text, delay=65):
    click(page, loc)
    loc.press_sequentially(text, delay=delay)


def wheel(page, dy, x=W * 0.55, y=H * 0.6, steps=24, pause=45):
    move_to(page, x, y, steps=8)
    for _ in range(steps):
        page.mouse.wheel(0, dy / steps)
        page.wait_for_timeout(pause)


def safe(fn):
    """A failed scene is logged with a screenshot, the others still run."""
    def run(*a, **kw):
        try:
            return fn(*a, **kw)
        except Exception:
            print(f"!! scene {fn.__name__} failed:\n{traceback.format_exc()}", flush=True)
    return run


# ---------- logins, off camera

def login_states(browser):
    ctx = new_context(browser)
    p = ctx.new_page()
    p.goto(FRONTEND)
    oauth_login(p, FRONTEND_USER, os.environ["FRONTEND_PASSWORD"])
    p.goto(FRONTEND)
    p.wait_for_selector("h1", timeout=60_000)
    admin = ctx.storage_state()
    ctx.close()

    ctx = new_context(browser)
    p = ctx.new_page()
    p.goto(RHOAI)
    oauth_login(p, PLATFORM_USER, os.environ["PLATFORM_PASSWORD"])
    p.wait_for_timeout(4000)
    close_rhoai_welcome(p)
    p.goto(CONSOLE + "/topology/ns/multi-agents?view=graph")
    oauth_login(p, PLATFORM_USER, os.environ["PLATFORM_PASSWORD"])
    p.wait_for_timeout(6000)
    dismiss_dialogs(p)
    mou = ctx.storage_state()
    ctx.close()
    return admin, mou


def recording_context(browser, state):
    ctx = new_context(browser, storage_state=state, record_video_dir=f"{OUT}/videos",
                      record_video_size={"width": W, "height": H})
    ctx.add_init_script(CURSOR_JS)
    return ctx


# ---------- scenes

SEARCH = re.compile(r"^(Search by claim number|Tender number|Complaint number)")


@safe
def start_case(ctx, domain, scenes):
    s = Scene(ctx, domain)
    scenes[domain] = s
    p = s.page
    p.goto(FRONTEND + f"/{domain}")
    p.wait_for_selector("tbody tr", timeout=60_000)
    p.wait_for_timeout(800)
    s.mark("ready")
    p.wait_for_timeout(1200)
    type_in(p, p.get_by_placeholder(SEARCH), CASES[domain])
    p.wait_for_timeout(1200)
    click(p, p.locator("tbody tr", has_text=CASES[domain]).first)
    btn = p.get_by_role("button", name="Start processing")
    btn.wait_for(timeout=60_000)
    p.wait_for_timeout(800)
    s.mark("case_open")
    p.wait_for_timeout(1500)
    click(p, btn)
    s.mark("processing_started")
    p.wait_for_timeout(4500)
    s.mark("processing_shown")
    s.shot("started")


@safe
def show_result(domain, scenes):
    s = scenes.get(domain)
    if not s:
        return
    p = s.page
    p.get_by_text("Agent recommendation").wait_for(timeout=20 * 60_000)
    p.wait_for_timeout(1500)
    info[f"{domain}_review"] = p.get_by_text("Manual review required").count() > 0
    run_time = p.get_by_text("Processing time", exact=True)
    if run_time.count():                             # "PROCESSING TIME\n52 s": the real duration, not our wait
        info[f"{domain}_run_time"] = run_time.first.evaluate("el => el.parentElement.innerText").split("\n")[-1]
    link = p.get_by_role("link", name=re.compile(r"Trace of the processing in MLflow", re.I))
    if link.count():
        info[f"{domain}_mlflow_url"] = link.first.get_attribute("href")
    to_top(p, p.get_by_role("heading", name="Decision", exact=True).first)   # the review reasons above are French
    p.wait_for_timeout(1200)
    s.mark("decided")
    glide(p, p.get_by_text("Agent recommendation").first, steps=20)
    p.wait_for_timeout(2500)
    wheel(p, 500)
    p.wait_for_timeout(2000)
    wheel(p, 600)
    p.wait_for_timeout(2000)
    wheel(p, 800)
    p.wait_for_timeout(2600)
    s.mark("end")
    s.shot("result")
    s.close()


REVIEW = {   # question to the agent, the reviewer's choice, the justification
    "claims": ("What amount does the invoice show, and does the contract cover it?", "Approve",
               "Invoice and contract checked: approved."),
    "tenders": ("What are the main risks you found for this tender?", "Go",
                "Reviewed with the bid team: our references cover this project, we go."),
    "postal": ("What does the tracking show for this parcel?", "Refund",
               "Tracking and client file reviewed: we refund the declared value."),
}


def open_case(p, domain, number):
    p.goto(FRONTEND + f"/{domain}")
    p.wait_for_selector("tbody tr", timeout=60_000)
    p.get_by_placeholder(SEARCH).fill(number)
    p.wait_for_timeout(800)
    p.locator("tbody tr", has_text=number).first.click()
    p.get_by_text("Agent recommendation").wait_for(timeout=60_000)
    p.wait_for_timeout(1500)


def to_top(p, loc, margin=70):
    """Brings `loc` to the top of the scrolling area (the French review reasons stay above, off screen)."""
    loc.evaluate("el => el.scrollIntoView({block: 'start'})")
    p.wait_for_timeout(300)
    wheel(p, -margin, steps=4, pause=20)


@safe
def result_only(ctx, domain, number):
    """The result of an already processed case, from its English decision card down (no processing)."""
    s = Scene(ctx, domain)
    p = s.page
    open_case(p, domain, number)
    to_top(p, p.get_by_role("heading", name="Decision", exact=True).first)
    p.wait_for_timeout(1200)
    s.mark("decided")
    s.shot("decision")
    info[f"{domain}_recommendation"] = p.get_by_text("Agent recommendation").first.evaluate(
        "el => el.parentElement.innerText.slice(0, 120)")
    glide(p, p.get_by_text("Agent recommendation").first, steps=20)
    p.wait_for_timeout(2500)
    wheel(p, 500)
    p.wait_for_timeout(2000)
    wheel(p, 600)
    p.wait_for_timeout(2000)
    wheel(p, 800)
    p.wait_for_timeout(2600)
    s.mark("end")
    s.shot("result")
    s.close()


@safe
def review_direct(ctx, domain, number):
    """The human review of a case, from its page: question, answer, decision (English only on screen)."""
    s = Scene(ctx, "review")
    p = s.page
    open_case(p, domain, number)
    to_top(p, p.get_by_text("2. Ask the agent").first, margin=0)
    p.wait_for_timeout(1500)
    s.mark("case_open")
    s.shot("ask")
    box = p.get_by_placeholder(re.compile(r"^E\.g\. what amount"))
    question = os.environ.get("REVIEW_QUESTION", REVIEW[domain][0])
    type_in(p, box, question, delay=45)
    click(p, p.get_by_role("button", name="Ask", exact=True))
    s.mark("asking")
    busy = p.get_by_role("button", name=re.compile(r"^(The agent is answering|Asking)"))
    try:
        busy.first.wait_for(timeout=10_000)
    except Exception:
        pass
    busy.first.wait_for(state="detached", timeout=10 * 60_000)
    p.wait_for_timeout(1200)
    s.mark("answered")
    to_top(p, p.get_by_text(question, exact=True).last, margin=0)   # the new exchange at the top
    p.wait_for_timeout(800)
    s.mark("answer_shown")
    s.shot("answered")
    p.wait_for_timeout(4500)
    decision = p.get_by_text("3. Your decision").first
    to_top(p, decision, margin=120)
    glide(p, decision, pause=800)
    choice = os.environ.get("REVIEW_CHOICE", REVIEW[domain][1])
    click(p, p.get_by_role("button", name=re.compile(rf"^{re.escape(choice)}(?![-\w])")).first, pause=700)
    type_in(p, p.locator("textarea").last, os.environ.get("REVIEW_NOTE", REVIEW[domain][2]), delay=35)
    click(p, p.get_by_role("button", name="Decide", exact=True).last)
    p.get_by_role("button", name="Cancel", exact=True).last.wait_for(timeout=15_000)
    p.wait_for_timeout(1500)
    s.mark("confirm")
    s.shot("confirm")
    click(p, p.get_by_role("button", name="Decide", exact=True).last)
    s.mark("confirmed")
    p.wait_for_timeout(2700)                         # then the page goes back to the top (French reasons)
    s.mark("end")
    s.shot("decided")
    s.close()


@safe
def sandbox(ctx):
    """OpenShell: the policy in force, then the isolation demo run live in the real sandbox."""
    s = Scene(ctx, "sandbox")
    p = s.page
    p.goto(FRONTEND + "/sandbox")
    p.get_by_text("Policy in force").first.wait_for(timeout=60_000)
    p.wait_for_timeout(1500)
    s.mark("ready")
    p.wait_for_timeout(2500)
    p.get_by_text("Policy in force").first.scroll_into_view_if_needed()
    wheel(p, -120)
    p.wait_for_timeout(600)
    s.mark("policy")
    for label in ("Filesystem", "Network", "Process"):
        loc = p.get_by_text(label, exact=True).first
        if loc.count():
            glide(p, loc, steps=18, pause=1300)
    run_all = p.get_by_role("button", name="Run all")
    run_all.scroll_into_view_if_needed()
    wheel(p, 250)
    p.wait_for_timeout(800)
    click(p, run_all)
    s.mark("run")
    p.wait_for_timeout(5000)
    s.shot("running")
    p.wait_for_timeout(12_000)
    s.mark("results")
    s.shot("results")
    for i, label in enumerate(("Internet access", "System write", "Read outside the policy")):
        loc = p.get_by_text(label, exact=True).first
        loc.scroll_into_view_if_needed()
        wheel(p, 260, steps=10)
        glide(p, loc, steps=16, pause=1800)
        s.mark(f"denied{i}")
        s.shot(f"denied{i}")
    p.wait_for_timeout(1200)
    s.mark("end")
    s.close()


def rhoai_open(s, path):
    p = s.page
    p.goto(RHOAI + path)
    settle(p, 20_000)
    close_rhoai_welcome(p)
    return p


@safe
def maas_models(ctx):
    s = Scene(ctx, "maas_models")
    p = rhoai_open(s, "/gen-ai-studio/assets/multi-agents")
    p.get_by_text("Llama 4 Scout 17B").first.wait_for(timeout=60_000)
    p.wait_for_timeout(1500)
    s.mark("ready")
    p.wait_for_timeout(1200)
    for name in ("GPT-OSS 120B", "Llama 4 Scout 17B"):
        glide(p, p.get_by_text(name, exact=True).first, steps=20, pause=1600)
    p.wait_for_timeout(1200)
    s.mark("end")
    s.shot("end")
    s.close()


@safe
def maas_subs(ctx):
    s = Scene(ctx, "maas_subs")
    p = rhoai_open(s, "/maas/keys-and-subs")
    p.get_by_text("Subscriptions", exact=True).first.wait_for(timeout=60_000)
    p.wait_for_timeout(1500)
    p.get_by_text("Subscriptions", exact=True).first.click()      # before the scene starts: no key owners on screen
    p.get_by_role("link", name="multi-agents-admin").first.wait_for(timeout=60_000)
    p.wait_for_timeout(1500)
    s.mark("ready")
    s.mark("subs")
    for name in ("multi-agents-admin", "multi-agents-users", "souscription-btp"):
        loc = p.get_by_role("link", name=name).first
        if loc.count():
            glide(p, loc, steps=16, pause=900)
    click(p, p.get_by_role("link", name="multi-agents-admin").first)
    p.get_by_text("Models available to members of this subscription").first.wait_for(timeout=60_000)
    p.wait_for_timeout(1500)
    s.mark("detail")
    s.shot("detail")
    for name in ("GPT-OSS 120B", "Llama 4 Scout 17B"):
        glide(p, p.get_by_text(name, exact=True).first, steps=16, pause=1000)
    glide(p, p.get_by_text("3,000,000 / 1 hour").first, steps=16, pause=1500)
    wheel(p, 450)
    p.wait_for_timeout(2500)
    s.mark("end")
    s.shot("keys")
    s.close()


@safe
def agent_detail(ctx):
    s = Scene(ctx, "agents")
    p = rhoai_open(s, "/ai-hub/agents")
    p.get_by_text("MO supported agents").first.wait_for(timeout=60_000)
    p.wait_for_timeout(1500)
    s.mark("ready")
    p.wait_for_timeout(1200)
    p.get_by_text("MO supported agents").first.scroll_into_view_if_needed()
    wheel(p, 200)
    for name in ("Claims Processing Agent", "Postal Services Agent", "Tenders Analysis Agent"):
        glide(p, p.get_by_text(name, exact=True).first, steps=18, pause=800)
    click(p, p.get_by_text("Claims Processing Agent", exact=True).first)
    p.get_by_text("README").first.wait_for(timeout=60_000)
    p.wait_for_timeout(1500)
    s.mark("detail")
    s.shot("detail")
    glide(p, p.get_by_text("Description", exact=True).first, steps=16, pause=1500)
    wheel(p, 450)
    p.wait_for_timeout(2500)
    wheel(p, 400)
    p.wait_for_timeout(2000)
    s.mark("end")
    s.shot("end")
    s.close()


@safe
def mcp_detail(ctx):
    s = Scene(ctx, "mcp")
    p = rhoai_open(s, "/ai-hub/mcp-servers")
    tab = p.get_by_text("MO supported MCP servers", exact=True).first
    tab.wait_for(timeout=60_000)
    p.wait_for_timeout(1500)
    s.mark("ready")
    click(p, tab)
    p.get_by_text("Claims records", exact=True).first.wait_for(timeout=60_000)
    p.wait_for_timeout(1500)
    s.mark("list")
    s.shot("list")
    for name in ("Claims records", "Document OCR", "Knowledge & similarity", "Sandboxed code", "Parcel tracking"):
        loc = p.get_by_text(re.compile("^" + re.escape(name))).first
        if loc.count():
            glide(p, loc, steps=14, pause=650)
    click(p, p.get_by_text("Claims records", exact=True).first)
    p.get_by_text("Tools", exact=True).first.wait_for(timeout=60_000)
    p.wait_for_timeout(1500)
    s.mark("detail")
    s.shot("detail")
    for tool in ("list_claims", "get_claim", "compute_payout"):
        loc = p.get_by_text(tool, exact=True).first
        if loc.count():
            glide(p, loc, steps=14, pause=900)
    glide(p, p.get_by_text("Server details", exact=True).first, steps=16, pause=1500)
    s.mark("detail_end")
    click(p, p.get_by_role("tab", name=re.compile("Deployments")).first)
    p.get_by_text("sandbox-mcp").first.wait_for(timeout=60_000)
    p.wait_for_timeout(1500)
    s.mark("deployments")
    s.shot("deployments")
    rows = p.locator("tbody tr:visible")
    for i in range(min(rows.count(), 7)):
        glide(p, rows.nth(i), steps=10, pause=350)
    p.wait_for_timeout(1500)
    s.mark("end")
    s.close()


@safe
def home(ctx):
    s = Scene(ctx, "home")
    p = s.page
    p.goto(FRONTEND)
    p.get_by_role("heading", name="Multi-Agent AI Platform").wait_for(timeout=60_000)
    p.wait_for_timeout(1000)
    s.mark("ready")
    p.wait_for_timeout(1500)
    for title in ("Claims", "Tenders", "Mail & Parcels"):
        glide(p, p.get_by_role("heading", name=title, exact=True).first, steps=22, pause=700)
    wheel(p, 900)
    p.wait_for_timeout(2500)
    s.mark("end")
    s.close()


@safe
def chat(ctx):
    s = Scene(ctx, "chat")
    p = s.page
    p.goto(FRONTEND)
    box = p.get_by_placeholder(re.compile(r"^What would you like to do\?"))
    box.wait_for(timeout=60_000)
    p.wait_for_timeout(1000)
    s.mark("ready")
    type_in(p, box, CHAT_PROMPT, delay=55)
    p.wait_for_timeout(600)
    click(p, p.get_by_role("button", name="Start"))
    p.locator("textarea").first.wait_for(timeout=60_000)
    s.mark("sent")
    p.locator("button[title='Stop generating']").wait_for(timeout=60_000)
    p.locator("button[title='Send']").wait_for(timeout=15 * 60_000)
    p.get_by_role("heading", name="Summary").wait_for(timeout=60_000)
    p.wait_for_timeout(1500)
    s.mark("done")
    s.shot("done")
    # the trace panel: back to the top, then down to the summary
    panel = p.get_by_role("heading", name="Execution trace").first
    pb = panel.bounding_box()
    px, py = pb["x"] + 160, H * 0.55
    wheel(p, -6000, x=px, y=py, steps=12, pause=20)
    p.wait_for_timeout(1500)
    s.mark("trace_top")
    for _ in range(5):
        wheel(p, 420, x=px, y=py)
        p.wait_for_timeout(1300)
    mlflow = p.get_by_role("link", name="Open in MLflow")
    if mlflow.count():
        info["chat_mlflow_url"] = mlflow.first.get_attribute("href")
        glide(p, mlflow.first)
        p.wait_for_timeout(1500)
    s.mark("end")
    s.shot("summary")
    s.close()


@safe
def mlflow(ctx):
    url = MLFLOW_URL or info.get("claims_mlflow_url") or info.get("chat_mlflow_url")
    if not url:
        print("!! no MLflow url, scene skipped", flush=True)
        return
    s = Scene(ctx, "mlflow")
    p = s.page
    p.goto(RHOAI + "/mlflow/")
    settle(p, 20_000)
    ws = p.get_by_role("link", name="multi-agents", exact=True).first
    ws.wait_for(timeout=60_000)
    p.wait_for_timeout(1500)
    s.mark("ready")
    p.wait_for_timeout(1200)
    click(p, ws)
    settle(p, 20_000)
    p.wait_for_timeout(1500)
    p.goto(url)                                    # the experiment of the agents, its traces
    settle(p, 20_000)
    p.get_by_role("heading", name="Traces").first.wait_for(timeout=60_000)
    p.wait_for_timeout(2500)
    s.mark("traces")
    rows = p.locator("tbody tr:visible, [role=row]:visible")
    for i in range(1, min(rows.count(), 5)):
        glide(p, rows.nth(i), steps=14, pause=600)
    req = p.get_by_text(re.compile(r"Process the following insurance claim")).first
    click(p, req)
    p.wait_for_timeout(5000)
    s.mark("trace_open")
    s.shot("trace-open")
    more = p.get_by_text(re.compile(r"Show \d+ more intermediate steps"))
    if more.count():
        click(p, more.first)
        p.wait_for_timeout(3000)
        s.mark("steps")
    tab = p.get_by_role("tab", name=re.compile(r"Details & Timeline"))
    if not tab.count():
        tab = p.get_by_text("Details & Timeline")
    if tab.count():
        click(p, tab.first)
        p.wait_for_timeout(4500)
        s.mark("timeline")
        s.shot("timeline")
        for span in ("guardrails", "tool:retrieve_similar_claims", "tool:compute_payout", "llm-response"):
            loc = p.get_by_text(span, exact=True)
            if loc.count():
                click(p, loc.first, steps=14)
                p.wait_for_timeout(1700)
    p.wait_for_timeout(1500)
    s.mark("end")
    s.shot("end")
    s.close()


@safe
def admin(ctx):
    s = Scene(ctx, "admin")
    p = s.page
    p.goto(FRONTEND + "/admin")
    p.get_by_role("heading", name="Admin Panel").wait_for(timeout=60_000)
    keep = "".join(f':not(:has(input[aria-label^="{u}"]))' for u in KEEP_USERS)
    p.add_style_tag(content=f'tr:has(input[aria-label*=" — "]){keep} td:first-child {{ filter: blur(7px); }}')
    p.wait_for_timeout(1000)
    s.mark("ready")
    p.wait_for_timeout(800)
    target = p.get_by_text("Users and access profiles").first
    target.scroll_into_view_if_needed()
    p.wait_for_timeout(400)
    wheel(p, 250)
    s.mark("profiles")
    for q in p.get_by_text(re.compile(r"^MaaS:")).all()[:4]:
        glide(p, q, steps=18, pause=900)
    p.wait_for_timeout(1200)
    s.mark("end")
    s.shot("profiles")
    s.close()


@safe
def console(ctx):
    s = Scene(ctx, "console")
    p = s.page
    p.goto(CONSOLE + "/topology/ns/multi-agents?view=graph")
    settle(p, 30_000)
    dismiss_dialogs(p)
    p.wait_for_timeout(8000)
    dismiss_dialogs(p)
    s.mark("ready")
    s.shot("ready")
    fit = p.get_by_role("button", name=re.compile(r"fit to screen", re.I))
    if fit.count():
        click(p, fit.first)
        p.wait_for_timeout(2500)
    p.mouse.move(W * 0.5, H * 0.5, steps=20)
    p.wait_for_timeout(4000)
    s.mark("end")
    s.close()


with sync_playwright() as pw:
    if not PLATFORM_USER:
        raise SystemExit("PLATFORM_USER is required (a cluster user who sees OpenShift AI, MLflow and the console)")
    browser = pw.chromium.launch(channel="chromium")   # full Chromium: the headless shell has no PDF viewer
    state_front, state_platform = login_states(browser)
    print("logins done", flush=True)
    ctx_a = recording_context(browser, state_front)
    ctx_m = recording_context(browser, state_platform)
    cases = {}
    try:
        if "cases" in SCENES:                       # first: the agents work while the other scenes are filmed
            for d in CASE_DOMAINS:
                start_case(ctx_a, d, cases)
        for key, scene in (("maasmodels", maas_models), ("maassubs", maas_subs), ("agentdetail", agent_detail),
                           ("mcpdetail", mcp_detail)):
            if key in SCENES:
                scene(ctx_m)
        for key, scene in (("home", home), ("chat", chat), ("admin", admin)):
            if key in SCENES:
                scene(ctx_a)
        if "console" in SCENES:
            console(ctx_m)
        if "sandbox" in SCENES:
            sandbox(ctx_a)
        if "results" in SCENES:
            for d in CASE_DOMAINS:
                show_result(d, cases)
        if "resultsonly" in SCENES:                 # results of cases processed earlier: RESULT_CASES=tenders:AO-...
            for item in os.environ.get("RESULT_CASES", "").split(","):
                if item:
                    d, n = item.split(":")
                    result_only(ctx_a, d, n)
        if "review" in SCENES:                      # the first of our cases the agent handed over, or REVIEW_DIRECT
            target = os.environ.get("REVIEW_DIRECT")
            if target:
                d, n = target.split(":")
            else:
                d = next((d for d in CASE_DOMAINS if info.get(f"{d}_review")), None)
                n = CASES.get(d)
            if d:
                review_direct(ctx_a, d, n)
            else:
                print("!! no case handed over to a human: review scene skipped (set REVIEW_DIRECT)", flush=True)
        if "mlflow" in SCENES:
            mlflow(ctx_m)
    finally:
        ctx_a.close()
        ctx_m.close()
        browser.close()
        json.dump({"scenes": marks, "info": info, "cases": CASES, "chat_prompt": CHAT_PROMPT},
                  open(f"{OUT}/marks.json", "w"), indent=2)
        print(json.dumps(info, indent=2), flush=True)

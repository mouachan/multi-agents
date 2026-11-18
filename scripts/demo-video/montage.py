"""Montage plan -> overlays (PNG, rendered by Chromium), music, voice track and out/build/montage.sh (ffmpeg).

Reads out/rec/marks.json (see record.py, merge_marks.py). Each clip of PLAN: scene, start mark, end mark
("label+1.5" offsets), speed, caption title and subtitle. The captions describe what was filmed: check them
against the footage after a new recording. With VOICE_JSON (narration.py), each clip lasts at least its spoken
line (the last frame is held) and the music is ducked under the voice.
"""
import html
import json
import os
import re
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import music  # noqa: E402

REC = os.environ.get("REC", "/work/out/rec")
BUILD = os.environ.get("BUILD", "/work/out/build")
os.makedirs(BUILD, exist_ok=True)
FPS = 30
XF = 0.4                                  # cross-fade between clips
W, H = 1920, 1080

m = json.load(open(f"{REC}/marks.json"))
S = m["scenes"]


def t(scene, expr):
    mt = re.fullmatch(r"([a-z_]+)([+-][0-9.]+)?", expr)
    label, off = mt.group(1), float(mt.group(2) or 0)
    return S[scene]["marks"][label] + off


def has(scene, *labels):
    return scene in S and all(lab in S[scene]["marks"] for lab in labels)


# processing time per domain, as shown by the UI (record.py reads it); RUN_TIME='{"tenders": "52 s"}' overrides
RUN_TIME = {k[:-len("_run_time")]: v for k, v in m.get("info", {}).items() if k.endswith("_run_time")}
RUN_TIME.update(json.loads(os.environ.get("RUN_TIME", "{}")))


def wait_minutes(scene):
    if scene in RUN_TIME:
        return RUN_TIME[scene]
    secs = t(scene, "decided") - t(scene, "processing_started")
    return f"{secs / 60:.0f} min" if secs >= 90 else f"{secs:.0f} s"


PLAN = [("card", "title")]
if has("maas_models", "ready", "end"):
    PLAN.append(("maas_models", "ready", "end", 1.0, "Models-as-a-Service on OpenShift AI",
                 "The models the agents use, served through MaaS: Llama 4 Scout 17B and GPT-OSS 120B"))
if has("maas_subs", "ready", "detail", "end"):
    PLAN.append(("maas_subs", "ready", "detail-0.3", 1.3, "Subscriptions: which OpenShift groups may call which models",
                 "multi-agents-admin, multi-agents-users, souscription-btp"))
    PLAN.append(("maas_subs", "detail-0.3", "end", 1.3, "Authorizations: models and token limits per subscription",
                 "Members of multi-agents-admin: Llama 4 Scout 17B and GPT-OSS 120B, 3,000,000 tokens per hour, their API keys"))
if has("agents", "ready", "detail", "end"):
    PLAN.append(("agents", "ready", "detail-0.3", 1.4, "Three A2A business agents, published in the OpenShift AI hub",
                 "MO supported agents: Claims, Postal, Tenders"))
    PLAN.append(("agents", "detail-0.3", "end", 1.4, "An agent page in the AI hub",
                 "Claims Processing Agent: what it does, its A2A framework, its README"))
if has("mcp", "ready", "detail", "detail_end", "end"):
    PLAN.append(("mcp", "ready", "detail-0.3", 1.4, "The MCP servers of the platform",
                 "Claims, OCR, postal, RAG search, sandboxed code interpreter, tenders, parcel tracking"))
    PLAN.append(("mcp", "detail-0.3", "detail_end", 1.0, "An MCP server page: its tools",
                 "Claims records: read-only tools such as list_claims, get_claim, compute_payout"))
    PLAN.append(("mcp", "detail_end", "end", 1.3, "Deployed in the multi-agents project",
                 "7 MCP servers, all available, behind the MCP Gateway"))
if has("home", "ready", "end"):
    PLAN.append(("home", "ready", "end", 1.6, "One platform, three business domains",
                 "Each domain has its own agent, its MCP tools and its human review"))
if has("claims", "ready", "processing_shown"):
    PLAN.append(("claims", "ready", "processing_shown", 1.6, "Claims: the agent processes a real insurance claim",
                 "PDF OCR, contract lookup, precedents (RAG): all through MCP tools"))
RESULTS = {
    "claims": ("Decision, confidence and reasoning",
               "Each MCP tool call is a step: the payout runs in an OpenShell sandbox, personal data flagged by NeMo"),
    "tenders": ("Tenders: not sure enough, the agent asks a human",
                "\u201cLook closer\u201d at 60 % confidence: the tender goes to human review"),
    "postal": ("Mail & Parcels: a damaged parcel complaint, escalated",
               "Tracking, documents and similar cases checked, then handed over to a human"),
}
for d, (cap, sub) in RESULTS.items():
    if has(d, "decided", "end") and (d in RUN_TIME or has(d, "processing_started")):
        PLAN.append((d, "decided-1", "end-2.6", 2.0, cap, f"{sub}   ·   ⏱ agent run: {wait_minutes(d)}"))
if has("review", "case_open", "answered", "answer_shown", "end"):
    ask = t("review", "answered") - t("review", "case_open")
    PLAN.append(("review", "case_open", "answered", max(1.0, ask / 7.0), "Human in the loop: the agent hands the case over",
                 f"Before deciding, the reviewer can question the agent   ·   ⏩ ×{max(1.0, ask / 7.0):.0f}"))
    PLAN.append(("review", "answered", "answer_shown+5", 1.0, "The agent answers, under the same guardrails",
                 "Read-only tools, personal data masked by NeMo, the exchange kept with the case and in MLflow"))
    PLAN.append(("review", "answer_shown+5", "end", 1.6, "The human decides",
                 "Refund, with a justification kept with the case"))
if has("chat", "ready", "sent", "done", "trace_top", "end"):
    PLAN.append(("chat", "ready", "sent+2.5", 1.3, "Chat: ask in natural language",
                 "The orchestrator routes the request to the right agent over A2A"))
    live = t("chat", "done") - t("chat", "sent+2.5")
    PLAN.append(("chat", "sent+2.5", "done", max(1.0, live / 6.5), "Live execution trace",
                 f"Routing · A2A · NeMo Guardrails · MCP tools · OpenShell sandbox   ·   ⏩ ×{max(1.0, live / 6.5):.0f}"))
    PLAN.append(("chat", "trace_top", "end", 2.0, "Every turn is traced",
                 "The OpenShell run, model, tokens, prompt version, guardrails (PII masked), the MLflow link"))
if has("mlflow", "ready", "trace_open", "end"):
    PLAN.append(("mlflow", "ready", "trace_open-0.5", 2.4, "MLflow on OpenShift AI: every agent run is a trace",
                 "Workspace multi-agents  ›  experiment multi-agent-orchestrator  ›  the runs just made"))
    PLAN.append(("mlflow", "trace_open-0.5", "end", 2.0, "Inside the claim's trace",
                 "NeMo Guardrails, MCP tool calls, the OpenShell payout run, LLM response: tokens and latency"))
if has("admin", "profiles", "end"):
    PLAN.append(("admin", "profiles-0.3", "end", 1.2, "Governance: access profiles are OpenShift groups",
                 "Each profile: its agents, its allowed MCP tools and its MaaS token quota"))
if has("console", "ready", "end"):
    PLAN.append(("console", "ready", "end", 1.15, "All of it runs on OpenShift",
                 "Agents, MCP servers and gateway, OGX, NeMo Guardrails, PostgreSQL"))
if has("sandbox", "ready", "run", "end"):
    PLAN.append(("sandbox", "ready", "run+1", 1.6, "OpenShell: the code the agents write runs in a sandbox",
                 "Policy enforced by the kernel: Landlock filesystem, all outbound traffic denied, non-root, 60 s max"))
    PLAN.append(("sandbox", "run+1", "end", 2.4, "Isolation demo, live in the real sandbox",
                 "The payout computation runs; internet access, writes to /etc and reads outside the policy are denied"))
PLAN.append(("card", "end"))

CARD_SECS = {"title": 3.6, "end": 4.2}
FONTS = ('<link rel="preconnect" href="https://fonts.gstatic.com">'
         '<link href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@500;700;900&'
         'family=Red+Hat+Text:wght@400;500&display=swap" rel="stylesheet">')
# layout: the capture at 87.5 % on top, the explanation in a band under it (nothing hides the demo)
VW, VH, VX, VY = 1680, 945, 120, 12
BG = "#111215"
CAPTION_HTML = """<html><head>{fonts}<style>
html,body{{margin:0;background:transparent;width:1920px;height:1080px;}}
.cap{{position:absolute;left:120px;top:972px;height:96px;display:flex;flex-direction:column;justify-content:center;
 border-left:5px solid #ee0000;padding-left:20px;color:#fff}}
.t{{font:700 30px/1.15 'Red Hat Display',sans-serif;letter-spacing:-.2px}}
.s{{font:400 20px/1.3 'Red Hat Text',sans-serif;color:#c4c6cc;margin-top:6px}}
</style></head><body><div class="cap"><div class="t">{title}</div><div class="s">{sub}</div></div></body></html>"""
MASK_HTML = """<html><head><style>
html,body{{margin:0;background:transparent;width:1920px;height:1080px;overflow:hidden}}
.hole{{position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-radius:14px;
 box-shadow:0 0 0 3000px {bg};outline:1px solid rgba(255,255,255,.10);outline-offset:-1px}}
</style></head><body><div class="hole"></div></body></html>"""
CARD_HTML = """<html><head>{fonts}<style>
html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;
 background:radial-gradient(1200px 700px at 78% 20%,rgba(238,0,0,.28),transparent 60%),linear-gradient(135deg,#0c0d10,#1b1d23);}}
.wrap{{position:absolute;left:140px;top:300px;right:140px;color:#fff}}
.kicker{{font:500 30px 'Red Hat Text',sans-serif;color:#ff5c5c;letter-spacing:3px;text-transform:uppercase}}
h1{{font:900 92px/1.05 'Red Hat Display',sans-serif;margin:22px 0 30px;letter-spacing:-1.5px}}
.bar{{width:120px;height:8px;background:#ee0000;border-radius:4px;margin-bottom:36px}}
.chips span{{display:inline-block;font:500 27px 'Red Hat Text',sans-serif;color:#e8e8e8;border:1.5px solid rgba(255,255,255,.28);
 border-radius:40px;padding:10px 24px;margin:0 14px 14px 0}}
</style></head><body><div class="wrap"><div class="kicker">{kicker}</div><h1>{title}</h1><div class="bar"></div>
<div class="chips">{chips}</div></div></body></html>"""
CARDS = {
    "title": ("Demo", "Agentic AI on<br>Red Hat OpenShift AI 3.5",
              ["OGX", "A2A agents", "MCP Gateway", "NeMo Guardrails", "OpenShell", "MLflow", "Models-as-a-Service"]),
    "end": ("Multi-agent platform", "Business agents,<br>governed and traced",
            ["Claims", "Tenders", "Mail & Parcels", "Human review", "OpenShell sandbox", "OpenShift groups = access profiles", "MaaS quotas", "MLflow traces"]),
}


def render_overlays():
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.set_content(MASK_HTML.format(x=VX, y=VY, w=VW, h=VH, bg=BG))
        pg.screenshot(path=f"{BUILD}/mask.png", omit_background=True)
        for i, item in enumerate(PLAN):
            if item[0] == "card":
                kicker, title, chips = CARDS[item[1]]
                pg.set_content(CARD_HTML.format(fonts=FONTS, kicker=kicker, title=title,
                                                chips="".join(f"<span>{html.escape(c)}</span>" for c in chips)))
                pg.evaluate("document.fonts.ready")
                pg.wait_for_timeout(400)
                pg.screenshot(path=f"{BUILD}/ov{i:02d}.png")
            else:
                pg.set_content(CAPTION_HTML.format(fonts=FONTS, title=html.escape(item[4]), sub=html.escape(item[5])))
                pg.evaluate("document.fonts.ready")
                pg.wait_for_timeout(400)
                pg.screenshot(path=f"{BUILD}/ov{i:02d}.png", omit_background=True)
        b.close()


def frames(sec):
    return round(sec * FPS) / FPS


VOICE_JSON = os.environ.get("VOICE_JSON")              # narration.json: one spoken line per clip
VOICE_LEAD, VOICE_TAIL = 0.45, 0.45                      # silence before / after each line inside its clip
CHAPTERS = {"maas_models": "Models-as-a-Service: models, subscriptions, authorizations",
            "agents": "A2A agents in the OpenShift AI hub", "mcp": "MCP servers",
            "home": "The multi-agent platform: claims processing", "tenders": "Tenders and mail & parcels",
            "review": "Human in the loop", "chat": "Chat and live execution trace",
            "mlflow": "MLflow traces on OpenShift AI", "admin": "Governance and OpenShift",
            "sandbox": "OpenShell sandbox"}


def voice_lines():
    if not VOICE_JSON:
        return None
    lines = json.load(open(VOICE_JSON))["lines"]
    assert len(lines) == len(PLAN), f"{len(lines)} narration lines for {len(PLAN)} clips"
    return lines


def build_script():
    voice = voice_lines()
    lines = ["set -e", f"cd {BUILD}"]
    durs = []
    for i, item in enumerate(PLAN):
        out = f"clip{i:02d}.mp4"
        need = voice[i]["seconds"] + VOICE_LEAD + VOICE_TAIL if voice else 0
        if item[0] == "card":
            d = frames(max(CARD_SECS[item[1]], need))
            lines.append(f"ffmpeg -hide_banner -loglevel error -y -loop 1 -framerate {FPS} -t {d} -i ov{i:02d}.png "
                         f"-vf \"format=yuv420p,fade=t=in:st=0:d=0.5\" -c:v libx264 -preset medium -crf 18 -r {FPS} {out}")
        else:
            scene, a, z, speed, *_ = item
            start, end = t(scene, a), t(scene, z)
            seen = frames((end - start) / speed)
            d = frames(max(seen, need))
            hold = f",tpad=stop_mode=clone:stop_duration={d - seen + 0.1:.2f}" if d > seen else ""   # freeze the last frame
            src = f"{REC}/{S[scene]['video']}"
            fo = max(0.0, d - 0.55)
            lines.append(
                f"ffmpeg -hide_banner -loglevel error -y -ss {start:.2f} -t {end - start:.2f} -i {src} "
                f"-loop 1 -i mask.png -loop 1 -i ov{i:02d}.png "
                f"-filter_complex \"[0:v]setpts=(PTS-STARTPTS)/{speed:.4f},fps={FPS}{hold},scale={VW}:{VH}:flags=lanczos,"
                f"pad={W}:{H}:{VX}:{VY}:color=0x111215,format=rgba[v];"
                f"[v][1:v]overlay=0:0:shortest=1[m];"
                f"[2:v]format=rgba,fade=t=in:st=0.2:d=0.4:alpha=1,fade=t=out:st={fo:.2f}:d=0.4:alpha=1[c];"
                f"[m][c]overlay=0:0:shortest=1,format=yuv420p\" -t {d} -an -c:v libx264 -preset medium -crf 18 -r {FPS} {out}")
        durs.append(d)
    starts = [sum(durs[:i]) - i * XF for i in range(len(PLAN))]
    # cross-fade chain
    inputs = " ".join(f"-i clip{i:02d}.mp4" for i in range(len(PLAN)))
    chain, prev, acc = [], "[0:v]", durs[0]
    for i in range(1, len(PLAN)):
        tag = f"[x{i}]"
        chain.append(f"{prev}[{i}:v]xfade=transition=fade:duration={XF}:offset={acc - XF:.3f}{tag}")
        prev, acc = tag, acc + durs[i] - XF
    total = acc
    fade_out = total - 3.0
    music = (f"[{len(PLAN)}:a]atrim=0:{total:.2f},afade=t=in:st=0:d=1.2,afade=t=out:st={fade_out:.2f}:d=3,"
             f"volume={0.55 if voice else 0.85}")
    if voice:
        build_voice_track(voice, starts, total)
        audio = (f"{music}[m0];[{len(PLAN) + 1}:a]aresample=44100,pan=stereo|c0=c0|c1=c0,asplit=2[vs][vm];"
                 f"[m0][vs]sidechaincompress=threshold=0.015:ratio=10:attack=25:release=450[md];"
                 f"[md][vm]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]")
        extra_in = "-i music.wav -i voice.wav"
    else:
        audio, extra_in = f"{music}[a]", "-i music.wav"
    lines.append(
        f"ffmpeg -hide_banner -loglevel error -y {inputs} {extra_in} -filter_complex "
        f"\"{';'.join(chain)};{prev}fade=t=out:st={total - 0.8:.2f}:d=0.8,format=yuv420p[v];{audio}\" "
        f"-map \"[v]\" -map \"[a]\" -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -r {FPS} "
        f"-c:a aac -b:a 192k -movflags +faststart final.mp4")
    open(f"{BUILD}/montage.sh", "w").write("\n".join(lines) + "\n")
    return total, durs, starts


def build_voice_track(voice, starts, total):
    """All the lines on one 24 kHz track, each at its clip start + VOICE_LEAD, normalised to -1 dBFS."""
    import wave
    import numpy as np
    rate = 24000
    track = np.zeros(int((total + 1) * rate), dtype=np.float32)
    for line, start in zip(voice, starts):
        with wave.open(line["wav"]) as w:
            pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        i = int((start + VOICE_LEAD) * rate)
        track[i:i + len(pcm)] += pcm[:len(track) - i]
    track *= 0.89 / max(1e-6, np.max(np.abs(track)))
    with wave.open(f"{BUILD}/voice.wav", "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((track * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    total, durs, starts = build_script()
    for item, d in zip(PLAN, durs):
        print(f"{d:6.2f}s  {item[0]:8s} {item[4] if len(item) > 4 else item[1]}")
    print(f"TOTAL ≈ {total:.1f}s ({len(PLAN)} clips)")
    print("Chapters")
    seen = set()
    for item, start in zip(PLAN, starts):
        key = item[0]
        if key in CHAPTERS and key not in seen:
            seen.add(key)
            st = 0 if not seen - {key} else int(start)
            print(f"{st // 60}:{st % 60:02d} {CHAPTERS[key]}")
    if "--plan" in sys.argv:
        sys.exit(0)
    render_overlays()
    music.main(total + 1.5, f"{BUILD}/music.wav")

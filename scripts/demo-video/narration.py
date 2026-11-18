"""The voice-over: one line per clip of montage.py's PLAN, in the same order (27 clips), spoken by Kokoro.

Writes out/voice/line-NN.wav (24 kHz mono) and out/voice/narration.json (text + duration per line).
The lines spell the acronyms the way they must be pronounced ("M C P", "A to A", "M L flow").
usage: python narration.py [voice] [speed]     (default af_sarah 1.0)
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
from kokoro import KPipeline

VOICE = sys.argv[1] if len(sys.argv) > 1 else "af_sarah"
SPEED = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

LINES = [
    "This is a multi-agent platform, running on Red Hat OpenShift AI three point five.",
    "It starts with Models as a Service: the agents use two models served by the platform, Llama four Scout and G P T O S S.",
    "Subscriptions decide which OpenShift groups may call which models,",
    "with token limits, here three million tokens per hour, and the A P I keys of their members.",
    "The three business agents are published in the OpenShift AI hub: claims, mail and parcels, and tenders.",
    "Each agent has its own page: what it does, its A to A framework, its documentation.",
    "Their tools come from M C P servers: claims records, document O C R, knowledge search, parcel tracking, and a sandboxed code interpreter.",
    "A server page lists its tools. These ones are read-only.",
    "All seven servers run in the multi-agents project, behind the M C P Gateway.",
    "Now, the business application: one platform, three domains, each with its own agent.",
    "A new insurance claim comes in. One click, and the agent reads the P D F and calls its tools.",
    "Within seconds, it decides, with its confidence and its reasoning. The payout is computed in an OpenShell sandbox, and Nemo Guardrails flags the personal data.",
    "On this tender, the agent is not confident enough, so it hands it over to a human.",
    "Same for this damaged parcel: the complaint is escalated to a person.",
    "Human in the loop: before deciding, the reviewer can question the agent,",
    "which answers with read-only tools, under the same guardrails. Names stay masked.",
    "The reviewer chooses a refund, adds a justification, and confirms. The decision stays with the case.",
    "Users can also just ask in plain English. The orchestrator routes the request to the right agent.",
    "The execution trace shows it live: routing, the A to A call, guardrails, M C P tools, and the sandbox.",
    "Every turn is summed up: model, tokens, prompt version, guardrails, and a link to its M L flow trace.",
    "In M L flow, on OpenShift AI, every agent run is a trace.",
    "Open one, and you see each step: the guardrails, every M C P tool call, the OpenShell payout run, and the model's answer, with tokens and latency.",
    "Governance is simple: access profiles are OpenShift groups, each with its agents, its M C P tools, and its token quota.",
    "And all of it runs on OpenShift: agents, M C P servers, gateways, guardrails, and data.",
    "Last, OpenShell. The code the agents write runs in a sandbox, where the kernel enforces the policy: no network, and a locked-down file system.",
    "Let's prove it, live. The payout computation runs, but internet access, writing to the system, and reading outside the policy, are all denied.",
    "Business agents on OpenShift AI: governed, observable, and safe.",
]

OUT = os.environ.get("VOICE_OUT", "/work/out/voice")
os.makedirs(OUT, exist_ok=True)
pipe = KPipeline(lang_code="a")
out = []
for i, text in enumerate(LINES):
    audio = np.concatenate([a for _, _, a in pipe(text, voice=VOICE, speed=SPEED)])
    path = f"{OUT}/line-{i:02d}.wav"
    sf.write(path, audio, 24000)
    out.append({"i": i, "say": text, "seconds": round(len(audio) / 24000, 2), "wav": path})
    print(f"{i:02d} {len(audio) / 24000:5.1f}s  {text[:70]}", flush=True)
json.dump({"voice": VOICE, "speed": SPEED, "lines": out}, open(f"{OUT}/narration.json", "w"), indent=2)
print("total speech:", round(sum(x["seconds"] for x in out), 1), "s")

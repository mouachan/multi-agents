# Demo video

Records a narrated demo video of the platform (about 3.5 minutes, 1080p) from a live cluster:
Models-as-a-Service, the agents and MCP servers in the OpenShift AI hub, real processings of a claim, a tender
and a complaint, the human review, the chat with its execution trace, MLflow traces, governance, the
OpenShift console and the OpenShell sandbox. Captions sit in a band under the capture, with an original music
track and an optional synthetic voice-over.

Everything runs in podman; what is produced goes to `out/` (git-ignored).

| Step | Tool | Script |
|---|---|---|
| Recording | Playwright + full Chromium (headless), one video per scene, timestamps in `marks.json` | `record.py`, `common.py` |
| Voice-over | Kokoro-82M text-to-speech (Apache 2.0), local CPU | `narration.py` |
| Music | a small synthesizer (numpy), original track | `music.py` |
| Montage | captions rendered by Chromium, then ffmpeg (cuts, speed, cross-fades, ducking) | `montage.py` |
| Retakes | replaces scenes of a recording by those of a retake | `merge_marks.py` |

## Before recording

- **Side effects**: a full recording processes 3 pending cases (`CLAIM`, `TENDER`, `POSTAL`), sends one chat
  message, asks one question to an agent and records one human decision. Admin > Reset database puts the cases
  back in their installation state.
- **Users**: `FRONTEND_USER` (default `demo-admin`) must be in the admin profile, which sees the three domains;
  `PLATFORM_USER` must see OpenShift AI (MaaS, AI hub), MLflow (workspace `multi-agents`) and the console.
- **The MaaS must answer**: the processings call the models. After a cluster restart, call it through every
  address of its load balancer; each one must answer (401 without a key):
  `for ip in $(dig +short maas.$APPS_DOMAIN); do curl -s -o /dev/null -w "$ip %{http_code}\n" -m 8 --resolve maas.$APPS_DOMAIN:443:$ip https://maas.$APPS_DOMAIN/v1/models; done`
  (MaaS objects and keys: [troubleshooting](../../docs/troubleshooting.md)).
- Use cases that are still pending (Claims / Tenders / Mail & Parcels lists, status Pending).

## Run

```bash
cd scripts/demo-video
./demo-video.sh build                      # once, ~5 GB image

export APPS_DOMAIN=apps.<cluster>.<base-domain>
export FRONTEND_PASSWORD=<demo-admin password> PLATFORM_USER=<user> PLATFORM_PASSWORD=<password>
export CLAIM=CLM-2024-0026 TENDER=AO-2026-0069 POSTAL=RECL-2025-0026
./demo-video.sh record                     # ~5 to 10 min, mostly waiting for the agents

./demo-video.sh voice                      # optional: out/voice/ (af_sarah, speed 1.0)
./demo-video.sh plan                       # durations and YouTube chapters
./demo-video.sh montage                    # out/multi-agents-demo.mp4
./demo-video.sh clean                      # remove the image and the model cache when done
```

Check the screenshots `out/rec/*.png` and the log before the montage: a failed scene prints `!! scene ... failed`.

## Settings

| Variable | Default | Use |
|---|---|---|
| `APPS_DOMAIN` | (required) | apps domain of the cluster |
| `IDP_NAME` | `local-users` | OpenShift identity provider to log in with |
| `FRONTEND_USER` / `FRONTEND_PASSWORD` | `demo-admin` / (required) | frontend scenes |
| `PLATFORM_USER` / `PLATFORM_PASSWORD` | (required) | OpenShift AI, MLflow and console scenes |
| `KEEP_USERS` | `demo-` | user names left readable on the Admin page (prefixes); the others are blurred, `PLATFORM_USER` is always kept |
| `SCENES` | all, in order | `cases, maasmodels, maassubs, agentdetail, mcpdetail, home, chat, admin, console, sandbox, results, review, mlflow` |
| `CLAIM` / `TENDER` / `POSTAL` | `CLM-2024-0030` / `AO-2026-0071` / `RECL-2025-0028` | pending cases to process |
| `REVIEW_DIRECT` | first of our cases handed to a human | `domain:number` of the reviewed case, e.g. `postal:RECL-2025-0026` |
| `REVIEW_QUESTION` / `REVIEW_CHOICE` / `REVIEW_NOTE` | per domain, see `REVIEW` in `record.py` | the human review |
| `RESULT_CASES` | | with `SCENES=resultsonly`: results of cases processed earlier, `tenders:AO-2026-0069,...` |
| `MLFLOW_URL` | the claim's trace | MLflow scene alone |
| `OUT` | `/work/out/rec` | recording folder (in the container) |
| `NO_VOICE=1` | | montage without the voice-over |
| `RUN_TIME` | read from the UI | override the processing time shown in captions, `{"tenders": "52 s"}` |

## Retakes

Record only the scenes to redo in another folder, then merge them into the main recording:

```bash
SCENES=review,mlflow OUT=/work/out/rec-retake REVIEW_DIRECT=postal:RECL-2025-0026 ./demo-video.sh record
./demo-video.sh merge /work/out/rec /work/out/rec-retake:review,mlflow
./demo-video.sh montage
```

## Editing the story

- `PLAN` in `montage.py`: the clips, their order, speed and captions. Captions state facts about the footage
  (models, quotas, decisions): read them again after a new recording.
- `LINES` in `narration.py`: one spoken line per clip of `PLAN`, same order (the montage checks the count).
  Spell the acronyms as they must be said ("M C P", "A to A", "M L flow"), then `./demo-video.sh voice`.

## Known pitfalls

- PDFs render only in the full Chromium (`channel="chromium"`): the headless shell has no PDF viewer.
- The red cursor is drawn by the script in the top document only, so it never sticks inside the PDF iframe.
- The review reasons and points to check are French only (`agents/shared/decision.py`): the result scenes start
  on the English decision card and the review scene starts on "Ask the agent", then ends before the page goes
  back to the top.
- `CLM-2024-0028` (the prompt-injection demo case) fails the processing; do not use it.

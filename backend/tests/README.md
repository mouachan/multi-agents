# Backend tests

The tests run the real application against a PostgreSQL (pgvector) loaded with the schema and the seed
of the cluster database (`database/init.sql`, `database/seed_data/`). The A2A agents are replaced by a
fake that records what it is asked and answers what each test sets (`conftest.py`, `FakeAgent`).

From the repository root:

```bash
podman compose -f backend/tests/compose.yaml up --build --abort-on-container-exit --exit-code-from tests
podman compose -f backend/tests/compose.yaml down -v      # remove the database
```

To run one file or one test while the database is up:

```bash
podman compose -f backend/tests/compose.yaml run --rm --build tests pytest -q tests/test_review.py -k justification
```

| File | What it checks |
|---|---|
| `test_domains.py` | the business API of every domain, the processing by the agent (tools sent, decision saved, status, failure) |
| `test_review.py` | the human review: inbox, brief and evidence, questions to the agent, decision and justification |
| `test_chat.py` | conversations, routing, the streamed answer, masking when the guardrails could not check |
| `test_access.py` | access profiles: a profile only reaches its domains, private conversations |
| `test_demo_reset.py` | the demo reset, the administration overview |

A new domain is covered by `test_domains.py` as soon as it is registered in `app/domains/__init__.py`
(the `domain` fixture runs those tests for every domain).

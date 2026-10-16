"""The text handling of the server (no model needed):
    podman run --rm -v ./guardrails/gliner-server:/src:ro,Z -w /src registry.access.redhat.com/ubi9/python-312 \
      bash -c "pip install -q fastapi pytest && python -m pytest -q -p no:cacheprovider test_server.py"
"""
from server import PRONOUNS, chunks, tagged, without_overlaps

TEXT = "Le sinistre de Jean Martin a été déclaré à Lyon. " * 20


def test_chunks_cover_the_text_and_overlap():
    pieces = list(chunks(TEXT, 120, 40))
    assert pieces[0][0] == 0 and pieces[-1][0] + len(pieces[-1][1]) == len(TEXT)
    for (offset, chunk), (next_offset, _) in zip(pieces, pieces[1:]):
        assert TEXT[offset:offset + len(chunk)] == chunk and next_offset < offset + len(chunk)


def test_a_name_seen_twice_is_kept_once_and_every_occurrence_stays():
    jean = {"suggested_label": "person", "value": "Jean Martin"}
    found = [{**jean, "start_position": 15, "end_position": 26, "score": 0.9},
             {**jean, "start_position": 15, "end_position": 26, "score": 0.8},     # the next chunk saw it too
             {**jean, "start_position": 64, "end_position": 75, "score": 0.7}]     # a second occurrence
    kept = without_overlaps(found)
    assert [(e["start_position"], e["score"]) for e in kept] == [(15, 0.9), (64, 0.7)]


def test_tagged_text():
    entity = {"suggested_label": "person", "start_position": 15, "end_position": 26}
    assert tagged("Le sinistre de Jean Martin.", [entity]) == "Le sinistre de [Jean Martin](person)."


def test_pronouns_are_not_names():
    assert {"je", "vous", "i", "we"} <= PRONOUNS and "marie" not in PRONOUNS

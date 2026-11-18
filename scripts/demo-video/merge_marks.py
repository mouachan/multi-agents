"""Replaces scenes of a recording by the same scenes of a retake, so montage.py uses the retake.

usage: python merge_marks.py <base dir> <retake dir>:<scene>[,<scene>...] [...]
  e.g. python merge_marks.py /work/out/rec /work/out/rec-retake:review,mlflow

The base marks.json is saved once as marks.orig.json; video paths of the retake are made relative to the base.
"""
import json
import os
import shutil
import sys

base = sys.argv[1]
target = os.path.join(base, "marks.json")
if not os.path.exists(os.path.join(base, "marks.orig.json")):
    shutil.copy(target, os.path.join(base, "marks.orig.json"))
merged = json.load(open(target))
for arg in sys.argv[2:]:
    retake, names = arg.split(":")
    scenes = json.load(open(os.path.join(retake, "marks.json")))
    for name in names.split(","):
        scene = dict(scenes["scenes"][name])
        scene["video"] = os.path.relpath(os.path.join(retake, scene["video"]), base)
        merged["scenes"][name] = scene
        print(f"{name}: {scene['video']}")
    merged["info"].update(scenes.get("info", {}))
json.dump(merged, open(target, "w"), indent=2)

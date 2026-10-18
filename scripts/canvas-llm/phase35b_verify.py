#!/usr/bin/env python3
"""Phase 3.5B final live verification (GET-only)."""
from __future__ import annotations
import json, sys, urllib.request
sys.path.insert(0, "/Users/owen/Projects/teacher-ai-workstation")
from scripts.canvas_llm_phase22 import canvas_credentials as cred

c = cred.resolve_credentials()
base = c["CANVAS_BASE_URL"].rstrip("/")
tok = c["CANVAS_TOKEN"]

def get(path):
    req = urllib.request.Request(base + path, headers={"Authorization": "Bearer " + tok, "Accept": "application/json"}, method="GET")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "{}")

print("=== FRONT PAGES ===")
for cid, name in [(26404, "Math"), (26442, "Reading/Spelling"), (28171, "Language Arts"), (28165, "History"), (28166, "Science")]:
    fp = get("/api/v1/courses/%d/front_page" % cid)
    print("  %s: %s | published=%s" % (name, fp.get("title"), fp.get("published")))

print("=== ASSIGNMENTS (Q2W1, duplicate check) ===")
expected = {
    26404: ["SM5: Lesson 31 Homework", "SM5: Lesson 32 Classwork", "SM5: Lesson 33 Homework", "SM5: Lesson 34 Classwork"],
    26442: ["RM4: Lesson 37 Workbook", "RM4: Lesson 38 Workbook and Comprehension", "RM4: Lesson 39 Workbook", "RM4: Lesson 40 Workbook and Comprehension", "RM4: Mastery Test 4", "RM4: Fluency Checkout 4", "RM4: Spelling Test 35"],
    28171: ["Classroom Practice 19"],
}
for cid, titles in expected.items():
    items = get("/api/v1/courses/%d/assignments?per_page=100" % cid)
    names = [a.get("name") for a in items if isinstance(a, dict)]
    for t in titles:
        cnt = names.count(t)
        print("  [%d] %s: %s" % (cid, t, "OK" if cnt == 1 else "DUP/ISSUE(%d)" % cnt))

print("=== HOMEROOM ===")
hfp = get("/api/v1/courses/26429/front_page")
body = hfp.get("body") or ""
print("  front page: %s | published=%s | Track2=%s | FallWeather=%s" % (hfp.get("title"), hfp.get("published"), "Track 2, Week 1" in body, "Fall Weather" in body))

print("=== STAMP-SHEET ===")
anns = get("/api/v1/courses/26429/discussion_topics?per_page=100&only_announcements=true")
stamps = [a for a in anns if a.get("title") == "Stamp Sheet Update - Track 2"]
print("  stamp-sheet count: %d" % len(stamps))
for s in stamps:
    print("    id=%s delayed_post_at=%s" % (s.get("id"), s.get("delayed_post_at")))

print("=== SUBJECT ANNOUNCEMENTS (duplicate check) ===")
subj = {
    26442: ["Spelling Test 35 - Thursday, October 15", "Reminder - Spelling Test 35 Tomorrow", "Reading Mastery Test 4 and Fluency Checkout 4 - Friday, October 16", "Reminder - Reading Test and Checkout Tomorrow", "Reading/Spelling Canvas Weekly Update"],
    26404: ["Math Canvas Weekly Update"],
    28171: ["Language Arts Canvas Weekly Update"],
    28166: ["Science Canvas Weekly Update"],
}
for cid, titles in subj.items():
    a = get("/api/v1/courses/%d/discussion_topics?per_page=100&only_announcements=true" % cid)
    names = [x.get("title") for x in a if isinstance(x, dict)]
    for t in titles:
        print("  [%d] %s: %d" % (cid, t, names.count(t)))

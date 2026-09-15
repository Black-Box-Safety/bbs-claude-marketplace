#!/usr/bin/env python3
"""Sibling-discrimination eval.

skill-creator's run_eval.py registers ONE description and asks "did it fire?".
That cannot answer the question that actually matters when 14 skills share a
desk: given a query, WHICH of the competing descriptions wins?

This registers every competing description simultaneously as a command stub in
an isolated project root, runs `claude -p <query>`, and records which one the
model reached for. Output is a per-query distribution over winners.

Usage:
  python3 discriminate.py --skills skills.json --queries queries.json \
      --runs 5 --workers 10 --out results.json
"""
import argparse
import base64
import json
import os
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

NONE = "__none__"

# Minimal real files so an attachment-dependent skill can actually fire.
# Without them the model routes correctly in prose ("I'll run it through
# grainger-screenshot") but never invokes the tool, which scores as a miss.
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
    "z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
MIN_PDF = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
           b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
           b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
           b"trailer<</Root 1 0 R>>\n%%EOF\n")


def write_fixture(root: Path, name: str) -> None:
    path = root / name
    if name.lower().endswith(".png"):
        path.write_bytes(PNG_1X1)
    elif name.lower().endswith(".pdf"):
        path.write_bytes(MIN_PDF)
    else:
        path.write_text("placeholder\n")


def opaque_names(skills: dict) -> dict:
    """skill_key -> opaque stub name, so only the description carries signal."""
    return {k: f"skill-{chr(ord('a') + i)}" for i, k in enumerate(sorted(skills))}


def build_root(skills: dict, root: Path, alias: dict | None = None) -> dict:
    """Write one command stub per skill. Returns {command_name: skill_key}.

    Names are bare (no random suffix): the model normalizes a long hex suffix
    away before emitting the skill name, which made suffixed matching miss.
    The field is isolated with --setting-sources so bare names cannot collide
    with the operator's account-synced skills.
    """
    cmd_dir = root / ".claude" / "commands"
    cmd_dir.mkdir(parents=True, exist_ok=True)
    mapping = {}
    for key, desc in skills.items():
        cmd_name = (alias or {}).get(key, key)
        mapping[cmd_name] = key
        indented = "\n  ".join(desc.split("\n"))
        (cmd_dir / f"{cmd_name}.md").write_text(
            f"---\ndescription: |\n  {indented}\n---\n\n"
            f"# {cmd_name}\n\nThis skill handles: {desc}\n"
        )
    return mapping


def winner_from_stream(process, mapping, timeout):
    """Return the skill key of the first skill/command invoked, or NONE."""
    buffer = ""
    pending = None
    acc = ""
    start = time.time()

    def match(text):
        """Resolve the invoked skill from a (possibly partial) JSON input blob.

        Reads the "skill"/"file_path"/"command" value rather than scanning the
        whole blob, so a skill named in free-text args cannot be mistaken for
        the skill actually invoked.
        """
        m = re.search(r'"(?:skill|command|file_path)"\s*:\s*"([^"]*)', text)
        if not m:
            return None
        val = m.group(1)
        for cmd_name, key in mapping.items():
            if cmd_name in val:
                return key
        return None

    while time.time() - start < timeout:
        if process.poll() is not None:
            rest = process.stdout.read()
            if rest:
                buffer += rest.decode("utf-8", errors="replace")
            break
        ready, _, _ = select.select([process.stdout], [], [], 1.0)
        if not ready:
            continue
        chunk = os.read(process.stdout.fileno(), 8192)
        if not chunk:
            break
        buffer += chunk.decode("utf-8", errors="replace")

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("type") == "stream_event":
                se = event.get("event", {})
                t = se.get("type", "")
                if t == "content_block_start":
                    cb = se.get("content_block", {})
                    if cb.get("type") == "tool_use":
                        if cb.get("name", "") in ("Skill", "Read", "SlashCommand"):
                            pending, acc = cb.get("name"), ""
                        else:
                            pending, acc = None, ""
                elif t == "content_block_delta" and pending:
                    d = se.get("delta", {})
                    if d.get("type") == "input_json_delta":
                        acc += d.get("partial_json", "")
                        hit = match(acc)
                        if hit:
                            return hit
                elif t == "content_block_stop" and pending:
                    hit = match(acc)
                    if hit:
                        return hit
                    pending, acc = None, ""
                elif t == "message_stop":
                    pass

            elif event.get("type") == "assistant":
                for item in event.get("message", {}).get("content", []):
                    if item.get("type") != "tool_use":
                        continue
                    blob = json.dumps(item.get("input", {}))
                    hit = match(blob)
                    if hit:
                        return hit

            elif event.get("type") == "result":
                return NONE
    return NONE


def run_one(query: str, skills: dict, timeout: int, model: str | None,
            files: list | None = None, alias: dict | None = None) -> str:
    root = Path(tempfile.mkdtemp(prefix="disc-"))
    try:
        mapping = build_root(skills, root, alias)
        for name in (files or []):
            write_fixture(root, name)
        cmd = ["claude", "-p", query, "--output-format", "stream-json",
               "--verbose", "--include-partial-messages",
               # Exclude user-level settings so the operator's account-synced
               # copies of these same skills are not also in the field.
               "--setting-sources", "project,local"]
        if model:
            cmd += ["--model", model]
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, cwd=str(root),
                                env=env, stdin=subprocess.DEVNULL)
        try:
            return winner_from_stream(proc, mapping, timeout)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
    except Exception as e:  # noqa: BLE001
        print(f"warn: {query[:50]}: {e}", file=sys.stderr)
        return NONE
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills", required=True)
    ap.add_argument("--queries", required=True)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--anonymize", action="store_true",
                    help="replace stub names with opaque tokens so the "
                         "description alone carries the routing signal")
    args = ap.parse_args()

    skills = json.loads(Path(args.skills).read_text())
    queries = json.loads(Path(args.queries).read_text())

    alias = opaque_names(skills) if args.anonymize else None

    jobs = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {}
        for q in queries:
            for _ in range(args.runs):
                f = ex.submit(run_one, q["query"], skills, args.timeout,
                              args.model, q.get("files"), alias)
                futs[f] = q["id"]
        for f in as_completed(futs):
            jobs.append((futs[f], f.result()))

    by_id = {}
    for qid, winner in jobs:
        by_id.setdefault(qid, []).append(winner)

    results = []
    correct = 0
    for q in queries:
        winners = by_id.get(q["id"], [])
        dist = {}
        for w in winners:
            dist[w] = dist.get(w, 0) + 1
        n = len(winners) or 1
        hits = sum(1 for w in winners if w == q["expect"])
        rate = hits / n
        ok = rate >= 0.8
        correct += ok
        results.append({
            "id": q["id"], "query": q["query"], "expect": q["expect"],
            "runs": n, "correct": hits, "accuracy": round(rate, 2),
            "pass": ok,
            "distribution": dict(sorted(dist.items(), key=lambda kv: -kv[1])),
        })

    out = {
        "model": args.model or "default",
        "anonymized": bool(args.anonymize),
        "runs_per_query": args.runs,
        "pass_threshold": 0.8,
        "summary": {"queries": len(queries), "passed": correct,
                    "failed": len(queries) - correct},
        "results": sorted(results, key=lambda r: r["accuracy"]),
    }
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"{correct}/{len(queries)} queries routed correctly "
          f"(>= 80% of {args.runs} runs)")
    for r in out["results"]:
        mark = "PASS" if r["pass"] else "FAIL"
        print(f"  [{mark}] {r['accuracy']:.0%} want={r['expect']:<22} "
              f"got={r['distribution']}  | {r['query'][:60]}")


if __name__ == "__main__":
    main()

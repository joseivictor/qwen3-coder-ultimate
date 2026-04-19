"""
QWEN3-CODER ULTIMATE — Model Feeding Script v1.0
Downloads and processes top coding datasets from HuggingFace to feed the model.
Strategy: Pull best-in-class datasets → convert to few-shot examples → inject into PromptEngine.

Datasets targeted (public, high quality):
  - bigcode/the-stack-v2-train-smol-ids  (code, all languages)
  - iamtarun/python_code_instructions_18k_alpaca  (Python instruction-following)
  - TokenBender/code_instructions_122k_alpaca_style  (multi-lang instructions)
  - Anthropic/hh-rlhf  (helpful/harmless — reasoning quality)
  - nickrosh/Evol-Instruct-Code-80k-v1  (evolved code instructions)
  - ajibawa-2023/Code-74k-ShareGPT  (ShareGPT code)
  - ise-uiuc/Magicoder-OSS-Instruct-75K  (OSS-Instruct — real GitHub issues)
"""

import json
import os
import sys
import sqlite3
import time
import hashlib
import argparse
from pathlib import Path

SCRIPT_DIR   = Path(__file__).parent.parent  # project root
DB_PATH      = SCRIPT_DIR / "qwen_prompt_engine.db"
CACHE_DIR    = SCRIPT_DIR / ".dataset_cache"

# Datasets and how many examples to pull from each
DATASETS = [
    {
        "id":      "iamtarun/python_code_instructions_18k_alpaca",
        "split":   "train",
        "max":     3000,
        "format":  "alpaca",         # has instruction, input, output
        "task_type": "code_generation",
        "lang":    "python",
    },
    {
        "id":      "TokenBender/code_instructions_122k_alpaca_style",
        "split":   "train",
        "max":     3000,
        "format":  "alpaca",
        "task_type": "code_generation",
        "lang":    "mixed",
    },
    {
        "id":      "nickrosh/Evol-Instruct-Code-80k-v1",
        "split":   "train",
        "max":     3000,
        "format":  "evol",           # has instruction, output
        "task_type": "code_generation",
        "lang":    "mixed",
    },
    {
        "id":      "ise-uiuc/Magicoder-OSS-Instruct-75K",
        "split":   "train",
        "max":     2000,
        "format":  "magicoder",      # has problem, solution
        "task_type": "bug_fix",
        "lang":    "mixed",
    },
    {
        "id":      "ajibawa-2023/Code-74k-ShareGPT",
        "split":   "train",
        "max":     2000,
        "format":  "sharegpt",       # has conversations[]
        "task_type": "code_generation",
        "lang":    "mixed",
    },
]

QUALITY_KEYWORDS = {
    "bug_fix":        ["fix", "bug", "error", "issue", "problem", "incorrect", "wrong", "fail"],
    "refactoring":    ["refactor", "improve", "optimize", "clean", "simplify", "restructure"],
    "testing":        ["test", "unittest", "pytest", "assert", "coverage", "mock"],
    "security":       ["security", "vulnerability", "injection", "xss", "csrf", "auth"],
    "code_generation":["create", "implement", "write", "generate", "build", "develop"],
    "explanation":    ["explain", "why", "how", "what", "describe", "understand"],
}


def setup_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prompt_examples (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type   TEXT NOT NULL,
            user_input  TEXT NOT NULL,
            response    TEXT NOT NULL,
            quality     REAL DEFAULT 0.5,
            usage_count INTEGER DEFAULT 0,
            source      TEXT DEFAULT '',
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_task ON prompt_examples(task_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_quality ON prompt_examples(quality)")
    conn.commit()
    return conn


def detect_task_type(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for task, keywords in QUALITY_KEYWORDS.items():
        scores[task] = sum(1 for kw in keywords if kw in text_lower)
    return max(scores, key=scores.get) if any(scores.values()) else "code_generation"


def estimate_quality(instruction: str, response: str) -> float:
    score = 0.5

    # Length checks
    if len(response) > 200:
        score += 0.1
    if len(response) > 1000:
        score += 0.1
    if len(instruction) > 30:
        score += 0.1

    # Code presence
    if "```" in response or "def " in response or "class " in response:
        score += 0.15

    # Explanation presence
    if any(w in response.lower() for w in ["because", "therefore", "note that", "this"]):
        score += 0.05

    # Penalize very short responses
    if len(response) < 50:
        score -= 0.3

    return min(1.0, max(0.0, score))


def parse_alpaca(row: dict) -> tuple[str, str]:
    instruction = row.get("instruction", "")
    inp         = row.get("input", "")
    output      = row.get("output", "")
    user = instruction + ("\n\n" + inp if inp else "")
    return user.strip(), output.strip()


def parse_evol(row: dict) -> tuple[str, str]:
    return row.get("instruction", "").strip(), row.get("output", "").strip()


def parse_magicoder(row: dict) -> tuple[str, str]:
    return row.get("problem", "").strip(), row.get("solution", "").strip()


def parse_sharegpt(row: dict) -> tuple[str, str]:
    convs = row.get("conversations", [])
    if len(convs) < 2:
        return "", ""
    human = next((c["value"] for c in convs if c.get("from") == "human"), "")
    gpt   = next((c["value"] for c in convs if c.get("from") in ("gpt", "assistant")), "")
    return human.strip(), gpt.strip()


PARSERS = {
    "alpaca":    parse_alpaca,
    "evol":      parse_evol,
    "magicoder": parse_magicoder,
    "sharegpt":  parse_sharegpt,
}


def dedup_hash(text: str) -> str:
    return hashlib.md5(text[:300].encode()).hexdigest()


def feed_dataset(conn: sqlite3.Connection, ds_cfg: dict, dry_run: bool = False) -> int:
    try:
        from datasets import load_dataset
    except ImportError:
        print("[ERROR] 'datasets' not installed. Run: pip install datasets")
        return 0

    ds_id     = ds_cfg["id"]
    split     = ds_cfg.get("split", "train")
    max_rows  = ds_cfg.get("max", 1000)
    fmt       = ds_cfg.get("format", "alpaca")
    task_type = ds_cfg.get("task_type", "code_generation")
    source    = ds_id.split("/")[-1]
    parser    = PARSERS.get(fmt, parse_alpaca)

    print(f"\n[FEED] Loading {ds_id} ({split}, max {max_rows})...")

    try:
        dataset = load_dataset(ds_id, split=split, streaming=True, trust_remote_code=True)
    except Exception as e:
        print(f"[SKIP] {ds_id}: {e}")
        return 0

    inserted = 0
    seen     = set()

    for i, row in enumerate(dataset):
        if inserted >= max_rows:
            break

        try:
            user_input, response = parser(row)
        except Exception:
            continue

        if not user_input or not response:
            continue
        if len(user_input) < 10 or len(response) < 20:
            continue

        h = dedup_hash(user_input)
        if h in seen:
            continue
        seen.add(h)

        actual_task = detect_task_type(user_input) if task_type == "auto" else task_type
        quality     = estimate_quality(user_input, response)

        if quality < 0.4:
            continue

        if not dry_run:
            try:
                conn.execute(
                    "INSERT INTO prompt_examples (task_type, user_input, response, quality, source) VALUES (?,?,?,?,?)",
                    (actual_task, user_input[:4000], response[:8000], quality, source),
                )
                if inserted % 100 == 0:
                    conn.commit()
                    print(f"  [{inserted}/{max_rows}] inserted...")
            except Exception as e:
                print(f"  [ERR] {e}")
                continue

        inserted += 1

    conn.commit()
    print(f"[FEED] {ds_id}: {inserted} examples inserted (task={task_type})")
    return inserted


def show_stats(conn: sqlite3.Connection):
    rows = conn.execute("""
        SELECT task_type, COUNT(*) as n, AVG(quality) as q
        FROM prompt_examples
        GROUP BY task_type
        ORDER BY n DESC
    """).fetchall()
    print("\n[STATS] PromptEngine DB:")
    total = 0
    for task, n, q in rows:
        print(f"  {task:<25} {n:>6} examples | avg quality {q:.2f}")
        total += n
    print(f"  {'TOTAL':<25} {total:>6}")


def main():
    parser = argparse.ArgumentParser(description="Feed QWEN PromptEngine with HuggingFace datasets")
    parser.add_argument("--datasets", nargs="+", help="Dataset IDs to load (default: all)")
    parser.add_argument("--max", type=int, default=None, help="Override max examples per dataset")
    parser.add_argument("--dry-run", action="store_true", help="Parse but don't insert")
    parser.add_argument("--stats", action="store_true", help="Show DB stats and exit")
    parser.add_argument("--clear", action="store_true", help="Clear DB before feeding")
    args = parser.parse_args()

    CACHE_DIR.mkdir(exist_ok=True)
    conn = setup_db()

    if args.stats:
        show_stats(conn)
        return

    if args.clear:
        conn.execute("DELETE FROM prompt_examples")
        conn.commit()
        print("[CLEAR] Prompt examples table cleared.")

    targets = DATASETS
    if args.datasets:
        targets = [d for d in DATASETS if any(a in d["id"] for a in args.datasets)]
        if not targets:
            print(f"[WARN] No matching datasets for: {args.datasets}")
            return

    total = 0
    t0    = time.time()

    for ds in targets:
        cfg = dict(ds)
        if args.max:
            cfg["max"] = args.max
        total += feed_dataset(conn, cfg, dry_run=args.dry_run)

    elapsed = time.time() - t0
    print(f"\n[DONE] {total} examples inserted in {elapsed:.1f}s")
    show_stats(conn)
    conn.close()


if __name__ == "__main__":
    main()

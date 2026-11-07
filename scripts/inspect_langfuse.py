"""Inspect recent Langfuse traces and prompt payloads directly from CLI."""

import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from src.config import load_env_file

load_env_file(Path(".env"))

pk = os.getenv("LANGFUSE_PUBLIC_KEY")
sk = os.getenv("LANGFUSE_SECRET_KEY")
host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")


def inspect_recent(limit: int = 5):
    if not pk or not sk:
        print("[!] Langfuse API keys are not set in .env")
        return

    print(f"Connecting to Langfuse Host: {host} ...")
    resp = httpx.get(f"{host}/api/public/v2/observations?limit={limit}", auth=(pk, sk))
    if resp.status_code != 200:
        print(f"[!] Failed to fetch observations: {resp.status_code} - {resp.text}")
        return

    items = resp.json().get("data", [])
    print(f"=== Found {len(items)} Recent Observations ===\n")

    for i, it in enumerate(items, 1):
        name = it.get("name")
        obs_type = it.get("type")
        model = it.get("model")
        start = it.get("startTime")
        trace_id = it.get("traceId")
        print(f"[{i}] {name} ({obs_type})")
        print(f"    - Model: {model} | Time: {start} | TraceID: {trace_id}")

        # If generation, fetch full trace to show input & output
        if obs_type and obs_type.upper() == "GENERATION" and trace_id:
            trace_resp = httpx.get(f"{host}/api/public/traces/{trace_id}", auth=(pk, sk))
            if trace_resp.status_code == 200:
                tdata = trace_resp.json()
                for o in tdata.get("observations", []):
                    if o.get("name") == name or o.get("id") == it.get("id"):
                        inp = o.get("input")
                        out = o.get("output")
                        print("\n    >>> [PROMPT INPUT]:")
                        if isinstance(inp, dict):
                            print(json.dumps(inp, ensure_ascii=False, indent=6))
                        else:
                            print(f"      {inp}")
                        print("\n    <<< [LLM OUTPUT]:")
                        if isinstance(out, (dict, list)):
                            print(json.dumps(out, ensure_ascii=False, indent=6))
                        else:
                            print(f"      {str(out)[:500]}...")
                        break
        print("-" * 60)


if __name__ == "__main__":
    inspect_recent(limit=5)

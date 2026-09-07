"""
OmniRoute Gateway Management and Verification Script
"""
import json
import subprocess
import sys
import time
import urllib.request

import os

BASE_URL = os.environ.get("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1")
API_KEY = os.environ.get("OMNIROUTE_API_KEY", "omniroute-local-key")


def is_server_running(url=f"{BASE_URL}/models"):
    try:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def ensure_server():
    if is_server_running():
        print("OmniRoute server is active and listening on port 20128.")
        return True

    print("Starting OmniRoute server on port 20128...")
    subprocess.Popen(
        ["omniroute", "serve", "--port", "20128", "--no-open", "--no-tray"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=True,
    )

    for i in range(15):
        time.sleep(1)
        if is_server_running():
            print(f"OmniRoute server successfully started and responsive after {i+1}s.")
            return True
        print(".", end="", flush=True)

    print("\nFailed to verify OmniRoute server startup within 15s.")
    return False


def verify_combos():
    url = f"{BASE_URL}/chat/completions"
    combos = ["combo/coder", "combo/planner", "combo/fast"]
    results = {}
    for c in combos:
        payload = {
            "model": c,
            "messages": [{"role": "user", "content": "Respond: OK"}],
            "temperature": 0,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                reply = body["choices"][0]["message"]["content"].strip()
                results[c] = f"PASS ({reply[:20]})"
        except Exception as exc:
            results[c] = f"FAIL ({exc})"

    print("\nCOMBO VERIFICATION:")
    for c, status in results.items():
        print(f"  {c}: {status}")


def main():
    print("=" * 60)
    print("OMNIROUTE GATEWAY HEALTH & VERIFICATION")
    print("=" * 60)
    running = ensure_server()
    if running:
        verify_combos()
    print("=" * 60)


if __name__ == "__main__":
    main()

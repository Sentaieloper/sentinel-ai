"""Sentinel AI — combined process launcher for Railway.

Spawns chain_reader (Node, port 8003) and drift_reader (Node, port 8002)
as background subprocesses, then exec's uvicorn for FastAPI on $PORT.
FastAPI proxies internal requests to the Node services on localhost.
"""
import os
import signal
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
CHAIN_PORT = "8003"
DRIFT_PORT = "8002"
WEB_PORT = os.environ.get("PORT", "8001")

procs = []


def spawn(label, cmd, cwd, port):
    env = os.environ.copy()
    env["PORT"] = port
    print(f"[start] launching {label} on :{port}", flush=True)
    p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=sys.stdout, stderr=sys.stdout)
    procs.append((label, p))


def shutdown(*_):
    print("[start] shutdown signal received", flush=True)
    for label, p in procs:
        try:
            p.terminate()
        except Exception:
            pass
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    spawn("chain_reader", ["node", "server.js"], os.path.join(ROOT, "chain_reader"), CHAIN_PORT)
    spawn("drift_reader", ["node", "server.js"], os.path.join(ROOT, "drift_reader"), DRIFT_PORT)

    os.environ.setdefault("CHAIN_READER_URL", f"http://127.0.0.1:{CHAIN_PORT}")
    os.environ.setdefault("DRIFT_READER_URL", f"http://127.0.0.1:{DRIFT_PORT}")

    time.sleep(2)
    for label, p in procs:
        if p.poll() is not None:
            print(f"[start] {label} exited early with code {p.returncode}", flush=True)

    print(f"[start] launching uvicorn on :{WEB_PORT}", flush=True)
    os.execvpe(
        "uvicorn",
        ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", WEB_PORT],
        os.environ,
    )


if __name__ == "__main__":
    main()

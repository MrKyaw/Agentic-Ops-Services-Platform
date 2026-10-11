#!/usr/bin/env python3
"""Preflight port check: pick free host ports, never kill anything.

Writes chosen ports to .env.local (git-ignored) and prints the URL map.
Usage: python3 infra/scripts/preflight.py [--check-only]
"""

import os
import socket
import sys

DEFAULTS = {
    "API_PORT": 8000,
    "FRONTEND_PORT": 4200,
    "DB_PORT": 5432,
    "NEO4J_HTTP_PORT": 7474,
    "NEO4J_BOLT_PORT": 7687,
}
RANGE = 20
TARGET = os.path.join(os.path.dirname(__file__), "..", "..", ".env.local")


def is_free(port: int) -> bool:
    for host in ("0.0.0.0", "127.0.0.1"):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                return False
    return True


def pick(name: str, default: int) -> int:
    override = os.environ.get(name)
    if override:
        port = int(override)
        if not is_free(port):
            print(
                f"ERROR: {name}={port} is occupied; refusing to kill anything. Unset it or free the port.",
                file=sys.stderr,
            )
            sys.exit(1)
        return port
    for port in range(default, default + RANGE):
        if is_free(port):
            return port
    print(
        f"ERROR: no free port for {name} in {default}..{default + RANGE - 1}",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    check_only = "--check-only" in sys.argv
    existing: dict[str, str] = {}
    if os.path.exists(TARGET):
        with open(TARGET, encoding="utf-8") as fh:
            for line in fh:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    existing[key.strip()] = value.strip()
    chosen = {name: pick(name, default) for name, default in DEFAULTS.items()}
    for name, port in chosen.items():
        status = "default" if port == DEFAULTS[name] else "shifted (default busy)"
        print(f"{name}={port} [{status}]")
    print(f"API -> http://localhost:{chosen['API_PORT']}/docs")
    if check_only:
        return
    merged = dict(existing)
    for name, port in chosen.items():
        merged[name] = str(port)
    with open(TARGET, "w", encoding="utf-8") as fh:
        for key, value in merged.items():
            fh.write(f"{key}={value}\n")
    print(f"wrote {TARGET}")


if __name__ == "__main__":
    main()

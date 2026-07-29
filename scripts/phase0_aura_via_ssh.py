"""Run Aura capacity check inside OncoBridge container (read-only)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "phase0_aura_capacity.py"

REMOTE = r"""
set -euo pipefail
C=$(docker ps -qf name=gq03pdvpvvtkzugkdmw8j2z3 | head -1)
echo "container=$C"
test -n "$C"
docker cp /tmp/phase0_aura_capacity.py "$C":/tmp/phase0_aura_capacity.py
docker exec "$C" python /tmp/phase0_aura_capacity.py
docker exec "$C" rm -f /tmp/phase0_aura_capacity.py
rm -f /tmp/phase0_aura_capacity.py
"""


def main() -> int:
    scp = subprocess.run(
        ["scp", str(SCRIPT), "eurthtech:/tmp/phase0_aura_capacity.py"],
        capture_output=True,
        text=True,
    )
    if scp.returncode:
        print(scp.stderr, file=sys.stderr)
        return scp.returncode
    run = subprocess.run(
        ["ssh", "eurthtech", "bash", "-s"],
        input=REMOTE.replace("\r\n", "\n").encode("utf-8"),
        capture_output=True,
    )
    sys.stdout.buffer.write(run.stdout)
    if run.returncode:
        sys.stderr.buffer.write(run.stderr)
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())

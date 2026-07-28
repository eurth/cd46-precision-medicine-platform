"""Research export pack: CSV results + freeze + NOTICE + CITATION."""
from __future__ import annotations

import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
_FREEZE = _ROOT / "config" / "data_freeze.yaml"
_NOTICE = _ROOT / "NOTICE"
_CITATION = _ROOT / "CITATION.cff"

ROW_CAP = 500
QUERY_TIMEOUT_S = 15


def build_export_pack(
    df: pd.DataFrame,
    *,
    active_target: str = "CD46",
    result_name: str = "query_results.csv",
) -> bytes:
    """Zip: results CSV + data_freeze.yaml + NOTICE + CITATION.cff + README.txt."""
    freeze_text = _FREEZE.read_text(encoding="utf-8") if _FREEZE.exists() else ""
    freeze_id = "unknown"
    for line in freeze_text.splitlines():
        if line.strip().startswith("freeze_id:"):
            freeze_id = line.split(":", 1)[1].strip().strip('"').strip("'")
            break

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    readme = (
        f"OncoBridge Intelligence — research export pack\n"
        f"generated_utc: {ts}\n"
        f"active_target: {active_target}\n"
        f"freeze_id: {freeze_id}\n"
        f"rows: {len(df)}\n"
        f"\n"
        f"Contents:\n"
        f"  {result_name} — query result table\n"
        f"  data_freeze.yaml — provenance freeze\n"
        f"  NOTICE — third-party licenses\n"
        f"  CITATION.cff — software citation\n"
        f"\n"
        f"Research use only. Not clinical advice.\n"
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(result_name, df.to_csv(index=False))
        if freeze_text:
            zf.writestr("data_freeze.yaml", freeze_text)
        if _NOTICE.exists():
            zf.writestr("NOTICE", _NOTICE.read_text(encoding="utf-8"))
        if _CITATION.exists():
            zf.writestr("CITATION.cff", _CITATION.read_text(encoding="utf-8"))
        zf.writestr("README.txt", readme)
    return buf.getvalue()


def ensure_cypher_limit(cypher: str, limit: int = ROW_CAP) -> str:
    """Append LIMIT if the query has no LIMIT clause (case-insensitive)."""
    stripped = cypher.strip().rstrip(";")
    if "LIMIT" in stripped.upper():
        return stripped
    return f"{stripped}\nLIMIT {limit}"


def assert_export_pack() -> None:
    """ponytail: zip must contain freeze_id + NOTICE."""
    df = pd.DataFrame([{"a": 1}])
    raw = build_export_pack(df, active_target="CD46")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = set(zf.namelist())
        assert "query_results.csv" in names
        assert "data_freeze.yaml" in names
        assert "NOTICE" in names
        assert "CITATION.cff" in names
        assert "README.txt" in names
        readme = zf.read("README.txt").decode("utf-8")
        assert "freeze_id:" in readme
    capped = ensure_cypher_limit("MATCH (n) RETURN n")
    assert "LIMIT 500" in capped
    assert "LIMIT" in ensure_cypher_limit("MATCH (n) RETURN n LIMIT 10").upper()


if __name__ == "__main__":
    assert_export_pack()
    print("export_pack_ok")

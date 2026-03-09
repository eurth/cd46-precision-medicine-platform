"""Re-fetch all Open Targets CD46 disease associations (size=772) and save to disk."""
import json
import sys
import urllib.request
from pathlib import Path

GRAPHQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"
ENSEMBL_ID = "ENSG00000117335"  # CD46
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "apis" / "open_targets_cd46.json"

QUERY = (
    "query CD46Diseases($ensemblId: String!) {"
    " target(ensemblId: $ensemblId) {"
    "  id approvedSymbol"
    "  associatedDiseases(page: {index: 0, size: 772}) {"
    "   count"
    "   rows {"
    "    disease { id name therapeuticAreas { id name } }"
    "    score"
    "    datasourceScores { id score }"
    "   }"
    "  }"
    " }"
    "}"
)

payload = json.dumps({"query": QUERY, "variables": {"ensemblId": ENSEMBL_ID}}).encode("utf-8")
req = urllib.request.Request(
    GRAPHQL_URL,
    data=payload,
    headers={"Content-Type": "application/json", "Accept": "application/json"},
)

print(f"Fetching CD46 associations from Open Targets (size=772)...")
try:
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print(f"HTTP {e.code}: {e.reason}")
    print(f"Response body: {body[:500]}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

rows = (
    data.get("data", {})
    .get("target", {})
    .get("associatedDiseases", {})
    .get("rows", [])
)
total = (
    data.get("data", {})
    .get("target", {})
    .get("associatedDiseases", {})
    .get("count", 0)
)

print(f"API reports {total} total associations.")
print(f"Fetched {len(rows)} rows in this response.")

OUT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
print(f"Saved to {OUT_PATH}")
print("Now run:  python scripts/load_kg_open_targets.py")

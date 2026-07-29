"""Phase 0 probes: Open Targets GraphQL + S3 release listing (no AWS CLI)."""
from __future__ import annotations

import json
import re
import urllib.request

OT_GQL = "https://api.platform.opentargets.org/api/v4/graphql"
OT_S3 = "https://open-targets-public-data-releases.s3.eu-west-1.amazonaws.com/"


def gql(query: str) -> dict:
    req = urllib.request.Request(
        OT_GQL,
        data=json.dumps({"query": query}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def s3_list(prefix: str = "", delimiter: str = "/", max_keys: int = 40) -> tuple[list[str], list[str]]:
    url = (
        f"{OT_S3}?list-type=2&delimiter={delimiter}&max-keys={max_keys}"
        f"&prefix={urllib.request.quote(prefix)}"
    )
    body = urllib.request.urlopen(url, timeout=60).read().decode("utf-8", errors="replace")
    prefs = re.findall(r"<Prefix>([^<]+)</Prefix>", body)
    keys = re.findall(r"<Key>([^<]+)</Key>", body)
    # CommonPrefixes use nested Prefix
    common = re.findall(r"<CommonPrefixes>\s*<Prefix>([^<]+)</Prefix>", body)
    return common or prefs, keys


def main() -> int:
    meta = gql("query { meta { name apiVersion { x y z } dataVersion { year month } } }")
    print("ot_meta", json.dumps(meta["data"]["meta"]))

    targets = {
        "CD46": "ENSG00000117335",
        "FOLH1_PSMA": "ENSG00000086205",
        "FAP": "ENSG00000078098",
        "SSTR2": "ENSG00000180616",
        "GRPR": "ENSG00000164825",
    }
    for name, ens in targets.items():
        q = (
            "query { target(ensemblId: \"%s\") { approvedSymbol "
            "associatedDiseases { count } } }" % ens
        )
        data = gql(q)
        t = (data.get("data") or {}).get("target")
        if not t:
            print(f"ot_target {name}={ens} MISSING {data}")
            continue
        print(
            f"ot_target {name} symbol={t.get('approvedSymbol')} "
            f"disease_assoc_count={t['associatedDiseases']['count']}"
        )

    print("--- s3 platform releases ---")
    common, _ = s3_list("platform/")
    print("releases", [c for c in common if c.startswith("platform/")][:12])

    latest = "platform/26.06/"
    common2, keys2 = s3_list(latest)
    print(f"latest={latest} prefixes={common2[:25]}")
    print(f"latest_sample_keys={keys2[:10]}")

    # known useful output folders in OT platform dumps
    for sub in ("output/", "output/target/", "output/association/", "output/disease/"):
        c, k = s3_list(latest + sub)
        print(f"s3 {latest}{sub} prefixes={c[:15]} keys={k[:5]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

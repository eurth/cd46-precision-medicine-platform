"""Quick OT GraphQL counts for seed theranostic targets."""
import json
import urllib.request

QUERY = """
query {
  CD46: target(ensemblId: "ENSG00000117335") {
    approvedSymbol
    associatedDiseases { count }
  }
  FOLH1: target(ensemblId: "ENSG00000086205") {
    approvedSymbol
    associatedDiseases { count }
  }
  FAP: target(ensemblId: "ENSG00000078098") {
    approvedSymbol
    associatedDiseases { count }
  }
  SSTR2: target(ensemblId: "ENSG00000180616") {
    approvedSymbol
    associatedDiseases { count }
  }
  GRPR: target(ensemblId: "ENSG00000164825") {
    approvedSymbol
    associatedDiseases { count }
  }
}
"""

req = urllib.request.Request(
    "https://api.platform.opentargets.org/api/v4/graphql",
    data=json.dumps({"query": QUERY}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=90) as resp:
    data = json.loads(resp.read().decode())
print(json.dumps(data, indent=2))

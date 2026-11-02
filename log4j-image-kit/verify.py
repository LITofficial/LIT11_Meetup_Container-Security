"""Compare actual Trivy JSON reports; never infer success from tag names."""
import json
import sys
from pathlib import Path
TARGET = "CVE-2021-44228"
def read(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if raw.get("SchemaVersion") != 2 or not isinstance(raw.get("Results"), list):
        raise ValueError("Unsupported or incomplete Trivy result")
    packages, vulnerabilities = [], []
    for result in raw["Results"]:
        packages.extend(result.get("Packages") or [])
        vulnerabilities.extend(result.get("Vulnerabilities") or [])
    log4j = [p for p in packages if "log4j-core" in str(p.get("Name", ""))]
    target = [v for v in vulnerabilities if v.get("VulnerabilityID") == TARGET and "log4j-core" in str(v.get("PkgName", ""))]
    critical = [v for v in vulnerabilities if v.get("Severity") == "CRITICAL"]
    return log4j, target, critical
if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: py verify.py vulnerable.json patched.json")
    try:
        old, new = read(sys.argv[1]), read(sys.argv[2])
        print("Vulnerable Log4j:", [(p.get("Name"), p.get("Version")) for p in old[0]])
        print("Patched Log4j:", [(p.get("Name"), p.get("Version")) for p in new[0]])
        print("Target CVE findings:", len(old[1]), "->", len(new[1]))
        print("All Critical findings:", len(old[2]), "->", len(new[2]))
        ok = bool(old[0] and new[0] and old[1]) and not new[1] and bool(old[2]) and not new[2]
        print("DEMO READY" if ok else "NOT VERIFIED: inspect reports; do not claim PASS/FAIL demonstration yet")
        sys.exit(0 if ok else 1)
    except Exception as exc:
        print("ERROR:", exc)
        sys.exit(2)

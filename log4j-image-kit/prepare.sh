#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"
command -v docker >/dev/null || { echo "Docker is required." >&2; exit 1; }
command -v python3 >/dev/null || { echo "Python 3 is required." >&2; exit 1; }
mkdir -p images
for name in vulnerable patched; do
    if [ -e "images/$name.tar" ]; then
        echo "Existing archive: images/$name.tar. Move it before running again." >&2
        exit 1
    fi
done

for name in vulnerable patched; do
    case "$name" in
        vulnerable) version="2.14.1" ;;
        patched) version="2.24.3" ;;
    esac
    tag="lit11-log4j:$name"
    docker build -f Dockerfile --build-arg "LOG4J_VERSION=$version" -t "$tag" .
    docker image save -o "images/$name.tar" "$tag"
done

python3 - <<'PY'
import hashlib
import json
import subprocess
from pathlib import Path

metadata = []
for name, version in [("vulnerable", "2.14.1"), ("patched", "2.24.3")]:
    tag = f"lit11-log4j:{name}"
    info = json.loads(subprocess.check_output(
        ["docker", "image", "inspect", tag], text=True
    ))
    digest = hashlib.sha256()
    with Path(f"images/{name}.tar").open("rb") as archive:
        for chunk in iter(lambda: archive.read(1024 * 1024), b""):
            digest.update(chunk)
    metadata.append({
        "tag": tag,
        "log4j_version": version,
        "image_id": info[0]["Id"],
        "archive_sha256": digest.hexdigest().upper(),
    })
Path("images/metadata.json").write_text(
    json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
)
PY

echo "Done. Images were built and saved, NOT started."

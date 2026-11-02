"""Windows용 Trivy 실행 및 Critical 기반 판정. Python 표준 라이브러리만 사용."""
import argparse
import html
import json
import shutil
import subprocess
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent


def assess(raw):
    if raw.get("SchemaVersion") != 2 or not isinstance(raw.get("Results"), list):
        raise ValueError("지원하지 않거나 불완전한 Trivy JSON 형식입니다.")
    rows = []
    for result in raw["Results"]:
        for vuln in result.get("Vulnerabilities") or []:
            rows.append({
                "target": result.get("Target", ""),
                "id": vuln.get("VulnerabilityID", ""),
                "package": vuln.get("PkgName", ""),
                "severity": vuln.get("Severity", "UNKNOWN"),
                "installed": vuln.get("InstalledVersion", ""),
                "fixed": vuln.get("FixedVersion", ""),
            })
    counts = Counter(row["severity"] for row in rows)
    counts = {level: counts.get(level, 0) for level in
              ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")}
    return ("FAIL" if counts["CRITICAL"] else "PASS"), counts, rows


def save_report(folder, summary, rows):
    (folder / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    esc = lambda value: html.escape(str(value))
    table_rows = "".join("<tr>" + "".join("<td>" + esc(row[key]) + "</td>"
        for key in ("target", "id", "package", "severity", "installed", "fixed"))
        + "</tr>" for row in rows)
    document = '''<!doctype html><html lang="ko"><meta charset="utf-8">
<title>Trivy 검사 보고서</title><style>
body{font-family:Arial,sans-serif;margin:32px;color:#17263b}table{border-collapse:collapse;width:100%}
td,th{border:1px solid #ccd5df;padding:8px;text-align:left;overflow-wrap:anywhere}
pre{white-space:pre-wrap}.decision{font-size:32px;font-weight:bold}
</style><h1>컨테이너 이미지 취약점 검사</h1>'''
    document += '<p class="decision">' + esc(summary["decision"]) + '</p>'
    document += '<pre>' + esc(json.dumps(summary, ensure_ascii=False, indent=2)) + '</pre>'
    document += '<p>PASS는 현재 차단 기준을 통과했다는 뜻이며, 모든 취약점이 없거나 안전함을 보장하지 않습니다. '
    document += '수정 버전 정보는 여러 버전 계열을 포함할 수 있으므로 적용 대상과 호환성을 검토하세요.</p>'
    document += '<table><tr><th>대상</th><th>취약점</th><th>패키지</th><th>심각도</th><th>현재 버전</th><th>수정 버전 정보</th></tr>' + table_rows + '</table></html>'
    (folder / "report.html").write_text(document, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Trivy 실행 -> Critical 판정 -> HTML 보고서")
    parser.add_argument("image", nargs="?", help="예: nginx:alpine 또는 my-app:1.0")
    parser.add_argument("--source", choices=["remote", "docker"], default="remote",
                        help="remote: 레지스트리 검사(기본), docker: 로컬 Docker 이미지")
    parser.add_argument("--input", dest="archive", help="이미지 tar 파일 검사")
    parser.add_argument("--timeout", type=int, default=900, help="검사 제한 시간(초)")
    args = parser.parse_args()
    if bool(args.image) == bool(args.archive):
        parser.error("이미지 이름 또는 --input 파일 중 하나만 지정하세요.")
    if args.image and args.image.startswith("-"):
        parser.error("이미지 이름은 '-'로 시작할 수 없습니다.")
    if args.timeout < 1:
        parser.error("timeout은 1 이상이어야 합니다.")
    folder = BASE / "reports" / (datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8])
    folder.mkdir(parents=True)
    rows = []
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "target": args.archive or args.image,
        "source": "archive" if args.archive else args.source,
        "policy": "Critical >= 1이면 FAIL; 검사 오류이면 ERROR",
        "scan_status": "error", "decision": "ERROR",
    }
    try:
        # PATH를 수정하지 않아도 scan.py 옆의 실행 파일을 찾습니다.
        local_exe = BASE / "trivy.exe"
        executable = str(local_exe) if local_exe.is_file() else shutil.which("trivy")
        if not executable:
            raise RuntimeError("trivy.exe를 scan.py와 같은 폴더에 넣어주세요.")
        version = subprocess.run([executable, "--version"], capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=30)
        if version.returncode != 0:
            raise RuntimeError("Trivy 버전 확인 실패: " + version.stderr[-1500:])
        summary["trivy_version"] = version.stdout.strip()
        raw_path = folder / "trivy.json"
        command = [executable, "image", "--scanners", "vuln", "--format", "json",
                   "--output", str(raw_path), "--exit-code", "0",
                   "--timeout", f"{args.timeout}s", "--no-progress"]
        if args.archive:
            archive = Path(args.archive).resolve()
            if not archive.is_file():
                raise RuntimeError("이미지 파일이 없습니다: " + str(archive))
            command += ["--input", str(archive)]
        else:
            command += ["--image-src", args.source, args.image]
        print("검사 중입니다. 첫 실행은 DB 다운로드 때문에 오래 걸릴 수 있습니다.", flush=True)
        # 셸을 통하지 않고 인자 배열로 실행합니다. 오류 로그는 파일로 저장됩니다.
        with (folder / "scan.log").open("w", encoding="utf-8") as log:
            result = subprocess.run(command, stdout=log, stderr=log, timeout=args.timeout + 30)
        if result.returncode != 0:
            raise RuntimeError("Trivy 실행 실패. 이번 보고서 폴더의 scan.log를 확인하세요.")
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        decision, counts, rows = assess(raw)
        summary.update(scan_status="completed", decision=decision, counts=counts,
                       reason="Critical 취약점 발견" if decision == "FAIL" else "현재 차단 기준 통과")
    except subprocess.TimeoutExpired:
        summary["reason"] = "제한 시간 초과. 검사하지 못했으므로 배포를 중단합니다."
    except Exception as exc:
        summary["reason"] = str(exc)
    save_report(folder, summary, rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("보고서:", folder / "report.html")
    return {"PASS": 0, "FAIL": 1, "ERROR": 2}[summary["decision"]]


if __name__ == "__main__":
    sys.exit(main())

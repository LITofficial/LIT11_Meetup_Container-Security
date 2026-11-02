Log4j Trivy demo / Windows PowerShell

[실행 전 필수 준비: trivy.exe를 이 폴더에 넣어주세요]
1. Windows용 Trivy를 공식 배포 페이지에서 다운로드하고 압축을 해제합니다.
   공식 배포 페이지: https://github.com/aquasecurity/trivy/releases/
2. 압축을 푼 파일 중 trivy.exe를 이 README.txt가 있는 폴더에 복사합니다.
   Dockerfile, prepare.ps1, verify.py와 같은 위치에 있어야 합니다.
   trivy.exe를 별도의 하위 폴더에 넣지 마세요.
3. 파일 탐색기에서 이 폴더를 열고 주소 표시줄에 powershell을 입력한 뒤 Enter를 누릅니다.
4. 열린 PowerShell에서 다음 명령으로 Trivy가 실행되는지 확인합니다.
   .\trivy.exe --version
5. 버전이 정상적으로 표시되면 아래 1번 단계부터 진행합니다.
   trivy.exe를 더블클릭하는 것이 아니라, 이 폴더에서 PowerShell 명령으로 실행하세요.

폴더 구성 예시:
log4j-image-kit
  README.txt
  Dockerfile
  prepare.ps1
  verify.py
  trivy.exe    <- 직접 다운로드한 실행 파일을 여기에 넣기
  scan.py      <- HTML 보고서 생성 시 필요

This kit builds two package-detection images, not a running Java web application.
Final images use FROM scratch and contain only log4j-core JAR files.
There are no OS packages, Java runtime, exposed ports, or exploit payloads.
The Maven build stage is not part of the final images.
Vulnerable: Log4j 2.14.1; comparison patched: 2.24.3.
Patched refers to CVE-2021-44228 and is not a guarantee against all present/future CVEs.
Requirements: Docker Desktop (Linux containers), Python 3, trivy.exe.
Place trivy.exe and the previously supplied scan.py beside these files.

1. Build and save (containers are NOT started):
powershell -NoProfile -ExecutionPolicy Bypass -File .\prepare.ps1
Follow organizational policy if script execution is restricted.

2. Inspect and save complete package lists for validation:
.\trivy.exe image --input .\images\vulnerable.tar --scanners vuln --list-all-pkgs --format json --output vulnerable.json
Check $LASTEXITCODE is 0 before proceeding.
.\trivy.exe image --input .\images\patched.tar --scanners vuln --list-all-pkgs --format json --output patched.json
Check $LASTEXITCODE is 0 before proceeding.
py .\verify.py .\vulnerable.json .\patched.json
DEMO READY requires: log4j-core detected in both reports, target CVE present only in vulnerable, Critical present only in vulnerable.
Do not confuse absent findings with successfully identifying the package.

3. Generate the previously supplied HTML report / policy decision:
py .\scan.py --input .\images\vulnerable.tar
py .\scan.py --input .\images\patched.tar
scan.py was supplied earlier; it is not included here.

If patched still has Critical, inspect the actual finding and select a compatible fixed release, then rebuild and re-export. Never edit findings to force PASS.
If Trivy cannot identify the JAR, inspect its log and Java DB downloads.
Missing OS metadata is expected for a scratch image; verify the Java package analysis separately.
These are static package-scan specimens. They do not demonstrate an exploitable running service or actual Azure deployment blocking.

Validation: Python syntax and synthetic JSON comparison tests checked. Docker build, Maven downloads, Windows PowerShell, and real Trivy scans were not executed by the authoring environment.

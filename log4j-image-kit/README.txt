Log4j Trivy demo / Windows PowerShell
 
[실행 전 필수 준비: trivy.exe를 이 폴더에 넣어주세요]
1. Windows용 Trivy를 공식 배포 페이지에서 다운로드하고 압축을 해제합니다.
   공식 배포 페이지: https://github.com/aquasecurity/trivy/releases/
   - 일반적인 64비트 Windows: trivy_<버전>_windows-64bit.zip
   - Windows on ARM 기기는 ARM64용이 제공되는지 확인하세요.
2. 압축을 푼 파일 중 trivy.exe를 이 README_windows.txt가 있는 폴더에 복사합니다.
   Dockerfile, prepare.ps1, verify.py와 같은 위치에 있어야 합니다.
   trivy.exe를 별도의 하위 폴더에 넣지 마세요.
3. 파일 탐색기에서 이 폴더를 열고 주소 표시줄에 powershell을 입력한 뒤 Enter를 누릅니다.
4. 열린 PowerShell에서 다음 명령으로 Trivy가 실행되는지 확인합니다.
   .\trivy.exe --version
   다운로드한 파일이 차단되어 실행되지 않으면 다음 명령으로 차단을 해제합니다.
   Unblock-File .\trivy.exe
   (SmartScreen 경고가 뜨면 "추가 정보" > "실행"을 선택하세요.)
5. 버전이 정상적으로 표시되면 아래 1번 단계부터 진행합니다.
   trivy.exe를 더블클릭하는 것이 아니라, 이 폴더에서 PowerShell 명령으로 실행하세요.
 
폴더 구성 예시:
log4j-image-kit
  README_windows.txt
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
Requirements: Docker Desktop (Linux containers, 실행 중이어야 함), Python 3, trivy.exe.
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
 
[Windows 관련 문제 해결]
- "이 시스템에서 스크립트를 실행할 수 없으므로..." 오류 : 1번 단계처럼
  -ExecutionPolicy Bypass 옵션으로 실행하세요. 조직 정책으로 막혀 있으면 정책을 따르세요.
- "trivy.exe : 용어가 cmdlet... 인식되지 않습니다" : PowerShell이 trivy.exe가 있는 폴더에서
  열렸는지 확인하고, 명령 앞에 .\ 를 붙였는지 확인하세요.
- "py : 용어가 ... 인식되지 않습니다" : Python 3를 설치할 때 "py launcher" 옵션이 포함되어야 합니다.
  python .\verify.py ... 로 대신 실행해 볼 수도 있습니다.
- "error during connect" 또는 Docker daemon 오류 : Docker Desktop을 실행하고
  완전히 시작될 때까지 기다린 뒤, Linux containers 모드인지 확인하세요.
 
Validation: Python syntax and synthetic JSON comparison tests checked. Docker build, Maven downloads, Windows PowerShell, and real Trivy scans were not executed by the authoring environment.



Log4j Trivy demo / macOS Terminal
 
[실행 전 필수 준비: trivy 실행 파일을 이 폴더에 넣어주세요]
1. macOS용 Trivy를 공식 배포 페이지에서 다운로드하고 압축을 해제합니다.
   공식 배포 페이지: https://github.com/aquasecurity/trivy/releases/
   - Apple Silicon(M1/M2/M3 등): trivy_<버전>_macOS-ARM64.tar.gz
   - Intel Mac: trivy_<버전>_macOS-64bit.tar.gz
   - 내 Mac이 어느 쪽인지 모르면 터미널에서 uname -m 을 실행하세요.
     arm64 이면 Apple Silicon, x86_64 이면 Intel입니다.
2. 압축을 푼 파일 중 trivy(확장자 없음)를 이 README.txt가 있는 폴더에 복사합니다.
   Dockerfile, prepare.sh, verify.py와 같은 위치에 있어야 합니다.
   trivy를 별도의 하위 폴더에 넣지 마세요.
3. 터미널에서 이 폴더로 이동합니다. 아래 중 편한 방법을 사용하세요.
   - Finder에서 이 폴더를 우클릭 > "폴더에 새로운 터미널" (서비스 메뉴에서 활성화 필요할 수 있음)
   - 터미널을 열고 cd 를 입력한 뒤 한 칸 띄우고 Finder의 폴더를 터미널 창으로 끌어다 놓고 Enter
4. 실행 권한을 부여하고, 다운로드 파일에 붙은 격리(quarantine) 속성을 제거합니다.
   chmod +x ./trivy ./prepare.sh
   xattr -d com.apple.quarantine ./trivy
   (격리 속성이 없다는 오류가 나오면 무시해도 됩니다.)
   "확인되지 않은 개발자" 경고로 실행이 막히면 시스템 설정 > 개인정보 보호 및 보안 에서
   "그래도 허용"을 선택한 뒤 다시 실행하세요.
5. 다음 명령으로 Trivy가 실행되는지 확인합니다.
   ./trivy --version
6. 버전이 정상적으로 표시되면 아래 1번 단계부터 진행합니다.
   trivy를 Finder에서 더블클릭하는 것이 아니라, 이 폴더에서 터미널 명령으로 실행하세요.
 
폴더 구성 예시:
log4j-image-kit
  README.txt
  Dockerfile
  prepare.sh
  verify.py
  trivy        <- 직접 다운로드한 실행 파일을 여기에 넣기
  scan.py      <- HTML 보고서 생성 시 필요
 
This kit builds two package-detection images, not a running Java web application.
Final images use FROM scratch and contain only log4j-core JAR files.
There are no OS packages, Java runtime, exposed ports, or exploit payloads.
The Maven build stage is not part of the final images.
Vulnerable: Log4j 2.14.1; comparison patched: 2.24.3.
Patched refers to CVE-2021-44228 and is not a guarantee against all present/future CVEs.
Requirements: Docker Desktop for Mac (Linux containers, 실행 중이어야 함), Python 3, trivy.
Place trivy and the previously supplied scan.py beside these files.
 
1. Build and save (containers are NOT started):
bash ./prepare.sh
(chmod +x ./prepare.sh 를 실행했다면 ./prepare.sh 로도 실행할 수 있습니다.)
Permission denied 오류가 나면 위처럼 bash ./prepare.sh 로 실행하거나 chmod +x 를 적용하세요.
Follow organizational policy if script execution is restricted.
 
2. Inspect and save complete package lists for validation:
./trivy image --input ./images/vulnerable.tar --scanners vuln --list-all-pkgs --format json --output vulnerable.json
Check that "echo $?" prints 0 before proceeding.
./trivy image --input ./images/patched.tar --scanners vuln --list-all-pkgs --format json --output patched.json
Check that "echo $?" prints 0 before proceeding.
python3 ./verify.py ./vulnerable.json ./patched.json
DEMO READY requires: log4j-core detected in both reports, target CVE present only in vulnerable, Critical present only in vulnerable.
Do not confuse absent findings with successfully identifying the package.
 
3. Generate the previously supplied HTML report / policy decision:
python3 ./scan.py --input ./images/vulnerable.tar
python3 ./scan.py --input ./images/patched.tar
scan.py was supplied earlier; it is not included here.
scan.py 안에서 trivy.exe 를 호출하도록 작성되어 있다면 macOS에서는 ./trivy (또는 trivy) 를
호출하도록 수정되었는지 확인하세요. 경로 구분자(\)도 / 로 맞아야 합니다.
 
If patched still has Critical, inspect the actual finding and select a compatible fixed release, then rebuild and re-export. Never edit findings to force PASS.
If Trivy cannot identify the JAR, inspect its log and Java DB downloads.
Missing OS metadata is expected for a scratch image; verify the Java package analysis separately.
These are static package-scan specimens. They do not demonstrate an exploitable running service or actual Azure deployment blocking.
 
[macOS 관련 문제 해결]
- "zsh: permission denied: ./trivy" : chmod +x ./trivy 를 실행하세요.
- "cannot be opened because the developer cannot be verified" : 4번 단계의 xattr 명령 또는 시스템 설정의 "그래도 허용"을 사용하세요.
- "bad interpreter" 또는 "^M" 오류 (Windows에서 만든 스크립트의 줄바꿈 문제):
  sed -i '' 's/\r$//' prepare.sh verify.py
- "Cannot connect to the Docker daemon" : Docker Desktop을 실행하고 완전히 시작될 때까지 기다린 뒤 다시 시도하세요.
- python3 실행 시 개발자 도구 설치 창이 뜨면 설치를 진행하거나 python.org에서 Python 3를 설치하세요.
 
Validation: This README is a conversion of the Windows PowerShell version for macOS. The macOS commands were not executed by the authoring environment. Docker build, Maven downloads, and real Trivy scans were not run.

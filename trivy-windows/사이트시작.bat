@echo off
chcp 65001 >nul
cd /d "%~dp0"
where docker >nul 2>&1
if errorlevel 1 (
 echo Docker Desktop을 설치한 뒤 이 파일을 다시 실행해주세요.
 echo https://www.docker.com/products/docker-desktop/
 pause
 exit /b 1
)
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
echo Docker 준비를 기다립니다. 초기 설정 창이 나타나면 완료해주세요.
set /a attempts=0
:waitdocker
docker info >nul 2>&1
if not errorlevel 1 goto prepare
set /a attempts+=1
if %attempts% GEQ 90 (
 echo Docker가 준비되지 않았습니다. Docker Desktop 상태를 확인해주세요.
 pause
 exit /b 1
)
timeout /t 2 /nobreak >nul
goto waitdocker
:prepare
echo 사이트를 준비합니다. 처음에는 다운로드 시간이 필요합니다.
docker compose build
if errorlevel 1 goto failed
echo 취약점 DB를 다운로드하거나 갱신합니다.
docker compose run --rm --no-deps web trivy image --download-db-only
if errorlevel 1 goto failed
echo Java 분석용 DB를 준비합니다.
docker compose run --rm --no-deps web trivy image --download-java-db-only
if errorlevel 1 goto failed
docker compose up -d
if errorlevel 1 goto failed
set /a attempts=0
:waitweb
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8080/' -TimeoutSec 3; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto ready
set /a attempts+=1
if %attempts% GEQ 30 goto webfailed
timeout /t 2 /nobreak >nul
goto waitweb
:ready
echo 준비 완료!
echo Enter를 누르면 사이트를 열고 이 창을 닫습니다.
set /p "answer="
start "" "http://localhost:8080"
exit /b 0
:webfailed
echo 사이트 응답을 확인하지 못했습니다.
docker compose logs --tail 40
:failed
echo 준비 또는 실행에 실패했습니다. 위 오류를 캡처해서 보내주세요.
pause
exit /b 1

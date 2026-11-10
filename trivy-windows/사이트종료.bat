@echo off
chcp 65001 >nul
cd /d "%~dp0"
docker compose down
if errorlevel 1 (
 echo 종료에 실패했습니다. Docker Desktop 실행 상태를 확인해주세요.
 pause
 exit /b 1
)
echo 사이트를 종료했습니다. DB는 다음 실행을 위해 유지합니다.
echo Enter를 누르면 이 창을 닫습니다.
set /p "answer="
exit /b 0
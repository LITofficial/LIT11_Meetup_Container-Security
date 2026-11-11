#!/bin/bash
cd "$(dirname "$0")"
if ! command -v docker >/dev/null 2>&1; then
 echo "Docker Desktop을 먼저 설치하고 실행해주세요."
 echo "https://www.docker.com/products/docker-desktop/"
 read -p "Enter를 누르면 종료합니다. "
 exit 1
fi
open -a Docker
printf "Docker 준비를 기다립니다"
ready=0
for i in {1..90}; do
 if docker info >/dev/null 2>&1; then ready=1; break; fi
 printf "."; sleep 2
done
echo
if [ "$ready" != 1 ]; then
 echo "Docker Desktop 초기 설정을 완료한 뒤 다시 실행해주세요."
 read -p "Enter를 누르면 종료합니다. "; exit 1
fi
echo "사이트를 준비합니다. 처음 한 번은 인터넷 연결과 다운로드 시간이 필요합니다."
if ! docker compose build; then
 echo "사이트 준비 실패. 위 오류를 캡처해서 보내주세요."
 read -p "Enter를 누르면 종료합니다. "; exit 1
fi
echo "취약점 데이터베이스를 미리 다운로드/갱신합니다."
if ! docker compose run --rm --no-deps web trivy image --download-db-only; then
 echo "DB 다운로드 실패. 인터넷 연결을 확인해주세요."
 read -p "Enter를 누르면 종료합니다. "; exit 1
fi
if ! docker compose run --rm --no-deps web trivy image --download-java-db-only; then
 echo "Java DB 다운로드 실패. 인터넷 연결을 확인해주세요."
 read -p "Enter를 누르면 종료합니다. "; exit 1
fi
if ! docker compose up -d; then
 echo "사이트 실행 실패. 위 오류를 확인해주세요."
 read -p "Enter를 누르면 종료합니다. "; exit 1
fi
for i in {1..30}; do
 if curl -fsS http://localhost:8080/ >/dev/null; then
  echo "준비 완료!"
  read -r -p "Enter를 누르면 사이트를 열고 이 창을 닫습니다. "
  open "http://localhost:8080"
  exit 0
 fi
 sleep 2
done
echo "사이트 응답을 확인하지 못했습니다. 아래 오류를 확인해주세요."
docker compose logs --tail 40
read -p "Enter를 누르면 종료합니다. "

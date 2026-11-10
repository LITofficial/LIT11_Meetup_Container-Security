#!/bin/bash
cd "$(dirname "$0")"
docker compose down
if ! docker compose down; then
  echo "사이트 종료에 실패했습니다. 위 오류를 확인해주세요."
  read -r -p "Enter를 누르면 종료합니다. "
  exit 1
fi
  echo "사이트를 종료했습니다. DB는 다음 실행을 위해 유지합니다."
  read -r -p "Enter를 누르면 이 창을 닫습니다. "
  exit 0
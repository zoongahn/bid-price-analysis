#!/bin/bash

# 모든 screen 세션 리스트 가져와서 종료
for session in $(screen -ls | grep -o '[0-9]\{1,\}\.\w*'); do
  echo "Killing session: $session"
  screen -S "$session" -X quit
done
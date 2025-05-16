#!/bin/bash

for year in {2000..2009}
do
  screen -dmS "year_$year" bash -c "cd /data/dev/bid-price-analysis/api-fetcher && source ./.venv/bin/activate && python fetch-data/main.py --service 사용자정보서비스 --oper 2 --year $year; exec bash"
done

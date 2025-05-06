#!/bin/bash

for year in {2010..2024}
do
  screen -dmS "year_$year" bash -c "cd /data/dev/bid-price-analysis/api-fetcher && source ./.venv/bin/activate && python fetch-data/collect_bid.py --service 낙찰정보서비스 --oper 10 --year $year; exec bash"
done

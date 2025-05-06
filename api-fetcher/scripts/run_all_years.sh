#!/bin/bash

for year in {2012..2024}
do
  screen -dmS "year_$year" bash -c "cd /data/dev/bid-price-analysis/api-fetcher && source ./.venv/bin/activate && python src/main.py --year $year; exec bash"
done

#!/bin/bash

for year in {2010..2024}
do
<<<<<<< HEAD
  screen -dmS "year_$year" bash -c "cd /data/dev/bid-price-analysis/api-fetcher && source ./.venv/bin/activate && python src/main.py --year $year; exec bash"
=======
  screen -dmS "year_$year" bash -c "python3 collect_bid.py --service 낙찰정보서비스 --oper 10 --year $year; exec bash"
>>>>>>> 42cae2062f14d779b33158f41e5652c75257dcc1
done

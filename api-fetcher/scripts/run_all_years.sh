#!/bin/bash

for year in {2010..2024}
do
  screen -dmS "year_$year" bash -c "python3 collect_bid.py --service 낙찰정보서비스 --oper 10 --year $year; exec bash"
done

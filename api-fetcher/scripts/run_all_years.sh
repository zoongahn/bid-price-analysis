#!/bin/bash

for year in {2012..2024}
do
  screen -dmS "year_$year" bash -c "python3 main.py --year $year; exec bash"
done

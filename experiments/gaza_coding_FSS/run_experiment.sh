#!/bin/bash

# get location of this script
EXPERIMENT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# TODO: First download csv files from Google Spreadsheet 
# and save them in `ratings_GSpreadsheet_csv` folder

# --------------- Converting ratings from Google Spreadsheet to CSV ratings  -----------
RATINGS=$EXPERIMENT_DIR/ratings
python GSpreadsheet_to_ratings.py \
    $EXPERIMENT_DIR/ratings_GSpreadsheet_csv/ \
    $RATINGS

# --------------- Calculating Inter-rater reliability  -----------

python calculate_IRR.py \
    --ratings-dir $RATINGS \
    --output-dir $EXPERIMENT_DIR/output_IRR/ \
    --prompt-definitions $EXPERIMENT_DIR/prompt_definitions.json



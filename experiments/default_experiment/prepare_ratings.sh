#!/bin/bash

# get location of this script
EXPERIMENT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# if $DISCOURSEER variable is not set, default to current directory
if [ -z $DISCOURSEER ]; then
    DISCOURSEER="./"
fi


# TODO: First download csv files from Google Spreadsheet
# and save them in `ratings_GSpreadsheet_csv` folder

# --------------- Converting ratings from Google Spreadsheet to CSV ratings  -----------
RATINGS=$EXPERIMENT_DIR/ratings
# python $DISCOURSEER/GSpreadsheet_to_ratings.py \
#     $EXPERIMENT_DIR/ratings_GSpreadsheet_csv/ \
#     $RATINGS

# --------------- Calculating Inter-rater reliability  -----------

python $DISCOURSEER/calc_irr_for_raters.py \
    --ratings-dir $RATINGS \
    --output-dir $EXPERIMENT_DIR/output_IRR/ \
    --prompt-definitions $EXPERIMENT_DIR/prompt_definitions.json



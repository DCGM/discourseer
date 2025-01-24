#!/bin/bash

# get location of this script
EXPERIMENT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
discourseer=../../

# --------------- Converting ratings from Google Spreadsheet to CSV ratings  -----------
RATINGS=$EXPERIMENT_DIR/ratings
python $discourseer/calc_irr_for_raters.py \
    --ratings-dir $RATINGS \
    --output-dir $EXPERIMENT_DIR/output_IRR/ \
    --codebook $EXPERIMENT_DIR/codebook.json


exit $?  # exit with the exit code of the last command

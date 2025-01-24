#!/bin/bash

# get location of this script
EXPERIMENT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# if $DISCOURSEER variable is not set, raise an error
if [ -z $DISCOURSEER ]; then
    echo "DISCOURSEER variable is not set. Please set DISCOURSEER variable to the location of the discourseer repository."
    exit 1
fi


# --------------- Converting ratings from Google Spreadsheet to CSV ratings  -----------
RATINGS=$EXPERIMENT_DIR/ratings
python $DISCOURSEER/GSpreadsheet_to_ratings.py \
    $EXPERIMENT_DIR/ratings_GSpreadsheet_csv/ \
    $RATINGS && \
python $DISCOURSEER/calc_irr_for_raters.py \
    --ratings-dir $RATINGS \
    --output-dir $EXPERIMENT_DIR/output_IRR/ \
    --prompt-definitions $EXPERIMENT_DIR/prompt_definitions.json

exit $?  # exit with the exit code of the last command

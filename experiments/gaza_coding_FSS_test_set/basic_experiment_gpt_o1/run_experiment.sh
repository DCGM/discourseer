#!/bin/bash

# get location of this script
EXPERIMENT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# if $DISCOURSEER variable is not set, default to current directory
if [ -z $DISCOURSEER ]; then
    DISCOURSEER="./"
fi

# ---------------------------  PARSING ARGUMENT  ---------------------------
# first arg: 'mini' (store true) or nothing (store false)
TEXT_COUNT=''
OUTPUT_DIR='output'
# check if the first argument is 'mini' or nothing
if [ "$1" = "mini" ]; then
    TEXT_COUNT='--text-count 3'
    OUTPUT_DIR="$EXPERIMENT_DIR/output_mini/"
fi
OUTPUT="--output-dir $OUTPUT_DIR"


# ---------------------------  RUNNING EXPERIMENT  ---------------------------
if [ "$1" = "recalc" ]; then
    # Check for exactly one codebook in the experiment directory
    codebook_count=$(ls $EXPERIMENT_DIR/codebook* | wc -l)
    if [ $codebook_count -eq 0 ]; then
        echo "No codebooks found in $EXPERIMENT_DIR"
        exit 1
    elif [ $codebook_count -gt 1 ]; then
        echo "More than one codebook found in $EXPERIMENT_DIR"
        ls $EXPERIMENT_DIR/codebook*
        exit 1
    elif [ $codebook_count -eq 1 ]; then
        codebook_name=$(ls $EXPERIMENT_DIR/codebook*)
    fi

    # recalculate IRR for dataframe using calc_irr_for_dataframe.py
    echo "Recalculating IRR for dataframe using calc_irr_for_dataframe.py"
    python $DISCOURSEER/calc_irr_for_dataframe.py \
        --input-dir $OUTPUT_DIR \
        --output-dir $OUTPUT_DIR \
        --codebook $codebook_name
else
    # run discourseer normaly
    python $DISCOURSEER/run_discourseer.py \
        --experiment-dir $EXPERIMENT_DIR \
        --ratings-dir $EXPERIMENT_DIR/../inputs/ratings/ \
        --texts-dir $EXPERIMENT_DIR/../inputs/texts/ \
        $TEXT_COUNT \
        $OUTPUT
    # --log DEBUG
fi

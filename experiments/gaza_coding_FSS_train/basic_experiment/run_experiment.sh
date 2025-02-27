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
OUTPUT_DIR=''
# check if the first argument is 'mini' or nothing
if [ "$1" = "mini" ]; then
    TEXT_COUNT='--text-count 3'
    OUTPUT="--output-dir $EXPERIMENT_DIR/output_mini/"
fi


# ---------------------------  RUNNING EXPERIMENT  ---------------------------
python $DISCOURSEER/run_discourseer.py \
    --experiment-dir $EXPERIMENT_DIR \
    --ratings-dir $EXPERIMENT_DIR/../inputs/ratings/ \
    --texts-dir $EXPERIMENT_DIR/../inputs/texts/ \
    --log DEBUG \
    $TEXT_COUNT \
    $OUTPUT

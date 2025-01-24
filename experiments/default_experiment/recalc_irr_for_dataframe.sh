#!/bin/bash
# Description: Recalc IRR for dataframe in output folder of `run_experiment.sh` script.
# Usage: ./recalc_irr_for_dataframe.sh [input_folder default: latest output folder] [output_folder default: output]

# get location of this script
EXPERIMENT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# if $DISCOURSEER variable is not set, default to current directory
if [ -z $DISCOURSEER ]; then
    DISCOURSEER="./"
fi

# --------------- Parsing arguments  -----------
if [ -z $1 ]; then
    # if 'output' exists, use it, otherwise use latest output folder
    if [ -d $EXPERIMENT_DIR/output ]; then
        INPUT_FOLDER=$EXPERIMENT_DIR/output
    else
        INPUT_FOLDER=$(ls -d $EXPERIMENT_DIR/output* | grep -v "output_IRR" | tail -1)  # default to latest output folder
    fi
else
    INPUT_FOLDER=$1
fi

if [ -z $2 ]; then
    OUTPUT_FOLDER="output"  # default to output folder
else
    OUTPUT_FOLDER=$2
fi

echo "Input folder: $INPUT_FOLDER"
echo "Output folder: $OUTPUT_FOLDER"

# --------------- Realculating Inter-rater reliability for dataframe  -----------

python $DISCOURSEER/calc_irr_for_dataframe.py \
    --input-dir $INPUT_FOLDER \
    --output-dir $EXPERIMENT_DIR/$OUTPUT_FOLDER \
    --codebook $EXPERIMENT_DIR/codebook.json

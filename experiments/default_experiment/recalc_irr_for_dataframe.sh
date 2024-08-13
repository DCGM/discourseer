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
    INPUT_FOLDER=$(ls -d $EXPERIMENT_DIR/output* | grep -v "output_IRR" | tail -1)  # default to latest output folder
else
    INPUT_FOLDER=$1
fi

if [ -z $2 ]; then
    OUTPUT_FOLDER="output"  # default to output folder
else
    OUTPUT_FOLDER=$2
fi

# --------------- Realculating Inter-rater reliability for dataframe  -----------

python $DISCOURSEER/calc_irr_for_dataframe.py \
    --input-dir $INPUT_FOLDER \
    --output-dir $EXPERIMENT_DIR/$OUTPUT_FOLDER \
    --prompt-definitions $EXPERIMENT_DIR/prompt_definitions.json
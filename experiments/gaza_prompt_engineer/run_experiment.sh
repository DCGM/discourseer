#!/bin/bash

# get location of this script
EXPERIMENT_DIR_BASE=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
rm -f $EXPERIMENT_DIR_BASE/out.csv

# if $DISCOURSEER variable is not set, default to current directory
if [ -z $DISCOURSEER ]; then
    DISCOURSEER="./"
fi

# DIRS=`ls -d $EXPERIMENT_DIR/*/`
for EXPERIMENT_DIR in `ls -d $EXPERIMENT_DIR_BASE/experiments/*/`; do  # 001/  002_delete_JSON_answer_template/  003_whole_prompt_info/  004_parenthesis_instead_of_columns/  005/ ; do
    echo ""
    echo "Running experiment in $EXPERIMENT_DIR"

    # ---------------------------  PARSING ARGUMENT  ---------------------------
    # first arg: 'mini' (store true) or nothing (store false)
    TEXT_COUNT=''
    OUTPUT_DIR=$EXPERIMENT_DIR"/output"
    OUT_CSV=$EXPERIMENT_DIR_BASE/out.csv
    # check if the first argument is 'mini' or nothin
    if [ "$1" = "mini" ]; then
        TEXT_COUNT='--text-count 3'
        OUTPUT_DIR=$OUTPUT_DIR"_mini"
        OUTPUT="--output-dir $OUTPUT_DIR"
        OUT_CSV=$EXPERIMENT_DIR_BASE/out_mini.csv
    fi
    rm -rf $OUTPUT_DIR

    # ---------------------------  RUNNING EXPERIMENT  ---------------------------
    python $DISCOURSEER/run_discourseer.py \
        --experiment-dir $EXPERIMENT_DIR \
        --prompt-schema-definition $EXPERIMENT_DIR/prompt_schema_definition.json \
        --prompt-definitions $EXPERIMENT_DIR/prompt_definitions.json \
        --ratings-dir $EXPERIMENT_DIR_BASE/ratings/ \
        --texts-dir $EXPERIMENT_DIR_BASE/texts/ \
        $TEXT_COUNT \
        $OUTPUT

    # # ---------------------------  COLLECTING RESULTS  ---------------------------
    echo -n "$EXPERIMENT_DIR;" >> $OUT_CSV
    echo `jq '.overall.gwet_ac1.with_model' $OUTPUT_DIR/irr_results.json` >> $OUT_CSV
    tail -n 1 $OUT_CSV

done

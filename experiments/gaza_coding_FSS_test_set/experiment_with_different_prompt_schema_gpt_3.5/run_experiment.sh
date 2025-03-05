#!/bin/bash

# get location of this script
EXPERIMENT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# if $DISCOURSEER variable is not set, default to current directory
if [ -z $DISCOURSEER ]; then
    DISCOURSEER="./"
fi

# ---------------------------  PARSING ARGUMENT  ---------------------------
# first arg: 'mini' (store true) or nothing (store false)
# TEXT_COUNT=''
# OUTPUT=''
# check if the first argument is 'mini' or nothing
if [ "$1" = "mini" ]; then
    TEXT_COUNT='--text-count 3'
    # OUTPUT="--output-dir $EXPERIMENT_DIR/output_mini"
fi


# ---------------------------  RUNNING EXPERIMENTS  ---------------------------

for prompt_schema in `ls $DISCOURSEER/prompt_schemas/prompt_schema_definition*`; do
    # echo "codebook: $codebook"
    # codebook_name=$(basename $codebook | sed 's/.json//')
    prompt_schema_name=$(basename $prompt_schema | sed 's/.json//')

    echo -e "\n\n=============================================================="
    echo -e "\tprompt_schema: $prompt_schema"
    echo -e "==============================================================\n\n"

    if [ "$1" = "mini" ]; then
        OUTPUT="--output-dir $EXPERIMENT_DIR/output_mini_$prompt_schema_name"
    else
        OUTPUT="--output-dir $EXPERIMENT_DIR/output_$prompt_schema_name"
    fi

    python $DISCOURSEER/run_discourseer.py \
        --experiment-dir $EXPERIMENT_DIR \
        --ratings-dir $EXPERIMENT_DIR/../inputs/ratings/ \
        --texts-dir $EXPERIMENT_DIR/../inputs/texts/ \
        --prompt-schema-definition $prompt_schema \
        --log DEBUG \
        $TEXT_COUNT \
        $OUTPUT
done


# ---------------------------  PRINTING RESULTS  ---------------------------

for prompt_schema in `ls $DISCOURSEER/prompt_schemas/prompt_schema_definition*`; do
    prompt_schema_name=$(basename $prompt_schema | sed 's/.json//')

    if [ "$1" = "mini" ]; then
        OUTPUT_DIR="$EXPERIMENT_DIR/output_mini_$prompt_schema_name"
    else
        OUTPUT_DIR="$EXPERIMENT_DIR/output_$prompt_schema_name"
    fi

    # cat $OUTPUT_DIR/irr_results.json
    echo -ne "$prompt_schema_name:\t"  | tee -a $EXPERIMENT_DIR/irr_results.txt
    cat $OUTPUT_DIR/irr_results.json | jq '.["mean_through_questions"]["krippendorff_alpha"]["with_model"]' |  tee -a $EXPERIMENT_DIR/irr_results.txt

done



# for dir in `ls -d $EXPERIMENT_DIR/output*`; do
#     dir=$(basename $dir)
#     cat $dir/irr_results.json | jq '.["mean_through_questions"]["krippendorff_alpha"]["with_model"]'
#     # echo -e "\n\n=============================================================="
#     # echo -e "\tdir: $dir"
#     # echo -e "==============================================================\n\n"
# done
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

RESULT_FILE_KRIP=$EXPERIMENT_DIR/krippendorff_alpha_means_through_questions.txt
RESULT_FILE_MAJ=$EXPERIMENT_DIR/majority_agreement_overall.txt
echo -n "" > $RESULT_FILE_KRIP
echo -n "" > $RESULT_FILE_MAJ

for prompt_schema in `ls $EXPERIMENT_DIR/prompt_schema_*`; do
    # echo "codebook: $codebook"
    # codebook_name=$(basename $codebook | sed 's/.json//')
    prompt_schema_name=$(basename $prompt_schema | sed 's/.json//')

    echo -e "\n\n=============================================================="
    echo -e "\tprompt_schema: $prompt_schema"
    echo -e "==============================================================\n\n"

    if [ "$1" = "mini" ]; then
        OUTPUT_DIR="$EXPERIMENT_DIR/output_mini_$prompt_schema_name"
    else
        OUTPUT_DIR="$EXPERIMENT_DIR/output_$prompt_schema_name"
    fi
    OUTPUT="--output-dir $OUTPUT_DIR"

    if [ "$1" = "recalc" ]; then
        # Check for exactly one codebook in the experiment directory
        codebook_count=$(ls $EXPERIMENT_DIR/codebook* | wc -l)
        if [ $codebook_count -eq 0 ]; then
            echo "No codebooks found in $EXPERIMENT_DIR"
            continue
        elif [ $codebook_count -gt 1 ]; then
            echo "More than one codebook found in $EXPERIMENT_DIR"
            ls $EXPERIMENT_DIR/codebook*
            continue
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
            --prompt-schema-definition $prompt_schema \
            $TEXT_COUNT \
            $OUTPUT
    fi

    cat $OUTPUT_DIR/irr_results.json | jq '.["irr_result"]["krippendorff_alpha"]["with_model"]' | tr -d '\n' >> $RESULT_FILE_KRIP
    echo -e "\t$prompt_schema_name" >> $RESULT_FILE_KRIP
    cat $OUTPUT_DIR/irr_results.json | jq '.["majority_agreement"]' | tr -d '\n' >> $RESULT_FILE_MAJ
    echo -e "\t$prompt_schema_name" >> $RESULT_FILE_MAJ

    echo -e "\nKrippendorf results so far:"
    cat $RESULT_FILE_KRIP

    echo -e "\nMajority agreement results so far:"
    cat $RESULT_FILE_MAJ
    echo "(last codebook: $codebook_name)"
done


# ---------------------------  PRINTING RESULTS  ---------------------------
echo "--------------------------------------------------------------"

echo -e "\nKrippendorf sorted results:"
cat $RESULT_FILE_KRIP | sort -n

echo -e "\nMajority agreement sorted results:"
cat $RESULT_FILE_MAJ | sort -n

#!/bin/bash

# if $DISCOURSEER variable is not set, default to current directory
if [ -z $DISCOURSEER ]; then
    DISCOURSEER="./"
fi

python $DISCOURSEER/run_discourseer.py \
	--experiment-dir $DISCOURSEER/experiments/gaza_run_1/ \
	--prompt-schema-definition $DISCOURSEER/experiments/default_experiment/prompt_schema_definition.json \
	--log DEBUG

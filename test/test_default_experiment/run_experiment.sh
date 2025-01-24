#!/bin/bash

# get location of this script
EXPERIMENT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# if $DISCOURSEER variable is not set, raise an error
if [ -z $DISCOURSEER ]; then
    echo "DISCOURSEER variable is not set. Please set DISCOURSEER variable to the location of the discourseer repository."
    exit 1
fi


# ---------------------------  RUNNING EXPERIMENT  ---------------------------
python $DISCOURSEER/run_discourseer.py \
    --experiment-dir $EXPERIMENT_DIR \
    --log DEBUG \
    $TEXT_COUNT \
    $OUTPUT

exit $?  # exit with the exit code of the last command
#!/bin/bash
set -e

while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

if [[ -z "$MODEL" ]]; then
    echo "--model is required"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_discourseer.sh"

echo "Running model: $MODEL"
echo $REPO_ROOT
echo "Running script: $RUN_SCRIPT"

source $REPO_ROOT/../venv/bin/activate

CODEBOOK=$REPO_ROOT/codebooks/codebook_gaza_v2_srpen.json
source "$RUN_SCRIPT" \
    --root-dir "$REPO_ROOT" \
    --model "$MODEL" \
    --codebook "$CODEBOOK" \
    --individual-questions "true" \

source "$RUN_SCRIPT" \
    --root-dir "$REPO_ROOT" \
    --model "$MODEL" \
    --codebook "$CODEBOOK" \
    --individual-questions "false"

CODEBOOK=$REPO_ROOT/codebooks/codebook_gaza_v0_kveten.json
source "$RUN_SCRIPT" \
    --root-dir "$REPO_ROOT" \
    --model "$MODEL" \
    --codebook "$CODEBOOK" \
    --individual-questions "true"

source "$RUN_SCRIPT" \
    --root-dir "$REPO_ROOT" \
    --model "$MODEL" \
    --codebook "$CODEBOOK" \
    --individual-questions "false"

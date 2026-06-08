#!/bin/bash
set -e

BASE_URL="http://localhost:11434/v1"
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --base-url)
            BASE_URL="$2"
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

source $REPO_ROOT/../venv/bin/activate

# Replace / in model name with - for output directory naming
MODEL_DIR_NAME=$(echo "$MODEL" | tr '/' '-')

CODEBOOK=$REPO_ROOT/codebooks/codebook_gaza_v2_srpen.json
source "$RUN_SCRIPT" \
    --root-dir "$REPO_ROOT" \
    --model "$MODEL" \
    --codebook "$CODEBOOK" \
    --individual-questions "true" \
    --output-dir $REPO_ROOT/$MODEL_DIR_NAME-srpen-indi

source "$RUN_SCRIPT" \
    --root-dir "$REPO_ROOT" \
    --model "$MODEL" \
    --codebook "$CODEBOOK" \
    --individual-questions "false" \
    --output-dir $REPO_ROOT/$MODEL_DIR_NAME-srpen

CODEBOOK=$REPO_ROOT/codebooks/codebook_gaza_v0_kveten.json
source "$RUN_SCRIPT" \
    --root-dir "$REPO_ROOT" \
    --model "$MODEL" \
    --codebook "$CODEBOOK" \
    --individual-questions "true" \
    --output-dir $REPO_ROOT/$MODEL_DIR_NAME-kveten-indi

source "$RUN_SCRIPT" \
    --root-dir "$REPO_ROOT" \
    --model "$MODEL" \
    --codebook "$CODEBOOK" \
    --individual-questions "false" \
    --output-dir $REPO_ROOT/$MODEL_DIR_NAME-kveten

#!/bin/bash
set -e

MODEL="llama3.1:8b"
TEMPERATURE=0.0
TOP_P=0.0
MAX_TOKENS=1024
MAX_RETRIES=4
LOG="INFO"
BASE_URL="http://localhost:11434/v1"

while [[ $# -gt 0 ]]; do
    case $1 in
        --root-dir)
            ROOT_DIR="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --codebook)
            CODEBOOK="$2"
            shift 2
            ;;
        --individual-questions)
            INDIVIDUAL_QUESTIONS="$2"
            shift 2
            ;;
        --temperature)
            TEMPERATURE="$2"
            shift 2
            ;;
        --top-p)
            TOP_P="$2"
            shift 2
            ;;
        --max-tokens)
            MAX_TOKENS="$2"
            shift 2
            ;;
        --max-retries)
            MAX_RETRIES="$2"
            shift 2
            ;;
        --log)
            LOG="$2"
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

if [[ -z "$ROOT_DIR" ]]; then
    echo "--root-dir is required"
    exit 1
fi
if [[ -z "$CODEBOOK" ]]; then
    echo "--codebook is required"
    exit 1
fi


TEXTS_DIR=$ROOT_DIR/experiments/gaza_coding_FSS_test_set/inputs/texts
RATINGS_DIR=$ROOT_DIR/experiments/gaza_coding_FSS_test_set/inputs/ratings

PROMPT_SCHEMA_DEFINITION=$ROOT_DIR/prompt_schema_definition_tmp.json

cat > $PROMPT_SCHEMA_DEFINITION <<EOF
{
  "model": "$MODEL",
  "max_tokens": $MAX_TOKENS,
  "temperature": $TEMPERATURE,
  "top_p": $TOP_P,
  "response_format": "json",
  "prompt_individual_questions": ${INDIVIDUAL_QUESTIONS:-false},
  "messages": [
    {
      "role": "system",
      "content": "You are a media content analyst. You are analyzing the following text to extract {question_names}. {question_names_and_descriptions_colon}. For every question pick only options from these lists.\n{question_options}\n\nYou will pick one option for these questions: {single_choice_questions}. You will pick one or more options for these questions: {multiple_choice_questions}.\nText will be in Czech language. JSON answers will be in same language as the options are. You must give answer in valid JSON format. Do not output any other text except the JSON. You will give answer in JSON format according to this schema:"
    },
    {
      "role": "system",
      "content": "{response_json_schema_with_options}"
    },
    {
      "role": "user",
      "content": "The text to analyze is: {text}"
    }
  ]
}
EOF

python $ROOT_DIR/run_discourseer.py \
    --log $LOG \
    --texts-dir $TEXTS_DIR \
    --ratings-dir $RATINGS_DIR \
    --output-dir $OUTPUT_DIR \
    --prompt-schema-definition $PROMPT_SCHEMA_DEFINITION \
    --codebook $CODEBOOK \
    --openrouter \
    --max-retries $MAX_RETRIES \
    --reasoning-effort "high"

cp $PROMPT_SCHEMA_DEFINITION $OUTPUT_DIR/prompt_schema_definition.json
rm $PROMPT_SCHEMA_DEFINITION

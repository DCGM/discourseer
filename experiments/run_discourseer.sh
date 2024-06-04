
DICSOURSEER_HOME="/home/xvlach22/skola/10-sem-23-24-letni/PP1/discourseer/"  # Add your path to Discourseer here
SCRIPT=$DICSOURSEER_HOME/discourseer.py


python $SCRIPT\
    --texts-dir $DICSOURSEER_HOME/data/texts-vlach \
    --ratings-dir $DICSOURSEER_HOME/data/texts-vlach-ratings/ \
    --output-dir $DICSOURSEER_HOME/data/output/ \
    --prompt-definitions $DICSOURSEER_HOME/data/default/prompt_definitions.json \
    --prompt-schema-definition $DICSOURSEER_HOME/data/default/prompt_schema_definition.json \
    --copy-input-ratings none \
    --log INFO


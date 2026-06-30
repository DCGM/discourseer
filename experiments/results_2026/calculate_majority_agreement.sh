ROOT_DIR=$1

source $ROOT_DIR/venv/bin/activate

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

N_BOOT=5000

python $DIR/calculate_metric.py \
    $DIR/ratings.csv \
    $DIR/majorities.csv \
    --metrics majority \
    --n-boot $N_BOOT 

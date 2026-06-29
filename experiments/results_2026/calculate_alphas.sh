ROOT_DIR=$1

source $ROOT_DIR/venv/bin/activate

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

N_BOOT=5000

python $DIR/calculate_metric.py \
    $DIR/ratings.csv \
    $DIR/alphas.csv \
    --metrics krippendorff \
    --n-boot $N_BOOT 

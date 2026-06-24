#!/bin/bash
set -euo pipefail

PACKAGE=localiza_o_robotica
PACKAGE_DIR=$(rospack find "$PACKAGE")
BAG="${1:-$PACKAGE_DIR/bags/husky_trajectory.bag}"
RESULTS_DIR="${2:-$PACKAGE_DIR/results}"
MODES=(odom odom_imu odom_imu_gps)

if [ ! -f "$BAG" ]; then
    echo "Bag nao encontrada: $BAG" >&2
    exit 1
fi

mkdir -p "$RESULTS_DIR"

for MODE in "${MODES[@]}"; do
    rm -f \
        "$RESULTS_DIR/${MODE}_metrics.csv" \
        "$RESULTS_DIR/${MODE}_summary.txt" \
        "$RESULTS_DIR/${MODE}_plot.png"
done

for MODE in "${MODES[@]}"; do
    echo ""
    echo "=== Rodando modo: $MODE ==="

    roslaunch "$PACKAGE" replay_bag.launch \
        mode:="$MODE" \
        bag:="$BAG" \
        output_dir:="$RESULTS_DIR"

    SUMMARY="$RESULTS_DIR/${MODE}_summary.txt"
    if [ ! -s "$SUMMARY" ]; then
        echo "Resumo nao foi gerado para o modo $MODE: $SUMMARY" >&2
        exit 1
    fi
done

echo ""
echo "=== Gerando comparacao ==="
rosrun "$PACKAGE" compare_results.py --results-dir "$RESULTS_DIR"

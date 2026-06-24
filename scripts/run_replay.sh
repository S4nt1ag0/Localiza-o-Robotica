#!/bin/bash
set -e
BAG=/home/ros/catkin_ws/src/Localiza-o-Robotica/bags/husky_trajectory.bag

for MODE in odom odom_imu odom_imu_gps; do
    echo ""
    echo "=== Rodando modo: $MODE ==="

    roscore &
    ROSCORE_PID=$!
    sleep 3

    # Sobe a bag em background
    rosbag play --clock --delay=1.0 $BAG &
    ROSBAG_PID=$!

    # Espera receber ao menos uma mensagem de /clock
    echo "Aguardando /clock..."
    timeout 15 rostopic echo /clock -n 5 > /dev/null 2>&1 || true
    echo "/clock estabelecido, subindo localizacao..."
    sleep 1

    # Sobe EKF e métricas em background
    roslaunch localiza_o_robotica localization.launch \
        mode:=$MODE \
        wheel_odom_topic:=/wheel/odom \
        imu_topic:=/imu/data \
        fix_topic:=/navsat/fix \
        publish_gt:=false \
        record_metrics:=true \
        output_dir:=/home/ros/catkin_ws/src/Localiza-o-Robotica/results &
    LOCALIZATION_PID=$!

    # Espera a bag terminar
    wait $ROSBAG_PID
    echo "Bag finalizada, aguardando escrita das metricas..."
    sleep 5

    # Derruba localization e roscore
    kill $LOCALIZATION_PID 2>/dev/null
    wait $LOCALIZATION_PID 2>/dev/null
    sleep 2

    kill $ROSCORE_PID
    wait $ROSCORE_PID 2>/dev/null
    sleep 3
done

echo ""
echo "=== Gerando comparacao ==="
python /home/ros/catkin_ws/src/Localiza-o-Robotica/scripts/compare_results.py \
    --results-dir /home/ros/catkin_ws/src/Localiza-o-Robotica/results
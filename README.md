# Localiza-o-Robotica

Pacote ROS para comparar tres configuracoes de localizacao do Clearpath Husky no Gazebo usando o `ekf_localization_node` do pacote `robot_localization`:

- odometria;
- odometria + IMU;
- odometria + IMU + GPS convertido para odometria local.

O topico `/gt/odom` e publicado apenas para avaliacao e nunca e usado como entrada do filtro.

## Topicos

Entradas esperadas:

- `/wheel/odom` (`nav_msgs/Odometry`)
- `/imu/data` (`sensor_msgs/Imu`)
- `/fix` (`sensor_msgs/NavSatFix`)
- `/gt/odom` (`nav_msgs/Odometry`, gerado a partir do Gazebo)

Saidas principais:

- `/gps/odom` (`nav_msgs/Odometry`)
- `/odometry/filtered` (`nav_msgs/Odometry`)
- `results/<modo>_metrics.csv`
- `results/<modo>_summary.txt`
- `results/<modo>_plot.png`

## Como executar

Compile o workspace:

```bash
cd ~/catkin_ws
catkin build localiza_o_robotica
source devel/setup.bash
```

## Gravando uma trajetoria para comparar

Abra quatro terminais. No host, antes de abrir as interfaces graficas do Docker,
libere o X11:

```bash
xhost +local:docker
```

Em cada terminal que entrar no container, rode a preparacao:

```bash
docker exec -it ros_lar_run bash
export LIBGL_ALWAYS_SOFTWARE=1
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
```

Terminal 1:

```bash
roscore
```

Terminal 2:

```bash
roslaunch lar_gazebo lar_husky.launch
```

Terminal 3:

```bash
rosrun rqt_robot_steering rqt_robot_steering
```

Na interface do `rqt_robot_steering`, selecione o topico de comando do Husky,
normalmente `/husky_velocity_controller/cmd_vel` ou `/cmd_vel`.

Terminal 4:

```bash
roslaunch localiza_o_robotica record_trajectory.launch \
  bag:=$(rospack find localiza_o_robotica)/bags/husky_trajectory.bag
```

Manipule o robo com o joystick gerado no Terminal 3. Depois de um tempo, pare a
gravacao no Terminal 4 com `Ctrl+C`. O bag vai conter os topicos normalizados
`/wheel/odom`, `/imu/data`, `/fix` e `/gt/odom`.

Em seguida, use a gravacao para comparar os tres metodos. Rode um comando por
vez:

```bash
roslaunch localiza_o_robotica replay_bag.launch mode:=odom
roslaunch localiza_o_robotica replay_bag.launch mode:=odom_imu
roslaunch localiza_o_robotica replay_bag.launch mode:=odom_imu_gps
rosrun localiza_o_robotica compare_results.py
```

Cada replay termina sozinho quando o bag acaba e grava os arquivos em `results/`:

```bash
results/<modo>_metrics.csv
results/<modo>_summary.txt
results/<modo>_plot.png
results/comparison_position_error.png
results/comparison_yaw_error.png
results/comparison_trajectories.png
```

## Metricas geradas

O no `localization_metrics.py` compara `/odometry/filtered` com `/gt/odom` e calcula:

- erro instantaneo de posicao;
- RMSE de posicao;
- erro final de posicao;
- RMSE de orientacao em yaw;
- erro final de orientacao em yaw.

<!-- ## Discussao esperada dos resultados

A configuracao apenas com odometria tende a acumular deriva ao longo do tempo. Com IMU, a estimativa de orientacao melhora e a trajetoria costuma ficar mais estavel em curvas. Com GPS, a posicao absoluta ajuda a reduzir o erro acumulado, principalmente em trajetorias longas, mas a qualidade final depende do ruido e da taxa do sensor GPS. DEU TUDO ERRADO PAPAI -->

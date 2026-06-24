# Localiza-o-Robotica

Pacote ROS para comparar tres configuracoes de localizacao do Clearpath Husky no Gazebo usando o `ekf_localization_node` do pacote `robot_localization`:

- odometria;
- odometria + IMU;
- odometria + IMU + GPS convertido para odometria local.

O topico `/gt/odom` e publicado apenas para avaliacao e nunca e usado como entrada do filtro.

## Configuracao do ambiente

O projeto possui um `dockerfile` para preparar o ambiente ROS/Gazebo usado nos testes. Baixe esse arquivo individualmente, coloque-o em uma pasta de trabalho e gere a imagem Docker a partir dele:

```bash
docker build -t localiza_o_robotica_ros -f dockerfile .
```

Depois que a imagem for criada, inicie o container:

```bash
docker run -it \
  --env DISPLAY=$DISPLAY \
  --env QT_X11_NO_MITSHM=1 \
  --volume /tmp/.X11-unix:/tmp/.X11-unix:rw \
  --network host \
  --name ros_lar_run \
  <sua_imagem>
```

Substitua `<sua_imagem>` pelo nome da imagem gerada no passo anterior, por exemplo `localiza_o_robotica_ros`.

No host, antes de abrir interfaces graficas pelo Docker, libere o acesso ao X11:

```bash
xhost +local:docker
```

Dentro do container, clone este repositorio dentro de `~/catkin_ws/src/`:

```bash
mkdir -p ~/catkin_ws/src
cd ~/catkin_ws/src
git clone <link-do-repositorio>
```

Somente depois disso compile o workspace:

```bash
cd ~/catkin_ws
catkin build localiza_o_robotica
source devel/setup.bash
```

Sempre que abrir um novo terminal no container, carregue o ambiente:

```bash
docker exec -it ros_lar_run bash
export LIBGL_ALWAYS_SOFTWARE=1
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
```

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

## Bag de teste

O repositorio ja inclui uma bag padrao em:

```bash
bags/husky_trajectory.bag
```

Voce pode usar essa bag diretamente para reproduzir os testes ou gravar sua propria trajetoria. Atencao: ao gravar uma nova bag no mesmo caminho, a bag padrao que vem no repositorio sera apagada/substituida.

## Gravando uma nova trajetoria

Abra quatro terminais dentro do container e carregue o ambiente em todos eles:

```bash
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

Na interface do `rqt_robot_steering`, selecione o topico de comando do Husky, normalmente `/husky_velocity_controller/cmd_vel` ou `/cmd_vel`.

Terminal 4:

```bash
roslaunch localiza_o_robotica record_trajectory.launch \
  bag:=$(rospack find localiza_o_robotica)/bags/husky_trajectory.bag
```

Manipule o robo com o joystick gerado no Terminal 3. Depois de um tempo, pare a gravacao no Terminal 4 com `Ctrl+C`. O bag vai conter os topicos normalizados `/wheel/odom`, `/imu/data`, `/fix` e `/gt/odom`.

## Executando os testes com a bag

Para reproduzir a bag ja gravada e comparar os tres modos de localizacao, nao e necessario abrir Gazebo, subir o mundo, usar `rqt_robot_steering` ou iniciar `roscore` manualmente. O `roslaunch` usado pelo script inicia o master ROS quando precisar, executa a bag e encerra tudo no final.

Use um unico terminal com o ambiente carregado:

```bash
cd ~/catkin_ws
source devel/setup.bash
rosrun localiza_o_robotica run_replay.sh
```

O script limpa os resultados antigos desses modos, executa automaticamente:

- `odom`
- `odom_imu`
- `odom_imu_gps`

Cada replay termina sozinho quando a bag acaba e grava os arquivos em `results/`:

```bash
results/<modo>_metrics.csv
results/<modo>_summary.txt
results/<modo>_plot.png
results/comparison_position_error.png
results/comparison_yaw_error.png
results/comparison_trajectories.png
```

## Metricas geradas

O script `localization_metrics.py` compara `/odometry/filtered` com `/gt/odom` e calcula:

- erro instantaneo de posicao;
- RMSE de posicao;
- erro final de posicao;
- RMSE de orientacao em yaw;
- erro final de orientacao em yaw.

## Resultados e discussao

Os resultados obtidos ficam em `results/` e permitem comparar o desempenho dos tres modos. Na execucao abaixo, os tres filtros tiveram erro de posicao muito parecido, com RMSE em torno de 5,63 m e erro final em torno de 6,05 m. A diferenca mais clara apareceu na orientacao: ao adicionar a IMU, o RMSE de yaw caiu de 0,020987 rad para 0,005610 rad, e com IMU + GPS ficou em 0,004573 rad.

| modo | amostras | RMSE posicao (m) | erro final posicao (m) | RMSE yaw (rad) | erro final yaw (rad) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `odom` | 2099 | 5.629646 | 6.050049 | 0.020987 | 0.000079 |
| `odom_imu` | 2098 | 5.630747 | 6.048574 | 0.005610 | 0.000186 |
| `odom_imu_gps` | 2099 | 5.631216 | 6.050032 | 0.004573 | 0.000079 |

Neste teste, o GPS nao reduziu significativamente o erro de posicao. Isso pode acontecer quando a conversao do GPS para odometria local usa uma origem simples e quando a trajetoria gravada, os ruidos/covariancias e o proprio filtro deixam a estimativa dominada pela odometria das rodas. Mesmo assim, o modo `odom_imu_gps` manteve o melhor RMSE de yaw entre as tres configuracoes.

O grafico de erro de posicao mostra que as tres curvas ficam muito proximas durante quase todo o replay:

![Comparacao do erro de posicao](results/comparison_position_error.png)

O grafico de erro de yaw evidencia melhor a vantagem dos modos com IMU:

![Comparacao do erro de yaw](results/comparison_yaw_error.png)

Por fim, o grafico de trajetorias compara a estimativa filtrada de cada modo com o ground truth usado apenas para avaliacao:

![Comparacao das trajetorias](results/comparison_trajectories.png)

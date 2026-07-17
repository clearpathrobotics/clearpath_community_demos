# auto_explore_clearpath

Autonomous map exploration demo for Clearpath platforms on ROS 2 Jazzy.

This demo runs a frontier-based exploration node that watches the live SLAM
occupancy grid, picks a frontier target, and sends goals to Nav2 repeatedly
until the map is covered.

## Prerequisites

- Gazebo simulation or a real robot is already running
- SLAM Toolbox is running (mapping mode)
- Nav2 is running

## Build

From your workspace root:

```bash
colcon build --symlink-install --packages-select auto_explore_clearpath
source install/setup.bash
```

## Run

```bash
ros2 launch auto_explore_clearpath auto_explore.launch.py \
  use_sim_time:=true \
  setup_path:=/path/to/setup
```

## Run as one stack (SLAM + Nav2 + auto-explore)

If simulation is already running, you can launch the full mapping stack from
one command:

```bash
ros2 launch auto_explore_clearpath auto_explore_stack.launch.py \
  use_sim_time:=true \
  setup_path:=/path/to/setup
```

## Docker Compose (Jazzy, sim + nav2 + viz + auto-explore)

This demo includes a compose stack that launches simulation, Nav2 with SLAM,
RViz, and the frontier explorer in one command.

### Requirements

- Docker Compose v2
- X11 display (for Gazebo and RViz)
- **NVIDIA GPU with `nvidia-container-toolkit` (strongly recommended)**

> **Warning:** Running this demo without an NVIDIA GPU results in extremely
> slow Gazebo physics simulation. The robot and sensors will lag far behind
> real-time, causing Nav2 timeouts and unreliable behavior. For best results,
> use a discrete NVIDIA GPU and run with the NVIDIA compose overlay.

### Quick start

```bash
cd demos/auto_explore_clearpath
xhost +local:
docker compose -f docker-compose.yml -f docker-compose.nvidia.yaml up -d
```

> **Note:** Omit `-f docker-compose.nvidia.yaml` if you don't have an NVIDIA GPU,
> but expect significantly slower performance.

> **Important:** `xhost +local:` must be run before `docker compose up` or
> Gazebo will hang waiting for a display connection.

On first run, Docker will build the `cpr-auto-explore-clearpath:jazzy-local`
image. Subsequent runs reuse the cached image. To force a rebuild:

```bash
docker compose -f docker-compose.yml -f docker-compose.nvidia.yaml up --build -d
```

### Startup sequence

The stack brings up services in order with healthchecks at each gate:

1. **setup_init** – validates `${SETUP_PATH_HOST}/robot.yaml` exists
2. **sim** – Gazebo with warehouse world (healthcheck: `/clock` + odom topic).
   A watchdog automatically restarts Gazebo if it hangs on GPU initialization.
3. **tf_relay** – bridges namespaced TF to global `/tf` (healthcheck: node alive)
4. **nav2** – SLAM Toolbox + Nav2 (healthcheck: `bt_navigator` + `slam_toolbox` nodes)
5. **auto_explore** – frontier explorer sends Nav2 goals
6. **viz** – RViz with navigation config

Typical time from `docker compose up -d` to first exploration goal: **~40 seconds**.

### Configuration

The stack reads robot configuration from `${SETUP_PATH_HOST}/robot.yaml`.
`setup_init` does not seed or overwrite this file; it only validates that the
file exists.

`setup_path` must contain `robot.yaml` so the launch files can derive the
robot namespace.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ROS_DOMAIN_ID` | `0` | ROS 2 domain isolation |
| `SETUP_PATH_HOST` | `./config` | Host setup directory mounted into containers |
| `GAZEBO_STARTUP_TIMEOUT` | `120` | Seconds before watchdog restarts Gazebo |
| `GAZEBO_MAX_RESTARTS` | `3` | Max Gazebo restart attempts |
| `AUTO_EXPLORE_MAX_GOAL_DISTANCE_M` | `8.5` | Frontier goals farther than this are ignored (keeps exploration within Nav2's default 20x20 rolling global costmap window) |

### Run with a custom setup path robot file

Pass a setup path that already contains `robot.yaml`:

```bash
SETUP_PATH_HOST=$HOME/clearpath \
docker compose up -d
```

### Teardown

```bash
docker compose down
```

## Example with Clearpath sim + nav2 demos

```bash
ros2 launch clearpath_gz simulation.launch.py \
  world:=warehouse \
  setup_path:=/path/to/setup

ros2 launch clearpath_nav2_demos slam.launch.py \
  use_sim_time:=true \
  setup_path:=/path/to/setup

ros2 launch clearpath_nav2_demos nav2.launch.py \
  use_sim_time:=true \
  setup_path:=/path/to/setup

ros2 launch auto_explore_clearpath auto_explore.launch.py \
  use_sim_time:=true \
  setup_path:=/path/to/setup
```

## Save map

Once exploration is complete, save the map from the namespaced map topic:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/explored_map \
  --ros-args -r map:=/<robot_namespace>/map
```

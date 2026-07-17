---
sort: 2
---

# Auto Explore Clearpath

Autonomous exploration demo for Clearpath platforms on ROS 2 Jazzy.

This demo uses a frontier-based planner node to continuously select exploration
goals from the live SLAM map and dispatch them to Nav2.

**Source:** [`demos/auto_explore_clearpath/`](https://github.com/clearpathrobotics/clearpath_community_demos/tree/main/demos/auto_explore_clearpath)

## Supported platforms

- Husky A300, Jackal, Dingo, Ridgeback, Warthog (real or simulated)
- Any platform with Nav2 + SLAM Toolbox + 2D occupancy grid map

## Build

```bash
mkdir -p ~/auto_explore_ws/src
cd ~/auto_explore_ws/src
git clone https://github.com/clearpathrobotics/clearpath_community_demos.git

cd ~/auto_explore_ws
rosdep install \
    --from-paths src/clearpath_community_demos/demos/auto_explore_clearpath \
    --ignore-src -r -y
colcon build --symlink-install --packages-up-to auto_explore_clearpath
source install/setup.bash
```

## Run

Start simulation and mapping stack first, then run the explorer:

```bash
ros2 launch auto_explore_clearpath auto_explore.launch.py \
  use_sim_time:=true \
  setup_path:=/path/to/clearpath/setup
```

`setup_path` must contain `robot.yaml` so the demo can resolve the robot
namespace.

## One-command mapping stack

If the simulator is already running, launch SLAM + Nav2 + auto-explore:

```bash
ros2 launch auto_explore_clearpath auto_explore_stack.launch.py \
  use_sim_time:=true \
  setup_path:=/path/to/clearpath/setup
```

## Docker Compose (Jazzy, sim + nav2 + viz + auto-explore)

This demo includes a compose stack that launches simulation, Nav2 with SLAM,
RViz, and the frontier explorer in one command.

### Requirements

- Docker Compose v2
- X11 display (for Gazebo and RViz)
- **NVIDIA GPU with `nvidia-container-toolkit` (strongly recommended)**

> **Warning:** Running this demo without an NVIDIA GPU results in very slow
> Gazebo simulation and can cause Nav2 timeouts.

### Quick start

```bash
cd demos/auto_explore_clearpath
xhost +local:
docker compose -f docker-compose.yml -f docker-compose.nvidia.yaml up -d
```

> **Note:** Omit `-f docker-compose.nvidia.yaml` if you don't have an NVIDIA
> GPU, but expect slower performance.

To force a rebuild:

```bash
docker compose -f docker-compose.yml -f docker-compose.nvidia.yaml up --build -d
```

### Configuration

The stack reads robot configuration from `${SETUP_PATH_HOST}/robot.yaml`.
`setup_path` must contain `robot.yaml` so launch files can derive robot
namespace.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ROS_DOMAIN_ID` | `0` | ROS 2 domain isolation |
| `SETUP_PATH_HOST` | `./config` | Host setup directory mounted into containers |
| `AUTO_EXPLORE_MAX_GOAL_DISTANCE_M` | `8.5` | Ignore far frontiers to keep navigation goals local |

### Run with a custom setup path

```bash
SETUP_PATH_HOST=$HOME/clearpath \
docker compose up -d
```

### Teardown

```bash
docker compose down
```

## Save map

```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/explored_map \
  --ros-args -r map:=/<robot_namespace>/map
```

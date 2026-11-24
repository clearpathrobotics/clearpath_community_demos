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

## Example robot configuration

An example
[`robot.yaml`](https://github.com/clearpathrobotics/clearpath_community_demos/blob/main/demos/auto_explore_clearpath/config/robot.yaml)
is shipped with the demo: a Husky A300 with a 2D lidar, as used to test it. To
use another robot, see [Changing the robot](#changing-the-robot).

## Changing the robot

The example `config/robot.yaml` describes a Husky A300. To run the demo on
your own robot, or on another platform in simulation:

1. **Start from the right file.** On a real robot, use its own `robot.yaml`
   (`/etc/clearpath/robot.yaml`). For another platform, start from that
   platform's
   [`clearpath_config` sample](https://github.com/clearpathrobotics/clearpath_config/tree/jazzy/clearpath_config/sample) with a 2D lidar, for example `j100/j100_dual_laser.yaml` for a Jackal.
   Samples are also installed in `/opt/ros/jazzy/share/clearpath_config/sample/`
   and in the clearpath_docker images.
2. **Edit the fields the demo depends on:**

   | Field | What it sets |
   |-------|--------------|
   | `serial_number` | The robot's serial number; its prefix (`a300`, `j100`, `w200`, ...) selects the platform |
   | `system.ros2.namespace` | The robot's namespace, which the demo runs under. If you leave it out, it is derived from the serial number |
   | `system.ros2.domain_id` | The ROS domain ID, from 0 to 101 |
   | `system.ros2.middleware` | The middleware settings; keep them as they are for the Docker Compose stack, including the `profile` |
   | `system.hosts` | The robot computer's hostname and IP (real robots only) |
   | `platform.attachments` | Attachments; they must belong to the platform, which is why another platform starts from its sample |
   | `sensors.lidar2d` | A 2D lidar as the first entry: SLAM and Nav2 use its scan (`sensors/lidar2d_0/scan`). It must also see beside and behind its mount, so the map covers the robot itself; otherwise Nav2 can't plan from the robot's position. The Warthog sample limits its lidars to the front 180°: widen the first one's `angle_min` and `angle_max` (for example to `-2.35` and `2.35`, the Hokuyo UST's 270°) |

   See the [`clearpath_config` documentation](https://docs.clearpathrobotics.com/docs/ros/config/yaml/overview/)
   for every field.
3. **Use it** natively, as in [Using another robot](#using-another-robot), or
   with Docker Compose, as in
   [Using another robot with Docker Compose](#using-another-robot-with-docker-compose).

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

The explorer needs these running first:

- Gazebo simulation or a real robot
- SLAM Toolbox, in mapping mode
- Nav2

Then start the explorer:

```bash
ros2 launch auto_explore_clearpath auto_explore.launch.py \
  use_sim_time:=true \
  setup_path:=/path/to/clearpath/setup
```

`setup_path` must contain `robot.yaml` so the demo can resolve the robot
namespace.

For example, with the Clearpath simulator and Nav2 demos:

```bash
ros2 launch clearpath_gz simulation.launch.py \
  world:=warehouse \
  setup_path:=/path/to/clearpath/setup

ros2 launch clearpath_nav2_demos slam.launch.py \
  use_sim_time:=true \
  setup_path:=/path/to/clearpath/setup

ros2 launch clearpath_nav2_demos nav2.launch.py \
  use_sim_time:=true \
  setup_path:=/path/to/clearpath/setup

ros2 launch auto_explore_clearpath auto_explore.launch.py \
  use_sim_time:=true \
  setup_path:=/path/to/clearpath/setup
```

### Using another robot

Put your `robot.yaml` in a directory and pass that directory as `setup_path`
to every launch above: the simulator (or robot), SLAM, Nav2, and the explorer
must all read the same file. On a real robot, that is usually
`/etc/clearpath/`. The example's middleware `profile` points to the demo's
`cyclonedds.xml` for Docker; natively, remove that line or point it to a
CycloneDDS profile on your machine.

After editing `robot.yaml`, restart the simulator: it regenerates the robot
description and launch files from `robot.yaml` each time it starts.

## Explorer behavior

The explorer targets the nearest frontier, with a small bonus for frontiers
that border more unexplored space. It skips frontiers that Nav2's global
costmap marks as too close to obstacles. Once the robot is close to a frontier
it counts it as visited and moves on, rather than waiting for Nav2 to reach the
exact goal pose; a goal that isn't reached in time, scaled by its distance, is
canceled. Tune it with these `auto_explore.launch.py` arguments:

| Argument | Default | Description |
|----------|---------|-------------|
| `max_goal_distance_m` | `20.0` | Ignore frontiers farther than this (the Docker Compose stack uses `8.5`) |
| `max_goal_cost` | `50` | Skip frontiers whose Nav2 global costmap cost (0-100) is above this |
| `goal_reached_distance_m` | `0.6` | Count a frontier as visited once the robot is this close |
| `goal_timeout_sec` | `30.0` | Minimum seconds before an unfinished goal is canceled |
| `goal_timeout_per_m_sec` | `15.0` | Seconds allowed per meter to the goal, when that is longer |
| `replan_period_sec` | `2.0` | Seconds between frontier replanning attempts |

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

> **Note:** Omit `-f docker-compose.nvidia.yaml` if you don't have an NVIDIA
> GPU, but expect significantly slower performance.

> **Important:** `xhost +local:` must be run before `docker compose up` or
> Gazebo will hang waiting for a display connection.

On first run, Docker pulls the published
`ghcr.io/clearpathrobotics/clearpath_community_demos:jazzy-auto_explore_clearpath-latest`
image, or builds it locally if it isn't available. Subsequent runs reuse it. To
build it from your checkout instead, for example after changing the demo:

```bash
docker compose -f docker-compose.yml -f docker-compose.nvidia.yaml up --build -d
```

### Startup sequence

The stack brings up services in order, using the health checks built into the
clearpath_docker images as gates:

1. **setup_init** – checks that `${SETUP_PATH_HOST}/robot.yaml` exists
2. **sim** – Gazebo with the warehouse world; healthy once `/clock` and the
   robot's odometry are publishing. A watchdog restarts Gazebo if `/clock`
   doesn't appear within `GAZEBO_STARTUP_TIMEOUT`.
3. **nav2** – SLAM Toolbox + Nav2, started once the sim is healthy; healthy once
   Nav2's nodes are active and the map is publishing
4. **auto_explore** – started once Nav2 is healthy; runs `tf_relay`, which
   bridges the namespaced TF to global `/tf`, and the frontier explorer, which
   sends Nav2 goals
5. **viz** – RViz with the navigation config, started with the sim

With an NVIDIA GPU and Gazebo models already cached, the sim and Nav2 are
typically healthy 1 to 2 minutes after `docker compose up -d`, and the first
exploration goal follows a few seconds later.

### Configuration

The stack reads robot configuration from `${SETUP_PATH_HOST}/robot.yaml`.
`setup_init` does not seed or overwrite this file; it only checks that the file
exists and makes the directory writable for the containers.

Every container takes its ROS settings from the `system.ros2` section of
`robot.yaml`, as on a robot: the domain ID (`domain_id`), CycloneDDS
(`middleware.implementation`), localhost-only discovery
(`middleware.automatic_discovery_range`), and the CycloneDDS profile
`cyclonedds.xml` (`middleware.profile`), which keeps traffic on the loopback
interface.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SETUP_PATH_HOST` | `./config` | Host setup directory mounted into containers |
| `AUTO_EXPLORE_USE_SIM_TIME` | `true` | Use Gazebo time for the explorer node |
| `GAZEBO_STARTUP_TIMEOUT` | `120` | Seconds before the watchdog restarts Gazebo |
| `GAZEBO_MAX_RESTARTS` | `3` | Max Gazebo restart attempts |
| `AUTO_EXPLORE_MAX_GOAL_DISTANCE_M` | `8.5` | Frontier goals farther than this are ignored (keeps exploration within Nav2's default 20x20 rolling global costmap window) |

### Using another robot with Docker Compose

Either edit `config/robot.yaml`, or put your own `robot.yaml` in a directory and
pass it with `SETUP_PATH_HOST`. Keep the middleware settings, and copy
`config/cyclonedds.xml` into a directory of your own, since every container
reads the profile from the setup directory.

After editing `robot.yaml`, stop the stack and start it again, so the
simulator regenerates the robot description and launch files:

```bash
docker compose down
SETUP_PATH_HOST=$HOME/clearpath docker compose up -d
```

### Teardown

```bash
docker compose down
```

## Save map

Once exploration is complete, save the map from the namespaced map topic. The
example `config/robot.yaml` uses the namespace `a300_0000`; use yours if you
changed it.

With the Docker Compose stack, run `cpr-nav2 save-map` in the `nav2`
container, from `demos/auto_explore_clearpath`. It finds the namespace from
`robot.yaml` and writes `explored_map.yaml` and `explored_map.pgm` to
`config/maps` (`maps` in `SETUP_PATH_HOST`):

```bash
docker compose exec nav2 cpr-nav2 save-map explored_map
```

To save from a host ROS 2 install instead, use the same middleware settings as
`config/robot.yaml`, from `demos/auto_explore_clearpath`, or the map saver
won't receive the map:

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export CYCLONEDDS_URI=file://$PWD/config/cyclonedds.xml
ros2 run nav2_map_server map_saver_cli -f config/maps/explored_map \
  --ros-args -r map:=/a300_0000/map
```

Without Docker, run that last command in the same environment as the demo.

To navigate on the saved map later, see
[Saving and loading a map](https://github.com/clearpathrobotics/clearpath_docker#saving-and-loading-a-map)
in clearpath_docker.

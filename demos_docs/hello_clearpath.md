---
sort: 1
---

# Hello Clearpath

A minimal "hello world" demo that publishes a greeting and drives the robot in
a small square. Use this to verify your environment is set up correctly before
trying more complex demos.

The package ships **two interchangeable implementations** — one in C++
(`hello_square_cpp`) and one in Python (`hello_square_py`) — so it can also
serve as a starting template for new demos in either language.

**Source:** [`demos/hello_clearpath/`](https://github.com/clearpathrobotics/clearpath_community_demos/tree/main/demos/hello_clearpath)

## Supported platforms

- Husky A300, Jackal, Dingo, Ridgeback, Warthog (real or simulated)
- Any platform exposing `/cmd_vel`

## Example robot configuration

An example
[`robot.yaml`](https://github.com/clearpathrobotics/clearpath_community_demos/blob/main/demos/hello_clearpath/config/robot.yaml)
is shipped with the demo as a reference for the
[`clearpath_config`](https://docs.clearpathrobotics.com/docs/ros/config/yaml/overview/)
that was used to test it. To use another robot, see
[Changing the robot](#changing-the-robot).

## Changing the robot

The example `config/robot.yaml` describes a Husky A300. To run the demo on
your own robot, or on another platform in simulation:

1. **Start from the right file.** On a real robot, use its own `robot.yaml`
   (`/etc/clearpath/robot.yaml`). For another platform, start from that
   platform's
   [`clearpath_config` sample](https://github.com/clearpathrobotics/clearpath_config/tree/jazzy/clearpath_config/sample), for example `j100/j100_default.yaml` for a Jackal.
   Samples are also installed in `/opt/ros/jazzy/share/clearpath_config/sample/`
   and in the clearpath_docker images.
2. **Edit the fields the demo depends on:**

   | Field | What it sets |
   |-------|--------------|
   | `serial_number` | The robot's serial number; its prefix (`a300`, `j100`, `w200`, ...) selects the platform |
   | `system.ros2.namespace` | The robot's namespace, which the demo runs under. If you leave it out, it is derived from the serial number |
   | `system.ros2.domain_id` | The ROS domain ID, from 0 to 101 |
   | `system.ros2.middleware` | The middleware settings; keep CycloneDDS (`rmw_cyclonedds_cpp`) for the Docker Compose stack |
   | `system.hosts` | The robot computer's hostname and IP (real robots only) |
   | `platform.attachments` | Attachments; they must belong to the platform, which is why another platform starts from its sample |

   See the [`clearpath_config` documentation](https://docs.clearpathrobotics.com/docs/ros/config/yaml/overview/)
   for every field.
3. **Use it** natively, as in [Using another robot](#using-another-robot), or
   with Docker Compose, as in
   [Using another robot with Docker Compose](#using-another-robot-with-docker-compose).

## Build

This demo is built in its own dedicated workspace. See
[Workspaces](../getting_started/building.md) for the general pattern.

Clone the repository into a fresh `hello_clearpath_ws` workspace, install
only this demo's dependencies, and build only this package and the packages
it depends on:

```bash
mkdir -p ~/hello_clearpath_ws/src
cd ~/hello_clearpath_ws/src
git clone https://github.com/clearpathrobotics/clearpath_community_demos.git

cd ~/hello_clearpath_ws
rosdep install \
    --from-paths src/clearpath_community_demos/demos/hello_clearpath \
    --ignore-src -r -y
colcon build --symlink-install --packages-up-to hello_clearpath
source install/setup.bash
```

## Run

The launch file reads `robot.yaml` from the Clearpath setup path
(`/etc/clearpath/` by default), pushes the demo node under the namespace
declared there, and forwards `use_sim_time` so the demo works correctly in
both simulation and on a real robot.

With your robot running and a `/cmd_vel` consumer active:

```bash
source ~/hello_clearpath_ws/install/setup.bash

# C++ implementation (default), real robot
ros2 launch hello_clearpath hello_clearpath.launch.py

# Python implementation
ros2 launch hello_clearpath hello_clearpath.launch.py language:=python

# Simulation
ros2 launch hello_clearpath hello_clearpath.launch.py use_sim_time:=true

# Custom Clearpath setup path
ros2 launch hello_clearpath hello_clearpath.launch.py \
    setup_path:=/path/to/your/clearpath/setup
```

The robot will drive a 1 m × 1 m square and log a message at each corner.

### Using another robot

On a real robot, the demo reads the robot's own `/etc/clearpath/robot.yaml` by
default, so it already matches the robot. In simulation, put your `robot.yaml`
in a directory and pass that directory to both the simulator and the demo:

```bash
ros2 launch clearpath_gz simulation.launch.py setup_path:=/path/to/dir

source ~/hello_clearpath_ws/install/setup.bash
ros2 launch hello_clearpath hello_clearpath.launch.py \
    use_sim_time:=true setup_path:=/path/to/dir
```

After editing `robot.yaml`, restart the simulator: it regenerates the robot
description and launch files from `robot.yaml` each time it starts.

## Docker Compose (Jazzy, sim + viz + demo / robot + demo)

The demo folder includes a Jazzy-only compose stack with two profiles:

- `sim`: simulation + visualization + `hello_clearpath`
- `robot`: `hello_clearpath` (expects robot stack already running on host)

Prerequisites:

- Install Docker on the Linux host machine before using either profile.
- For `sim`, `viz`, and demo, Docker must be available on the host.
- For `robot` and demo, Docker must be available on the host.
- **NVIDIA GPU with `nvidia-container-toolkit` is strongly recommended for the `sim` profile.**

> **Warning (`sim` profile):** Running without an NVIDIA GPU can make Gazebo
> simulation very slow. Robot motion and sensors may lag behind real time,
> which can cause unstable demo behavior.

Safety warning (`robot` profile):

- This mode can command a physical robot. Ensure an E-stop is available, the area is clear, and the robot is safely supported before launching.

```bash
cd demos/hello_clearpath
xhost +local:
docker compose --profile sim up
```

For better sim performance with NVIDIA:

```bash
cd demos/hello_clearpath
xhost +local:
docker compose -f docker-compose.yml -f docker-compose.nvidia.yaml --profile sim up
```

For robot + demo:

```bash
cd demos/hello_clearpath
docker compose --profile robot up
```

By default, `hello_clearpath` services use the published GHCR image:

- `ghcr.io/clearpathrobotics/clearpath_community_demos:jazzy-hello_clearpath-latest`

The hello container image also ships with a default config at
`/etc/clearpath/robot.yaml` (copied from `config/robot.yaml` at build time),
so it is usable out-of-the-box. You can still override it by bind-mounting a
host setup directory and setting `SETUP_PATH` accordingly.

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HELLO_LANGUAGE` | `cpp` | Implementation to run: `cpp` or `python` |
| `USE_SIM_TIME` | sim: `true`, robot: `false` | Use the simulator clock |
| `WAIT_FOR_SIM` | sim: `true`, robot: `false` | Wait for `/clock` and odometry before starting the demo |
| `WAIT_FOR_TIMEOUT_SEC` | `120` | Seconds to wait for each of them before starting anyway |
| `SETUP_PATH_HOST` | `./config` | Host setup directory for the `sim` profile |
| `ROBOT_SETUP_PATH_HOST` | `/etc/clearpath/` | Host setup directory for the `robot` profile |

The ROS domain ID, middleware, and discovery range come from the `system.ros2`
section of `robot.yaml` in the setup directory, as on a robot. The `robot`
profile reads the robot's own `robot.yaml`, so it matches the robot.

### Using another robot with Docker Compose

The `sim` profile uses `demos/hello_clearpath/config/` as the setup directory:
the simulator reads its `robot.yaml` and writes generated files next to it,
which git ignores. Either edit `config/robot.yaml`, or put your own
`robot.yaml` in a directory and pass it with `SETUP_PATH_HOST`. Keep the
middleware set to CycloneDDS.

The `robot` profile reads `/etc/clearpath/robot.yaml` on the robot, so it
already matches the robot; `ROBOT_SETUP_PATH_HOST` points it elsewhere.

After editing `robot.yaml`, stop the stack and start it again, so the
simulator regenerates the robot description and launch files:

```bash
cd demos/hello_clearpath
docker compose --profile sim down
SETUP_PATH_HOST=/path/to/dir docker compose --profile sim up
```

## GitHub Image Build

This repository includes a GitHub Actions workflow that builds the hello image
from `demos/hello_clearpath/Dockerfile`:

- Pull requests: build validation only (no push)
- Pushes to `main`: build and push to GHCR

Published tags:

- `ghcr.io/clearpathrobotics/clearpath_community_demos:jazzy-hello_clearpath-latest`

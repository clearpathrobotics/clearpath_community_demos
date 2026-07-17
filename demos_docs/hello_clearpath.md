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
that was used to test it. Update to match your robot before deploying.

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

By default, the stack creates and uses a writable
`demos/hello_clearpath/config/.setup_path/` directory, auto-seeded from
`config/robot.yaml`.

For the `robot` profile, the stack uses `/etc/clearpath/robot.yaml` on the
Linux host by default.

To override the robot configuration, provide a host setup directory containing
your own `robot.yaml`:

```bash
cd demos/hello_clearpath
SETUP_PATH_HOST=/path/to/clearpath_setup docker compose --profile sim up
ROBOT_SETUP_PATH_HOST=/path/to/clearpath_setup docker compose --profile robot up
```

By default, `hello_clearpath` services use the published GHCR image:

- `ghcr.io/clearpathrobotics/clearpath_community_demos:jazzy-hello_clearpath-latest`

The hello container image also ships with a default config at
`/etc/clearpath/robot.yaml` (copied from `config/robot.yaml` at build time),
so it is usable out-of-the-box. You can still override it by bind-mounting a
host setup directory and setting `SETUP_PATH` accordingly.

The entrypoint waits for simulation readiness by default before launching the
demo command. To tune this behavior:

- `WAIT_FOR_SIM=true|false` (default: `true`)
- `WAIT_FOR_TIMEOUT_SEC=<seconds>` (default: `60`)

## GitHub Image Build

This repository includes a GitHub Actions workflow that builds the hello image
from `demos/hello_clearpath/Dockerfile`:

- Pull requests: build validation only (no push)
- Pushes to `main`: build and push to GHCR

Published tags:

- `ghcr.io/clearpathrobotics/clearpath_community_demos:jazzy-hello_clearpath-latest`

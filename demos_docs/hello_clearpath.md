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
[Workspaces](../getting_started/building.md) for the general pattern. The
source repositories required by the demo are declared in
[`hello_clearpath.repos`](https://github.com/clearpathrobotics/clearpath_community_demos/blob/main/demos/hello_clearpath/hello_clearpath.repos).

```bash
mkdir -p ~/hello_clearpath_ws/src
cd ~/hello_clearpath_ws
vcs import src < <(curl -fsSL \
    https://raw.githubusercontent.com/clearpathrobotics/clearpath_community_demos/main/demos/hello_clearpath/hello_clearpath.repos)

rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
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

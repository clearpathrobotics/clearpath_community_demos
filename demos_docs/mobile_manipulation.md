---
sort: 2
---

# Whole-Body Mobile Manipulation

This example shows whole-body motion planning and control for a mobile manipulator. The platform, **Reachback**, pairs a [Clearpath Ridgeback](https://clearpathrobotics.com/ridgeback-indoor-robot-platform/) omnidirectional base with a [Doosan H2017](https://www.doosanrobotics.com/en/product-solutions/product/h-series/h2017/) 6-DOF industrial arm and an [OnRobot 2FG14](https://onrobot.com/en/products/2fg14-finger-gripper), yielding a 9-DOF system (3 base + 6 arm) capable of whole-body motion planning.

Please note that this example is meant for simulation only and has not been tested with hardware!

**Source:** [`demos/mobile_manipulation_ws/`](https://github.com/clearpathrobotics/clearpath_community_demos/tree/main/demos/unified_manipulation_config_ws)

## Supported platforms

- No supported hardware

## Example robot configuration

This example does not use a robot.yaml

### Requirements

This project uses Docker to manage dependencies.
To install Docker:

1. Follow the official [Docker install instructions](https://docs.docker.com/engine/install/ubuntu/)
2. Follow the official [Docker post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/)
3. Install Docker Compose: `sudo apt install docker-compose-plugin`

> Note:
> This repository requires a patched version of MoveIt and joint trajectory controller version >= 4.40
> We're currently working on releasing these images so you won't need to build yourself.
> In the meantime, the patches are publicly available; you will need to build [ros2_controllers](https://github.com/ros-controls/ros2_controllers/tree/4.40.0) and MoveIt with [these](https://github.com/moveit/moveit2/pull/3702) [changes](https://github.com/moveit/moveit2/pull/3704).

> The Docker setup assumes you're using NVIDIA graphics.

Run the setup script to create the .env file to capture your UID and GID.
You will only need to run this script once.
```bash
./set-up-container-user.sh
```

> Please note that this project uses dependencies that are not provided by rosdep!
> `rosdep install` will *not* be sufficient to install all depenendencies.
> If you would like to work outside of the Docker image, please see the [Dockerfile](./docker/Dockerfile) for a complete list of dependencies.

### Building the Docker Container

From the mobile_manipulation_ws directory (`cd demos/mobile_manipulation_ws`), build the container with:
```bash
docker compose build
```

Run with:
```bash
docker compose up -d
```

Then, exec into the container with:
```bash
./docker-compose-shell.sh
```

### Building

From inside the container, import dependencies:

```bash
vcs import --recursive src/vendor < mobile_manipulation.repos
```

Build packages up to the demos from the workspace root:

```bash
colcon build --symlink-install --packages-up-to mm_demo
source install/setup.bash
```

## Run

To launch the RViz motion planning demo where you can drag the interactive marker to plan, use:

```bash
ros2 launch reachback_moveit_config moveit_rviz.launch
```

Two Cartesian planning demos are also available, writing text:

```bash
ros2 launch mm_demo cartesian_task.launch mode:=write_letters
```

and drawing a square:

```bash
ros2 launch mm_demo cartesian_task.launch mode:=draw_square
```

---
sort: 1
---

# Prerequisites

Demos run either on a native ROS 2 install or in Docker. Each demo's page
says which it supports, and may list additional prerequisites.

## Option 1: Native ROS 2

1. A working **Clearpath robot** (real or simulated) with the
   [Clearpath ROS 2 stack](https://docs.clearpathrobotics.com/docs/ros/) installed.
2. **ROS 2 Jazzy** on your development machine.
3. **Git** and **colcon** for cloning and building workspaces.

```bash
sudo apt update
sudo apt install -y git python3-colcon-common-extensions python3-rosdep
```

## Option 2: Docker

The Hello Clearpath and Auto Explore Docker Compose stacks run the
simulation, Nav2, RViz, and the demo in containers built on the
[clearpath_docker](https://github.com/clearpathrobotics/clearpath_docker)
images, so the host needs no ROS installation. On a Linux host, you need:

1. **Docker Engine** with the **Docker Compose v2** plugin (`docker compose`):
   follow the [Docker install instructions](https://docs.docker.com/engine/install/ubuntu/)
   and the [post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/)
   to run Docker without `sudo`.
2. **Git** for cloning the repository.
3. An **X11 display** for Gazebo and RViz. Allow local containers to use it
   before starting a stack:

   ```bash
   xhost +local:
   ```

4. Optionally, an **NVIDIA GPU** with the
   [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html),
   for real-time simulation with the demos' NVIDIA compose overlays. Without
   one, Gazebo runs much slower.

Check the installation:

```bash
docker run --rm hello-world
docker compose version
```

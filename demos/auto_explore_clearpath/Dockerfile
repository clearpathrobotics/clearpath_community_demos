# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# auto_explore_clearpath - Dockerfile
# Base: ROS 2 Jazzy
# ---------------------------------------------------------------------------
ARG ROS_DISTRO=jazzy
ARG CPR_BASE_IMAGE=ghcr.io/clearpathrobotics/clearpath_docker
ARG CPR_BASE_TAG=${ROS_DISTRO}-latest

FROM ros:${ROS_DISTRO}-ros-base AS builder
ARG ROS_DISTRO

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-colcon-common-extensions \
        python3-rosdep \
        ros-${ROS_DISTRO}-clearpath-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ws/src/clearpath_community_demos/demos
COPY demos/auto_explore_clearpath auto_explore_clearpath

RUN rosdep update --rosdistro ${ROS_DISTRO}
RUN apt-get update
RUN rosdep install \
        --from-paths /ws/src/clearpath_community_demos/demos/auto_explore_clearpath \
        --ignore-src -r -y

WORKDIR /ws
RUN . /opt/ros/${ROS_DISTRO}/setup.sh && \
    colcon build \
        --packages-up-to auto_explore_clearpath \
        --cmake-args -DCMAKE_BUILD_TYPE=Release

FROM ${CPR_BASE_IMAGE}:${ROS_DISTRO}-nav2-latest AS cpr-common

FROM ${CPR_BASE_IMAGE}:${CPR_BASE_TAG} AS runtime
ARG ROS_DISTRO

RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-${ROS_DISTRO}-clearpath-config \
        ros-${ROS_DISTRO}-clearpath-nav2-demos \
        ros-${ROS_DISTRO}-clearpath-common \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /ws/install /ws/install
COPY --from=cpr-common /usr/local/bin/cpr-common.sh /usr/local/bin/cpr-common.sh

COPY demos/auto_explore_clearpath/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /usr/local/bin/cpr-common.sh /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["ros2", "launch", "auto_explore_clearpath", "auto_explore_stack.launch.py"]
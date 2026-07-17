# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# hello_clearpath – Dockerfile
# Base: ROS 2 Jazzy desktop
# ---------------------------------------------------------------------------
ARG ROS_DISTRO=jazzy
ARG CPR_BASE_IMAGE=ghcr.io/clearpathrobotics/clearpath_docker
ARG CPR_BASE_TAG=${ROS_DISTRO}-latest

FROM ros:${ROS_DISTRO}-ros-base AS builder
ARG ROS_DISTRO

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-colcon-common-extensions \
        python3-rosdep \
        python3-pip \
        ros-${ROS_DISTRO}-clearpath-config \
    && rm -rf /var/lib/apt/lists/*

# Copy only the demo source so layer caching survives unrelated repo changes
WORKDIR /ws/src/clearpath_community_demos/demos
COPY demos/hello_clearpath hello_clearpath

# Initialize rosdep (already done in base image, but update to be safe)
RUN rosdep update --rosdistro ${ROS_DISTRO}

# Install package dependencies declared in package.xml
RUN rosdep install \
        --from-paths /ws/src/clearpath_community_demos/demos/hello_clearpath \
        --ignore-src -r -y

# Build
WORKDIR /ws
RUN . /opt/ros/${ROS_DISTRO}/setup.sh && \
    colcon build \
        --packages-up-to hello_clearpath \
        --cmake-args -DCMAKE_BUILD_TYPE=Release

# ---------------------------------------------------------------------------
# Runtime image (smaller — drop build tools)
# ---------------------------------------------------------------------------
FROM ${CPR_BASE_IMAGE}:${ROS_DISTRO}-nav2-latest AS cpr-common

FROM ${CPR_BASE_IMAGE}:${CPR_BASE_TAG} AS runtime
ARG ROS_DISTRO

# Runtime-only Clearpath dependency
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-${ROS_DISTRO}-clearpath-config \
        ros-${ROS_DISTRO}-clearpath-common \
    && rm -rf /var/lib/apt/lists/*

# Copy the built install tree from the builder stage
COPY --from=builder /ws/install /ws/install
COPY --from=cpr-common /usr/local/bin/cpr-common.sh /usr/local/bin/cpr-common.sh

# Default Clearpath setup path (robot.yaml lives here inside the container)
ENV CLEARPATH_SETUP_PATH=/etc/clearpath

# Copy the example robot.yaml so the container is usable out-of-the-box.
# Mount your own robot.yaml at /etc/clearpath/robot.yaml to override.
RUN mkdir -p /etc/clearpath
COPY demos/hello_clearpath/config/robot.yaml /etc/clearpath/robot.yaml

# Entrypoint: source the workspace then exec the supplied command
COPY demos/hello_clearpath/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /usr/local/bin/cpr-common.sh /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]

# Default command launches the demo (overridden by docker-compose or CLI)
CMD ["ros2", "launch", "hello_clearpath", "hello_clearpath.launch.py"]

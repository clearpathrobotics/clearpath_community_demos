#!/bin/bash
# docker-entrypoint.sh – source the ROS 2 and workspace setup files, then run CMD.
set -e

# Source shared demo utilities
# shellcheck disable=SC1091
source /usr/local/bin/cpr-common.sh

# ROS domain, middleware, and discovery settings from robot.yaml, as on a robot
load_ros_env

# Source ROS 2 base layer
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash

# Source the built workspace if it exists
if [ -f /ws/install/setup.bash ]; then
    # shellcheck disable=SC1091
    source /ws/install/setup.bash
fi

wait_for_sim_if_enabled

exec "$@"

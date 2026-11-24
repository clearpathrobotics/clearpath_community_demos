#!/bin/bash
set -e

# shellcheck disable=SC1091
source /usr/local/bin/cpr-common.sh

# ROS domain, middleware, and discovery settings from robot.yaml, as on a robot
load_ros_env

# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash

if [ -f /ws/install/setup.bash ]; then
    # shellcheck disable=SC1091
    source /ws/install/setup.bash
fi

wait_for_sim_if_enabled

exec "$@"

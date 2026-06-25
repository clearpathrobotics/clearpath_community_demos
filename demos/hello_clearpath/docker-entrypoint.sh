#!/bin/bash
# docker-entrypoint.sh – source the ROS 2 and workspace setup files, then run CMD.
set -e

# Source ROS 2 base layer
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash

# Source the built workspace if it exists
if [ -f /ws/install/setup.bash ]; then
    # shellcheck disable=SC1091
    source /ws/install/setup.bash
fi

wait_for_sim_if_enabled() {
    local wait_for_sim="${WAIT_FOR_SIM:-true}"
    if [[ "${wait_for_sim}" != "true" ]]; then
        return 0
    fi

    local timeout_sec="${WAIT_FOR_TIMEOUT_SEC:-60}"
    local sleep_sec=1
    local waited=0

    echo "[entrypoint] WAIT_FOR_SIM=true, waiting for simulation topics..."
    echo "[entrypoint] expecting: /clock and */platform/odom/filtered"

    while (( waited < timeout_sec )); do
        local topics
        topics="$(ros2 topic list 2>/dev/null || true)"

        if echo "${topics}" | grep -Fxq "/clock" && \
           echo "${topics}" | grep -Eq '/platform/odom/filtered$'; then
            echo "[entrypoint] Simulation topics detected. Launching command."
            return 0
        fi

        sleep "${sleep_sec}"
        waited=$((waited + sleep_sec))
    done

    echo "[entrypoint] Timeout waiting for simulation topics after ${timeout_sec}s; launching anyway." >&2
    return 0
}

wait_for_sim_if_enabled

exec "$@"

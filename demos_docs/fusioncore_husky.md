---
sort: 2
---

# FusionCore Sensor Fusion (Husky A200)

Fuses the Husky A200 wheel odometry, Microstrain 3DM-GX5-25 IMU, and
u-blox F9P GPS using [FusionCore](https://github.com/manankharwar/fusioncore),
a ROS 2 UKF. Outputs a continuous global-frame `odom -> base_link` TF and
`/fusion/odom` at 100 Hz, ready for Nav2.

**Source:** [`demos/fusioncore_husky/`](https://github.com/clearpathrobotics/clearpath_community_demos/tree/main/demos/fusioncore_husky)

## Supported platforms

- Husky A200 (real or simulated)

## Prerequisites

```bash
sudo apt install ros-jazzy-fusioncore-ros
```

## Install

```bash
mkdir -p ~/community_ws/src && cd ~/community_ws/src
git clone https://github.com/clearpathrobotics/clearpath_community_demos.git
cd ~/community_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select fusioncore_husky
source install/setup.bash
```

## Run

```bash
ros2 launch fusioncore_husky fusioncore_husky.launch.py setup_path:=/etc/clearpath/
```

FusionCore will initialize on the first IMU message and start publishing
`/fusion/odom` and the `odom -> base_link` TF. Point Nav2 at `/fusion/odom`.

## Configuration

The config file at
[`config/husky_fusioncore.yaml`](../demos/fusioncore_husky/config/husky_fusioncore.yaml)
contains noise values pulled from the Microstrain 3DM-GX5-25 and u-blox F9P
datasheets. Key parameters to adjust for your hardware:

| Parameter | Default | Notes |
|---|---|---|
| `gnss.lever_arm_z` | 0.0 | Set to antenna height above base_link |
| `gnss.base_noise_xy` | 2.5 m | Lower to 0.015 for RTK fixed |
| `gnss.min_fix_type` | 1 (GPS) | Set to 4 for RTK fixed only |
| `imu.frame_id` | imu_link | Match your IMU TF frame |

## Topic remaps

The launch file handles the Husky non-default topic names automatically:

| FusionCore topic | Clearpath platform topic |
|---|---|
| `/imu/data` | `/<namespace>/sensors/imu_0/data` |
| `/odom/wheels` | `/<namespace>/platform/odom` |
| `/gnss/fix` | `/fix` |

The namespace (e.g. `a200_0000`) is read from `robot.yaml` at the `setup_path`.
Pass `setup_path:=<path>` if your robot.yaml is not at `/etc/clearpath/`.

## Full documentation

Config reference and tuning guide: <https://github.com/manankharwar/fusioncore>

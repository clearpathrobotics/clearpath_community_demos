---
sort: 1
---

# Overview

The **Clearpath Community Demos** repository is a place for users of Clearpath
Robotics platforms to share end-to-end examples that go beyond the basic
documentation — things like inspection routines, autonomy stacks, fleet
behaviors, custom payload integrations, and creative use cases.

## What you'll find here

- **Documentation** for each demo (this site)
- **Source code** for each demo, organized under the [`demos/`](https://github.com/clearpathrobotics/clearpath_community_demos/tree/main/demos)
  directory of the repository
- **Tutorials** describing how to set up your robot, build the demos, and run them
- **Contribution guidelines** for adding your own demo

## Supported platforms

Demos in this repository may target any Clearpath platform, including but not
limited to:

- Husky A300 / Husky A200
- Jackal
- Dingo
- Warthog
- Ridgeback

Each demo specifies which platform(s) it has been tested on.

## Software requirements

Most demos target **ROS 2 Jazzy** with the Clearpath ROS 2 stack.
Refer to the [Clearpath Robotics, by Rockwell Automation documentation](https://docs.clearpathrobotics.com/)
for setting up your robot before running a demo.

Demos may be written in **Python** (`ament_python`) or **C++** (`ament_cmake`),
and individual packages may also use additional tooling — each demo's page
documents its specific dependencies.

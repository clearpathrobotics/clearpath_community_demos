---
sort: 2
---

# Cloning the Repository

The community demos live under the [`demos/`](https://github.com/clearpathrobotics/clearpath_community_demos/tree/main/demos)
directory of this repository. Each subfolder is an independent ROS 2 package
(or set of packages) that you can build with `colcon`.

Clone the repository into a ROS 2 workspace:

```bash
mkdir -p ~/community_ws/src
cd ~/community_ws/src
git clone https://github.com/clearpathrobotics/clearpath_community_demos.git
```

Each demo is built independently — community demos may have unrelated
dependencies, so building all of them at once is rarely what you want. See the
**Build** section on each individual demo's page for instructions on
installing only that demo's dependencies and building only the packages it
needs.

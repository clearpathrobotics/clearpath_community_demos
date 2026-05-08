---
sort: 2
---

# Building the Demos

The community demos live under the [`demos/`](https://github.com/clearpathrobotics/clearpath_community_demos/tree/main/demos)
directory of this repository. Each subfolder is an independent ROS 2 package
(or set of packages) that you can build with `colcon`.

## Clone the repository

```bash
mkdir -p ~/community_ws/src
cd ~/community_ws/src
git clone https://github.com/clearpathrobotics/clearpath_community_demos.git
```

## Install dependencies

```bash
cd ~/community_ws
rosdep install --from-paths src --ignore-src -r -y
```

## Build

Build only the demo (or demos) you actually want to run — community demos are
independent packages and may have unrelated dependencies, so building all of
them at once is rarely what you want.

```bash
cd ~/community_ws
colcon build --symlink-install --packages-select <demo_package_name>
source install/setup.bash
```

For example, to build just the `hello_clearpath` demo:

```bash
colcon build --symlink-install --packages-select hello_clearpath
```

If you do want to build everything in the repository, omit `--packages-select`:

```bash
colcon build --symlink-install
```

You can now follow the instructions for any individual demo on this site.

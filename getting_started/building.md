---
sort: 2
---

# Workspaces

This page is for building demos from source on a native ROS 2 install. With
Docker, you don't need a workspace: clone the repository and follow the
demo's **Docker Compose** section, which builds the demo's image for you.

```bash
git clone https://github.com/clearpathrobotics/clearpath_community_demos.git
```

Each community demo is built in its own dedicated colcon workspace.
Community demos may have unrelated — and sometimes conflicting —
dependencies, so they are not intended to share a workspace. The repository's
[CI](https://github.com/clearpathrobotics/clearpath_community_demos/blob/main/.github/workflows/ros2-build.yml)
follows the same pattern, building each demo in its matrix in a separate
workspace.

The convention used throughout this site is to create one workspace per demo
at `~/<demo_name>_ws/`, clone this repository into its `src/` directory, and
build only that demo:

```bash
mkdir -p ~/<demo_name>_ws/src
cd ~/<demo_name>_ws/src
git clone https://github.com/clearpathrobotics/clearpath_community_demos.git

cd ~/<demo_name>_ws
rosdep install \
    --from-paths src/clearpath_community_demos/demos/<demo_name> \
    --ignore-src -r -y
colcon build --symlink-install --packages-up-to <demo_name>
source install/setup.bash
```

The exact commands (with the demo name filled in) live on each demo's own
page under **Build**.

## Demos with extra source dependencies

If a demo needs source repositories beyond this one (for example, an
unreleased fork or a sibling repo), it ships a
[`vcstool`](https://github.com/dirk-thomas/vcstool) `.repos` file at
`demos/<demo_name>/<demo_name>.repos`. In that case the demo's own page
includes an additional `vcs import` step before `rosdep install`. Most demos
do not need one.

## Next: run your first demo

Start with [Hello Clearpath](../demos_docs/hello_clearpath.md), a minimal demo
that drives the robot in a small square. It confirms that your setup works,
natively or with Docker, before you try the larger demos.

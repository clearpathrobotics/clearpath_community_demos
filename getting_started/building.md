---
sort: 2
---

# Workspaces

Each community demo is built in its own dedicated colcon workspace.
Community demos may have unrelated — and sometimes conflicting —
dependencies, so they are not intended to share a workspace. The CI for this
repository follows the same pattern: every demo is built in isolation.

Every demo ships a [`vcstool`](https://github.com/dirk-thomas/vcstool)
`.repos` file at `demos/<demo_name>/<demo_name>.repos`. This file is the
single source of truth for the demo's source-level dependencies (this
repository, plus any forks or unreleased packages the demo needs).

The build steps for every demo follow the same shape:

1. Create `~/<demo_name>_ws/src/`.
2. `vcs import src < <demo_name>.repos` to populate it.
3. `rosdep install --from-paths src --ignore-src -r -y`.
4. `colcon build --symlink-install`.

The exact commands (with the right URLs filled in) live on each demo's own
page under **Build**.

## Prerequisite tools

```bash
sudo apt install -y python3-vcstool
```

(`git`, `colcon`, and `rosdep` are covered in
[Prerequisites](prerequisites.md).)

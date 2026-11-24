---
sort: 4
---

# Contributing

The Clearpath Community Demos repository is community-driven — we welcome new
demos, improvements, bug fixes, and documentation updates from anyone using a
Clearpath platform.

To report a bug or suggest a demo, open an
[issue](https://github.com/clearpathrobotics/clearpath_community_demos/issues/new/choose).
For a fix or improvement to an existing demo, open a pull request against
`main`.

## How to contribute a new demo

Use [`hello_clearpath`](https://github.com/clearpathrobotics/clearpath_community_demos/tree/main/demos/hello_clearpath)
as a template: it is a minimal, complete example of every item below. In the
steps, `<demo_name>` is your demo's directory and ROS 2 package name; CI
builds the package with that name, so keep the two the same.

1. **Fork** the [repository](https://github.com/clearpathrobotics/clearpath_community_demos)
   and create a branch.
2. **Add the source** under `demos/<demo_name>/` as a self-contained ROS 2
   package (or set of packages). Don't depend on other demos.
3. **Include an example `robot.yaml`** at `demos/<demo_name>/config/robot.yaml`:
   a working
   [`clearpath_config`](https://docs.clearpathrobotics.com/docs/ros/config/yaml/overview/)
   file describing the platform, sensors, and any payloads the demo was tested
   against. Reviewers and other users need it to reproduce your setup. Document
   any parts that must be edited (serial numbers, IPs, namespaces) in a comment
   at the top of the file.
4. **List extra source repositories**, if the demo needs any (for example, an
   unreleased fork), in a [`vcstool`](https://github.com/dirk-thomas/vcstool)
   file at `demos/<demo_name>/<demo_name>.repos`. CI imports it before
   installing dependencies.
5. **Add tests** that run with `colcon test`: `pytest` tests for Python code,
   and `ament_lint_auto` (plus `gtest` where useful) for C++ packages. CI runs
   them on every pull request.
6. **Add the demo to CI**: add `<demo_name>` to the `demo` matrix in
   [`.github/workflows/ros2-build.yml`](https://github.com/clearpathrobotics/clearpath_community_demos/blob/main/.github/workflows/ros2-build.yml),
   which builds and tests each demo in its own workspace.
7. **Write the documentation page** at `demos_docs/<demo_name>.md`, following
   the existing demo pages. Start it with front matter whose `sort` value is the
   next number after the existing demos, which sets its position in the site's
   menu:

   ```markdown
   ---
   sort: 4
   ---

   # My Demo
   ```

   Include a short description, the supported platform(s), prerequisites, build
   and run instructions, what to expect, and a link to the example
   `robot.yaml` with any required edits.
8. **Point the demo's `README.md` at that page.** The documentation page is the
   single source of instructions, so keep `demos/<demo_name>/README.md` to a
   short description and a link to the page, as `hello_clearpath` does.
9. **List the demo** in the layout in [`demos/README.md`](https://github.com/clearpathrobotics/clearpath_community_demos/blob/main/demos/README.md).
10. **Optionally, add a Docker Compose stack** so the demo runs without a ROS
    installation. Build it on the
    [clearpath_docker](https://github.com/clearpathrobotics/clearpath_docker)
    images as `hello_clearpath` and `auto_explore_clearpath` do: their
    `docker-compose.yml` files show the simulator, Nav2, and RViz services, the
    `setup_init` service that checks `robot.yaml`, and the demo image, whose
    entrypoint loads the ROS settings from `robot.yaml`. To publish the demo's
    image to GHCR, add `<demo_name>` to the `demo` matrix and the `paths` filters in
    [`.github/workflows/demo-images.yml`](https://github.com/clearpathrobotics/clearpath_community_demos/blob/main/.github/workflows/demo-images.yml);
    it builds the image on pull requests and pushes it as
    `jazzy-<demo_name>-latest` on `main`.
11. **Open a pull request** against `main`. The pull request template has a
    checklist of these steps.

## Local docs development

The site is served under `/clearpath_community_demos/`, as on GitHub Pages, so
open <http://localhost:4000/clearpath_community_demos/> once it is running. It
rebuilds whenever you save a file. Use whichever setup suits you:

- **Dev Container (VS Code):** the repository ships a
  [Dev Container](https://containers.dev/) with Ruby 3.2 that installs the gems
  and forwards port 4000. It needs [Docker](https://docs.docker.com/get-docker/)
  and the
  [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).
  Open the repository in VS Code, choose **Reopen in Container** (or run
  **Dev Containers: Reopen in Container** from the Command Palette), and once
  `bundle install` has finished, run:

  ```bash
  bundle exec jekyll serve --livereload
  ```

- **Ruby on the host:** with Ruby 3.2 installed, from the repository root:

  ```bash
  make           # install bundler and the gems
  make server    # build and serve the site
  ```

## Code style

This repository uses [pre-commit](https://pre-commit.com/) to run style and
lint checks both locally and in CI. Install the hooks before committing:

```bash
python3 -m venv venv
. venv/bin/activate
pip install pre-commit
pre-commit install            # in the top-level dir of the repo
```

The configured hooks include formatters for each language:

- **Python** — [`ruff`](https://docs.astral.sh/ruff/) for linting and
  formatting (config in [`.ruff.toml`](https://github.com/clearpathrobotics/clearpath_community_demos/blob/main/.ruff.toml)).
- **C / C++** — `clang-format` (config in
  [`.clang-format`](https://github.com/clearpathrobotics/clearpath_community_demos/blob/main/.clang-format)).

The code follows ROS 2 style: these configurations produce code that also
passes the ROS 2 linters that `ament_lint_auto` runs with `colcon test`
(`uncrustify`, `cpplint`, `flake8`, and others), which CI runs for each demo.
Demos using C++ should use `ament_cmake` and enable `ament_lint_auto` in their
`CMakeLists.txt`, mirroring the
[`hello_clearpath`](https://github.com/clearpathrobotics/clearpath_community_demos/tree/main/demos/hello_clearpath)
example, and include their packages' headers with quotes
(`#include "rclcpp/rclcpp.hpp"`). Each source file starts with the Apache 2.0
license header that `hello_clearpath`'s files use.

The other hooks:

- **Spell checking** — [`cspell`](https://cspell.org/); add new project-specific
  words to [`.cspell.json`](https://github.com/clearpathrobotics/clearpath_community_demos/blob/main/.cspell.json)
  when needed.
- **GitHub Actions** — `actionlint` validates the workflow files.
- **Generic** — trailing whitespace, end-of-file newlines, merge-conflict
  markers, leaked credentials, and similar checks.

Other guidelines:

- Follow the [ROS 2 Developer Guide](https://docs.ros.org/en/rolling/The-ROS2-Project/Contributing/Developer-Guide.html)
  conventions.
- Use `ament_cmake` for C++ and mixed C++/Python packages (adding
  `ament_cmake_python` for Python modules, as `hello_clearpath` does), and
  `ament_cmake` or `ament_python` for pure Python packages. Keep packages
  self-contained — avoid cross-dependencies between demos.
- Pin or document the ROS 2 distribution(s) and Clearpath software version(s)
  you tested against.

## License

By contributing, you agree that your contributions will be licensed under the
[Apache License 2.0](https://github.com/clearpathrobotics/clearpath_community_demos/blob/main/LICENSES/Apache2)
that covers this repository.

## Disclaimer

Demos in this repository are provided as-is by the community. They are not
officially supported by Clearpath Robotics, by Rockwell Automation. Always
review code before running it on hardware, and be mindful of safety when
operating real robots.

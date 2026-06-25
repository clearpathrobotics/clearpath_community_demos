---
sort: 5
---

# Contributing

The Clearpath Community Demos repository is community-driven — we welcome new
demos, improvements, bug fixes, and documentation updates from anyone using a
Clearpath platform.

## How to contribute a new demo

1. **Fork** the [repository](https://github.com/clearpathrobotics/clearpath_community_demos).
2. Add your demo source code under `demos/<your_demo_name>/` as a self-contained
   ROS 2 package (or set of packages).
3. **Include an example `robot.yaml`** — provide a working Clearpath robot
   configuration that the demo was tested against under
   `demos/<your_demo_name>/config/robot.yaml`. This is the
   [`clearpath_config`](https://docs.clearpathrobotics.com/docs/ros/config/yaml/overview/)
   file describing the platform, sensors, and any payloads the demo expects.
   Reviewers and other users need this to reproduce your setup. Document any
   parts that must be edited (serial numbers, IPs, namespaces) in a comment
   at the top of the file.
4. Add a documentation page under `demos_docs/<your_demo_name>.md` following the
   pattern of the existing demos. Include:
   - A short description.
   - Supported platform(s).
   - Prerequisites.
   - How to launch and what to expect.
   - A link to the example `robot.yaml` and any required edits.
5. Open a **pull request** against `main`.

## Local docs development

The repository ships a [Dev Container](https://containers.dev/) configured for
editing and previewing the Jekyll documentation site. It uses a Ruby 3.2
image, installs all gem dependencies automatically on creation, and forwards
port 4000 so you can view the site in your browser.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (or a compatible runtime)
- [VS Code](https://code.visualstudio.com/) with the
  [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Steps

1. Open the repository root in VS Code.
2. When prompted **"Reopen in Container"**, click it — or open the Command
   Palette (`Ctrl+Shift+P`) and run **Dev Containers: Reopen in Container**.
3. VS Code builds the container image and runs `bundle install` automatically.
   This may take a minute on the first launch; subsequent opens are instant.
4. Once inside the container, start the Jekyll server:

   ```bash
   bundle exec jekyll serve --livereload
   ```

5. Open [http://localhost:4000](http://localhost:4000) in your browser (VS Code
   also shows a notification with the forwarded URL).

The site hot-reloads whenever you save a Markdown or layout file.

## Code style

This repository uses [pre-commit](https://pre-commit.com/) to run style and
lint checks both locally and in CI. Install the hooks before committing:

```bash
python3 -m venv venv
. venv/bin/activate
pip install pre-commit
pre-commit install            # in the top-level dir of the repo
```

The configured hooks include:

- **Python** — [`ruff`](https://docs.astral.sh/ruff/) for linting and
  formatting (config in [`.ruff.toml`](https://github.com/clearpathrobotics/clearpath_community_demos/blob/main/.ruff.toml)).
- **C / C++** — `clang-format` (config in
  [`.clang-format`](https://github.com/clearpathrobotics/clearpath_community_demos/blob/main/.clang-format)).
  Demos using C++ should use `ament_cmake` and enable `ament_lint_auto` in
  their `CMakeLists.txt`, mirroring the
  [`hello_clearpath`](https://github.com/clearpathrobotics/clearpath_community_demos/tree/main/demos/hello_clearpath)
  example.
- **Spell checking** — [`cspell`](https://cspell.org/); add new project-specific
  words to [`.cspell.json`](https://github.com/clearpathrobotics/clearpath_community_demos/blob/main/.cspell.json)
  when needed.
- **GitHub Actions** — `actionlint` validates the workflow files.
- **Generic** — trailing whitespace, end-of-file newlines, merge-conflict
  markers, leaked credentials, and similar checks.

Other guidelines:

- Follow the [ROS 2 Developer Guide](https://docs.ros.org/en/rolling/The-ROS2-Project/Contributing/Developer-Guide.html)
  conventions.
- Python demos use `ament_python`; C++ demos use `ament_cmake`. Keep packages
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

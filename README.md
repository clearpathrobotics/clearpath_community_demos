# Clearpath Community Demos

A community-maintained collection of demos, examples, and tutorials for
[Clearpath Robotics, by Rockwell Automation](https://clearpathrobotics.com)
platforms.

This repository hosts both:

- **Source code** for each demo, under [`demos/`](demos/), as self-contained
  ROS 2 packages.
- A **documentation site** built with Jekyll, served via GitHub Pages at
  <https://clearpathrobotics.github.io/clearpath_community_demos/>.

> Demos in this repository are contributed by the community and are **not
> officially supported** by Clearpath Robotics, by Rockwell Automation. They
> are provided as-is to help users get started and share what they have built.

> ## ⚠️ Use at your own risk
>
> The code in this repository can drive real robots. It has **not** been
> reviewed, tested, or certified by Clearpath Robotics, by Rockwell
> Automation, and comes with **no warranty of any kind** (see the
> [LICENSE](LICENSE)). You are solely responsible for any consequences of
> running it — including damage to property, injury to people, or harm to
> your robot. Always:
>
> - Review the code before running it.
> - Test in simulation first.
> - Keep a clear path and a working e-stop within reach when running on
>   hardware.
> - Confirm the demo supports your platform and software version.

## Repository layout

```
.
├── demos/                # ROS 2 source code for each community demo
├── overview/             # Docs: project overview
├── getting_started/      # Docs: prerequisites, building, running
├── demos_docs/           # Docs: one page per demo
├── tutorials/            # Docs: longer walkthroughs
├── contributing/         # Docs: how to contribute
├── media/                # Docs: images and figures
├── _config.yml           # Jekyll site configuration
├── Gemfile               # Jekyll/GitHub Pages dependencies
└── Makefile              # Convenience targets for local docs preview
```

Both the docs and the source code live on `main` so a single PR can update a
demo and its documentation together.

## Building the demos

See [Building the Demos](getting_started/building.md). In short:

```bash
mkdir -p ~/community_ws/src
cd ~/community_ws/src
git clone https://github.com/clearpathrobotics/clearpath_community_demos.git
cd ~/community_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```

## Building the docs site locally

The site uses the [`clearpathrobotics/jekyll-rtd-theme`](https://github.com/clearpathrobotics/jekyll-rtd-theme)
remote theme so it matches the Clearpath Robotics, by Rockwell Automation
branding used by the rest of the Clearpath documentation.

Install Ruby 3.2, then:

```bash
make           # install bundler and gems
make server    # serve at http://127.0.0.1:4000/clearpath_community_demos
```

## Contributing

Contributions are welcome — please see the
[Contributing](contributing/README.md) page for guidelines on adding a new
demo or improving an existing one.

## License

[Apache License 2.0](LICENSE).

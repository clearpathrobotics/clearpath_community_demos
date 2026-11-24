## Description

<!-- What does this change, and why? Link any related issue. -->

## Testing

<!-- How did you test it? Include the platform (real or simulated), ROS 2
distribution, and Clearpath software version. -->

## New demo checklist

<!-- For a new demo, check off each step in the Contributing guide. Delete this
section otherwise. -->

- [ ] Source in `demos/<demo_name>/`, with the package named `<demo_name>`
- [ ] Example `config/robot.yaml`, with the parts to edit documented
- [ ] `demos/<demo_name>/<demo_name>.repos` for any extra source repositories
- [ ] Tests that run with `colcon test`
- [ ] Demo added to the `demo` matrix in `.github/workflows/ros2-build.yml`
- [ ] `demos_docs/<demo_name>.md`, with the next `sort` number in its front matter
- [ ] `demos/<demo_name>/README.md` links to the documentation page
- [ ] Demo listed in `demos/README.md`
- [ ] `pre-commit run --all-files` passes

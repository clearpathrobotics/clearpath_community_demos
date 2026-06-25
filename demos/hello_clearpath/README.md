# hello_clearpath

A minimal "hello world" community demo for Clearpath platforms. Drives the
robot in a 1 m × 1 m square. The package ships **two interchangeable
implementations** — one in C++ (`hello_square_cpp`) and one in Python
(`hello_square_py`) — to serve as starting templates for new demos in either
language.

See [demos_docs/hello_clearpath.md](../../demos_docs/hello_clearpath.md) for
documentation and run instructions.

## Docker Compose (Jazzy: sim + viz + demo or robot + demo)

This demo includes `docker-compose.yml` with two profiles:

- `sim`: `sim` + `viz` + `hello_clearpath`
- `robot`: `hello_clearpath_robot` (expects robot stack already running on host)

Prerequisites:

- Install Docker on the Linux host machine before using either profile.
- For `sim`, `viz`, and demo, Docker must be available on the host.
- For `robot` and demo, Docker must be available on the host.

Safety warning (`robot` profile):

- This mode can command a physical robot. Ensure an E-stop is available, the area is clear, and the robot is safely supported before launching.

From `demos/hello_clearpath/`:

```bash
xhost +local:
docker compose --profile sim up
```

For robot + demo:

```bash
docker compose --profile robot up
```

By default, the stack creates and uses a writable
`demos/hello_clearpath/config/.setup_path/` directory, auto-seeded from
`config/robot.yaml`.

For the `robot` profile, the stack uses `/etc/clearpath/robot.yaml` on the
Linux host by default.

To override the robot configuration, point `SETUP_PATH_HOST` at a different
host setup directory that contains `robot.yaml`:

```bash
SETUP_PATH_HOST=/path/to/clearpath_setup docker compose up
```

If you use profiles, apply the same override command with the profile flag:

```bash
SETUP_PATH_HOST=/path/to/clearpath_setup docker compose --profile sim up
ROBOT_SETUP_PATH_HOST=/path/to/clearpath_setup docker compose --profile robot up
```

By default, `hello_clearpath` services use the published GHCR image:

- `ghcr.io/clearpathrobotics/clearpath_community_demos:jazzy-hello_clearpath-latest`

The hello_clearpath container image also ships with a default config at
`/etc/clearpath/robot.yaml` (copied from `config/robot.yaml` at build time),
so it is usable out-of-the-box. You can still override it by bind-mounting a
host setup directory and setting `SETUP_PATH` accordingly.

The entrypoint waits for simulation readiness by default before launching the
demo command. To tune this behavior:

- `WAIT_FOR_SIM=true|false` (default: `true`)
- `WAIT_FOR_TIMEOUT_SEC=<seconds>` (default: `60`)

## GitHub Image Build

This repo includes a GitHub Actions workflow that builds the hello image from
`demos/hello_clearpath/Dockerfile`:

- Pull requests: build validation only (no push)
- Pushes to `main`: build and push to GHCR

Published tags:

- `ghcr.io/clearpathrobotics/clearpath_community_demos:jazzy-hello_clearpath-latest`

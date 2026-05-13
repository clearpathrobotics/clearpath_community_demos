# TODO: Investigate creating a standardized developer image

# This image is the official MoveIt 2 jazzy image with some added fixes on top:
# See the following pull requests for details:
# - https://github.com/moveit/moveit2/pull/3702
# - https://github.com/moveit/moveit2/pull/3704

FROM  ghcr.io/clearpathrobotics/moveit2:jazzy-source AS moveit_source_build

# Build ros2_controllers from source (tag 4.40.0)
FROM docker.io/osrf/ros:jazzy-desktop AS ros2_controllers_source_build
RUN set -xe; \
    apt-get update; \
    apt-get install -y python3-colcon-common-extensions python3-rosdep python3-vcstool; \
    mkdir -p /root/ros2_control_ws/src; \
    cd /root/ros2_control_ws/src; \
    git clone --branch 4.40.0 --depth 1 https://github.com/ros-controls/ros2_controllers.git; \
    vcs import --input ros2_controllers/ros2_controllers.jazzy.repos; \
    cd /root/ros2_control_ws; \
    rosdep update; \
    rosdep install --from-paths src --ignore-src -r -y; \
    . /opt/ros/${ROS_DISTRO}/setup.sh; \
    colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release; \
    # Preserve package.xml files for dependency installation in the final image
    mkdir -p /root/ros2_control_ws/package_xmls && \
    cd src && find . -name package.xml | xargs -I{} cp --parents {} /root/ros2_control_ws/package_xmls/

# Base ROS image
FROM docker.io/osrf/ros:jazzy-desktop

# Copy the MoveIt install from the MoveIt source build image to our image
COPY --from=moveit_source_build /root/ws_moveit/install /workspaces/moveit_ws/install

# Copy the ros2_controllers install from the source build stage
COPY --from=ros2_controllers_source_build /root/ros2_control_ws/install /workspaces/ros2_controllers_ws/install

# Copy ros2_controllers package.xml files and install their runtime dependencies
COPY --from=ros2_controllers_source_build /root/ros2_control_ws/package_xmls /tmp/ros2_controllers_package_xmls

# Set ROS_VERSION ARG again because it's required after FROM
# It defaults to jazzy, but can be overridden by setting the build arg to other ROS 2 distributions
ARG ROS_VERSION=jazzy

# Set the ROS_VERSION ARG to an environment variable
ENV ROS_DISTRO=jazzy

# Prevent ROS from doing automatic discovery over the network
ENV ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST

# Declare and default the WORKSPACE ARG to the ROS workspace directory
ARG WORKSPACE=/workspaces/mobile_manipulation

# Declare and default the USERNAME ARG to the username of the container user
ARG USERNAME=administrator

# Create a non-root user
RUN set -xe; \
    adduser --gecos "" --disabled-password $USERNAME; \
    usermod -a -G sudo $USERNAME; \
    usermod -a -G video $USERNAME; \
    echo "%sudo ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/sudoers;

# Install other ROS dependencies
RUN set -xe; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    # ROS 2 control dependencies from the copied package XML files
    rosdep update; \
    rosdep install --from-paths /tmp/ros2_controllers_package_xmls --ignore-src -r -y; \
    rm -rf /tmp/ros2_controllers_package_xmls; \
    # Other dependencies
    apt-get install -y \
        # Install MoveIt run dependencies
        freeglut3-dev \
        libfcl0.7 \
        ros-${ROS_DISTRO}-ament-cmake-google-benchmark \
        ros-${ROS_DISTRO}-chomp-motion-planner \
        ros-${ROS_DISTRO}-controller-manager-msgs \
        ros-${ROS_DISTRO}-eigen-stl-containers \
        ros-${ROS_DISTRO}-object-recognition-msgs \
        ros-${ROS_DISTRO}-octomap-msgs \
        ros-${ROS_DISTRO}-ompl \
        ros-${ROS_DISTRO}-ros-testing \
        ros-${ROS_DISTRO}-stomp \
        ros-${ROS_DISTRO}-warehouse-ros \
        ros-${ROS_DISTRO}-warehouse-ros-sqlite \
        # ROS packages
        ros-${ROS_DISTRO}-generate-parameter-library \
        ros-${ROS_DISTRO}-graph-msgs \
        ros-${ROS_DISTRO}-joint-state-publisher-gui \
        ros-${ROS_DISTRO}-moveit-visual-tools \
        ros-${ROS_DISTRO}-py-binding-tools \
        ros-${ROS_DISTRO}-rviz-visual-tools \
        ros-${ROS_DISTRO}-tf-transformations \
        ros-${ROS_DISTRO}-trac-ik \
        ros-${ROS_DISTRO}-trajectory-msgs \
        ros-${ROS_DISTRO}-visualization-msgs \
        ros-${ROS_DISTRO}-pinocchio \
        # Doosan dependency
        libpoco-dev \
        # Robot
        ros-${ROS_DISTRO}-clearpath-platform-description \
    ; \
    # Clean apt cache to reduce image size
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*;

# Install development tools
RUN set -xe; \
    # apt-get update must be repeated because the apt cache was cleaned in the previous step
    apt-get update; \
    apt-get install -y \
        ccache \
        clangd \
        clang-tidy \
        clang-tools \
        clang-format-18 \
        gdb \
        less \
        mesa-utils \
        nano \
        pcl-tools \
        python3-pip \
        python3-venv \
        wget \
        xdg-utils \
    ; \
    echo "export CONTAINER_WORKSPACE_FOLDER=${WORKSPACE}" > /etc/default/container-workspace-folder; \
    echo "export ROS_DISTRO=${ROS_DISTRO}" >> /etc/default/ros-distro; \
    chsh -s /bin/bash $USERNAME; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*;

# Create a venv and install pip dependencies
RUN python3 -m venv --system-site-packages /venv; \
    . /venv/bin/activate; \
    pip install --no-cache-dir \
      black \
      meshcat \
      meshcat-shapes \
      pandas \
      pymeshlab \
      "scipy>=1.11.4" \
      pin-pink \
      "pyglet<2" \
      "qpsolvers[quadprog]" \
      qtqp \
      robot_descriptions \
      "numpy<2" \
      yourdfpy;

# Use venv by default
ENV VIRTUAL_ENV=/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy the ROS activation script into the profile.d directory so it gets sourced on shell startup
COPY ros-activate.sh /etc/profile.d/ros-activate.sh

# Set the USERNAME to an environment variable. This is used by the entrypoint script.
ENV USERNAME=$USERNAME

# Copy the entrypoint script and configure it as the entrypoint
COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

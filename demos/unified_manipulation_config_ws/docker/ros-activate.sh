source /etc/default/container-workspace-folder
source /etc/default/ros-distro

cd $CONTAINER_WORKSPACE_FOLDER

for setup in \
  /opt/ros/$ROS_DISTRO/setup.bash \
  /workspaces/moveit_ws/install/setup.bash \
  /workspaces/ros2_controllers_ws/install/setup.bash \
  $CONTAINER_WORKSPACE_FOLDER/install/setup.bash
do
  if [ -f "$setup" ]; then
    . "$setup"
  fi
done

export PATH=/usr/lib/ccache:${PATH}
export RCUTILS_COLORIZED_OUTPUT=1

# Set the bash history file to a location inside the workspace so that it can be persisted
export HISTFILE=$CONTAINER_WORKSPACE_FOLDER/docker/histfile
export PROMPT_COMMAND='history -a'
export HISTSIZE=100000
export HISTFILESIZE=200000
export HISTTIMEFORMAT="%d/%m/%y %T "

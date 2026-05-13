#!/bin/bash

# TODO: Investigate creating a standardized developer image

username=$USERNAME

create_user_if_necessary() {
  # 24.04 image has a default user Ubuntu that may conflict with the container user, delete it
  if id ubuntu >/dev/null 2>&1; then
    deluser ubuntu
    rm -rf /home/ubuntu
  fi

  # Create a user in the entrypoint with matching UID and GID as the host user
  # The custom start script will pass in the host UID and GID
  # This is done in the entrypoint to avoid users needing to build the Docker image during the workshop
  if ! getent passwd $username >/dev/null 2>/dev/null; then
    echo "Creating user $username with $HOST_UID:$HOST_GID..."

    addgroup --gid $HOST_GID $username
    adduser --gid $HOST_GID --uid $HOST_UID --gecos "" --disabled-password $username

    usermod -a -G sudo $username
    usermod -a -G video $username

    echo "%sudo ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/sudoers;
  else
    # In Docker Compose, the container user exists, but the container UID and GID may not match host user UID and GID
    # Not necessary for Dev container case as VSCode handles this for us
    if [ -n $DEVCONTAINER != "true" ]; then
      # Do what VSCode does: https://github.com/devcontainers/cli/blob/721c21b8fba699679cc03c01baa782e816be6f54/scripts/updateUID.Dockerfile
      fix_uid_gid
    fi
  fi
}

# The following function is adapted from devcontainers/cli.
# Licensed under the MIT License.
# See: LICENSES/MIT-devcontainers-cli
fix_uid_gid(){
  eval $(sed -n "s/${username}:[^:]*:\([^:]*\):\([^:]*\):[^:]*:\([^:]*\).*/OLD_UID=\1;OLD_GID=\2;HOME_FOLDER=\3/p" /etc/passwd)
  eval $(sed -n "s/\([^:]*\):[^:]*:${HOST_UID}:.*/EXISTING_USER=\1/p" /etc/passwd)
  eval $(sed -n "s/\([^:]*\):[^:]*:${HOST_GID}:.*/EXISTING_GROUP=\1/p" /etc/group)
  if [ -z "$OLD_UID" ]; then
    echo "Remote user not found in /etc/passwd ($username)."
  elif [ "$OLD_UID" = "$HOST_UID" -a "$OLD_GID" = "$HOST_GID" ]; then
    echo "UIDs and GIDs are the same ($HOST_UID:$HOST_GID)."
  elif [ "$OLD_UID" != "$HOST_UID" -a -n "$EXISTING_USER" ]; then
    echo "User with UID exists ($EXISTING_USER=$HOST_UID)."
  else \
    if [ "$OLD_GID" != "$HOST_GID" -a -n "$EXISTING_GROUP" ]; then
      echo "Group with GID exists ($EXISTING_GROUP=$HOST_GID)."
      HOST_GID="$OLD_GID"
    fi
    echo "Updating UID:GID from $OLD_UID:$OLD_GID to $HOST_UID:$HOST_GID.";
    sed -i -e "s/\(${username}:[^:]*:\)[^:]*:[^:]*/\1${HOST_UID}:${HOST_GID}/" /etc/passwd;
    if [ "$OLD_GID" != "$HOST_GID" ]; then
      sed -i -e "s/\([^:]*:[^:]*:\)${OLD_GID}:/\1${HOST_GID}:/" /etc/group;
    fi
    chown -R $HOST_UID:$HOST_GID $HOME_FOLDER
  fi
}


# Need to fix user permissions to have access to the proper rendering for gazebo
# https://github.com/linuxserver/docker-plex/blob/b01cd52/root/etc/cont-init.d/50-gid-video
# They have a root clause that I'm not going to worry about. See:
# https://github.com/linuxserver/docker-plex/pull/208#issuecomment-532948347
fix_dri_permissions() {
  local files=$(find /dev/dri -type c -print 2>/dev/null)

  for file in $files; do
    local gid=$(stat -c '%g' $file)
    echo -n "$file has group of $gid... "
    if id -G | grep -q "$gid"; then
      echo "and is already a part of user $username"
    else
      local gname=$(getent group "$gid" | awk -F: '{print $1}')
      if [ -z "$gname" ]; then
        gname="video${gid}"
        groupadd "$gname"
        groupmod -g "$gid" "$gname"
      fi

      usermod -a -G "$gname" $username
      echo "and is added to part of $username"
    fi
  done
}

set -xe
create_user_if_necessary
fix_dri_permissions

# Sleep forever to keep the container running
exec sleep infinity

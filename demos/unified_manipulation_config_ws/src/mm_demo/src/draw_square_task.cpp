// Copyright (c) 2026, Rockwell Automation Technologies, Inc., and community contributors.
// Licensed under the Apache License, Version 2.0.

#include "mm_demo/draw_square_task.hpp"

#include <moveit/task_constructor/solvers.h>
#include <moveit/task_constructor/stages.h>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <moveit_msgs/msg/collision_object.hpp>
#include <rclcpp/logging.hpp>

#include "mm_demo/draw_square_params.hpp"

#include <cmath>
#include <string>

namespace mm_demo
{
namespace
{
const auto & logger = rclcpp::get_logger("write_letters_task");
}

namespace mtc = moveit::task_constructor;

DrawSquareTask::DrawSquareTask(const rclcpp::Node::SharedPtr & node, const std::string & name)
: TaskBase(node, name)
{
}

bool DrawSquareTask::init()
{
  task_.stages()->setName(task_name_);
  task_.loadRobotModel(node_);

  const draw_square::ParamListener param_listener(node_);
  const auto params = param_listener.get_params();
  const auto fraction = params.fraction;
  const auto size = params.size;
  const auto z_diff = params.z_diff;

  const auto sampling_planner = std::make_shared<mtc::solvers::PipelinePlanner>(node_);
  const auto cartesian_planner = std::make_shared<mtc::solvers::CartesianPath>();
  cartesian_planner->setMaxVelocityScalingFactor(1.0);
  cartesian_planner->setMaxAccelerationScalingFactor(1.0);
  cartesian_planner->setStepSize(.03);
  cartesian_planner->setMinFraction(fraction);

  const auto x_diff = std::sqrt(std::pow(size, 2) - std::pow(z_diff, 2));

  task_.setProperty("group", group_);

  {
    auto current_state = std::make_unique<mtc::stages::CurrentState>("current state");
    task_.add(std::move(current_state));
  }
  {
    auto stage = std::make_unique<mtc::stages::MoveTo>("start", sampling_planner);
    stage->setGroup(group_);
    geometry_msgs::msg::PoseStamped start_pose;
    start_pose.header.frame_id = "odom";
    start_pose.pose.position.x = -size / 2;
    start_pose.pose.position.y = -size / 2;
    start_pose.pose.position.z = 0.5;
    // Hardcoded orientation for now, but could be parameterized if needed
    start_pose.pose.orientation.x = M_SQRT1_2;
    start_pose.pose.orientation.y = 0.0;
    start_pose.pose.orientation.z = M_SQRT1_2;
    start_pose.pose.orientation.w = 0.0;
    stage->setGoal(start_pose);
    task_.add(std::move(stage));
  }

  {
    auto stage = std::make_unique<mtc::stages::MoveRelative>("Move +X", cartesian_planner);
    stage->setGroup(group_);
    geometry_msgs::msg::Vector3Stamped direction;
    direction.header.frame_id = "odom";
    direction.vector.x = x_diff;
    direction.vector.z = z_diff;
    stage->setDirection(direction);
    task_.add(std::move(stage));
  }

  {
    auto stage = std::make_unique<mtc::stages::MoveRelative>("Move +Y", cartesian_planner);
    stage->setGroup(group_);
    geometry_msgs::msg::Vector3Stamped direction;
    direction.header.frame_id = "odom";
    direction.vector.y = size;
    stage->setDirection(direction);
    task_.add(std::move(stage));
  }

  {
    auto stage = std::make_unique<mtc::stages::MoveRelative>("Move -X", cartesian_planner);
    stage->setGroup(group_);
    geometry_msgs::msg::Vector3Stamped direction;
    direction.header.frame_id = "odom";
    direction.vector.x = -x_diff;
    direction.vector.z = -z_diff;
    stage->setDirection(direction);
    task_.add(std::move(stage));
  }

  {
    auto stage = std::make_unique<mtc::stages::MoveRelative>("Move -Y", cartesian_planner);
    stage->setGroup(group_);
    geometry_msgs::msg::Vector3Stamped direction;
    direction.header.frame_id = "odom";
    direction.vector.y = -size;
    stage->setDirection(direction);
    task_.add(std::move(stage));
  }
  task_.init();

  return true;
}

}  // namespace mm_demo

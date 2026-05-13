// Copyright (c) 2026, Rockwell Automation Technologies, Inc., and community contributors.
// Licensed under the Apache License, Version 2.0.

#include "mm_demo/task_base.hpp"

#include <rclcpp/logging.hpp>

namespace mm_demo
{
namespace
{
const auto & logger = rclcpp::get_logger("mtc_task");
}

TaskBase::TaskBase(const rclcpp::Node::SharedPtr & node, const std::string & name)
: node_(node), task_name_(name)
{
  param_listener_ = std::make_shared<task_base::ParamListener>(node_);
  params_ = param_listener_->get_params();
  group_ = params_.group_name;
  num_retries_ = params_.num_retries;
}

bool TaskBase::plan(const std::size_t max_solutions)
{
  auto success = false;
  for (std::size_t i = 0; i < num_retries_ && !success; ++i)
  {
    RCLCPP_INFO_STREAM(logger, "Planning attempt " << i + 1 << " of " << num_retries_);
    if (static_cast<bool>(task_.plan(max_solutions)))
    {
      RCLCPP_INFO_STREAM(logger, "Planning successful");
      success = true;
    }
  }
  if (success)
  {
    task_.introspection().publishSolution(*task_.solutions().front());
  }
  return success;
}

bool TaskBase::execute()
{
  if (task_.solutions().empty() || task_.solutions().front() == nullptr)
  {
    RCLCPP_ERROR_STREAM(logger, "No planned solutions to execute");
    return false;
  }
  auto result = task_.execute(*task_.solutions().front());
  if (result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS)
  {
    RCLCPP_ERROR_STREAM(logger, "Task execution failed: " << result.val);
    return false;
  }
  return true;
}

std::optional<moveit_task_constructor_msgs::msg::Solution> TaskBase::getPlannedSolution() const
{
  if (task_.solutions().empty() || task_.solutions().front() == nullptr)
  {
    RCLCPP_ERROR_STREAM(logger, "No planned solutions available");
    return std::nullopt;
  }
  moveit_task_constructor_msgs::msg::Solution solution;
  task_.solutions().front()->toMsg(solution);
  return solution;
}

const moveit::core::JointModelGroup * TaskBase::getJointModelGroup() const
{
  const auto * jmg = task_.getRobotModel()->getJointModelGroup(group_);
  if (!jmg)
  {
    RCLCPP_ERROR_STREAM(logger, "Joint model group '" << group_ << "' not found in robot model");
  }
  return jmg;
}
}  // namespace mm_demo

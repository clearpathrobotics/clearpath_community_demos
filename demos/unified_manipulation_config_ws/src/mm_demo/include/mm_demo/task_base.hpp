// Copyright (c) 2026, Rockwell Automation Technologies, Inc., and community contributors.
// Licensed under the Apache License, Version 2.0.

#pragma once

#include <moveit/task_constructor/task.h>
#include <moveit_task_constructor_msgs/msg/solution.h>
#include <rclcpp/node.hpp>
#include "mm_demo/base_params.hpp"

#include <optional>
#include <string>
namespace mm_demo
{
class TaskBase
{
public:
  TaskBase(const rclcpp::Node::SharedPtr & node, const std::string & name);

  virtual bool init() = 0;

  bool plan(const std::size_t max_solutions = 1);

  bool execute();

  // Retrieve the planned solution as a message for visualization or other purposes
  std::optional<moveit_task_constructor_msgs::msg::Solution> getPlannedSolution() const;

  // Get the joint model group used in the task, needed for visualization
  const moveit::core::JointModelGroup * getJointModelGroup() const;

protected:
  rclcpp::Node::SharedPtr node_;
  moveit::task_constructor::Task task_;
  task_base::Params params_;
  std::shared_ptr<task_base::ParamListener> param_listener_;

  std::string group_;        // The name of the joint model group to use for planning
  std::string task_name_;    // The name of the MTC task
  std::size_t num_retries_;  // Number of planning attempts before giving up
};
}  // namespace mm_demo

// Copyright (c) 2026, Rockwell Automation Technologies, Inc., and community contributors.
// Licensed under the Apache License, Version 2.0.

#pragma once

#include <rclcpp/node.hpp>
#include <string>

#include "mm_demo/task_base.hpp"
namespace mm_demo
{
class DrawSquareTask : public TaskBase
{
public:
  DrawSquareTask(const rclcpp::Node::SharedPtr & node, const std::string & name);

  bool init() override;
};
}  // namespace mm_demo

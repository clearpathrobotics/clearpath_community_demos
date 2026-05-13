// Copyright (c) 2026, Rockwell Automation Technologies, Inc., and community contributors.
// Licensed under the Apache License, Version 2.0.

#include <moveit_visual_tools/moveit_visual_tools.h>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp/utilities.hpp>

#include <cmath>
#include <string>
#include <thread>

#include "mm_demo/base_params.hpp"
#include "mm_demo/draw_square_task.hpp"
#include "mm_demo/write_letters_task.hpp"

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::NodeOptions node_options;
  node_options.automatically_declare_parameters_from_overrides(true);
  const auto node = rclcpp::Node::make_shared("mm_cartesian_demo", node_options);
  const auto logger = rclcpp::get_logger("mm_cartesian_demo");

  const auto visual_tools =
    std::make_shared<moveit_visual_tools::MoveItVisualTools>(node, "odom", "/rviz_visual_markers");

  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  auto spin_thread = std::thread([&executor]() { executor.spin(); });

  visual_tools->loadRemoteControl();
  visual_tools->prompt("Press 'Next' to start the demo");
  std::unique_ptr<mm_demo::TaskBase> task;

  const task_base::ParamListener param_listener(node);
  const auto params = param_listener.get_params();
  const auto mode = params.mode;
  if (mode == "write_letters")
  {
    task = std::make_unique<mm_demo::WriteLettersTask>(node, "write_letters_task");
  }
  else if (mode == "draw_square")
  {
    task = std::make_unique<mm_demo::DrawSquareTask>(node, "draw_square_task");
  }

  task->init();
  RCLCPP_INFO_STREAM(logger, "Planning starting...");

  task->plan();
  const auto solution = task->getPlannedSolution();
  if (solution.has_value())
  {
    visual_tools->prompt("Press 'Next' to visualize the planned solution");
    for (const auto & sub_trajectory : solution->sub_trajectory)
    {
      if (sub_trajectory.info.planner_id != "CartesianPath")
      {
        // Only visualize the CartesianPath stages since the letters are entirely written with Cartesian paths
        continue;
      }
      RCLCPP_WARN_STREAM(
        logger,
        "sub trajectory " << sub_trajectory.info.id << " with " << sub_trajectory.info.stage_id);
      visual_tools->publishTrajectoryLine(sub_trajectory.trajectory, task->getJointModelGroup());
    }
    visual_tools->trigger();
    RCLCPP_INFO_STREAM(logger, "Planning complete, executing...");
    task->execute();
  }

  spin_thread.join();
  rclcpp::shutdown();
  return 0;
}

// Copyright (c) 2026, Rockwell Automation Technologies, Inc., and community contributors.
// Licensed under the Apache License, Version 2.0.

#include <cmath>
#include <geometry_msgs/msg/pose.hpp>
#include <moveit/move_group_interface/move_group_interface.hpp>
#include <moveit/planning_scene_interface/planning_scene_interface.hpp>
#include <moveit_msgs/msg/collision_object.hpp>
#include <rclcpp/rclcpp.hpp>
#include <rviz_visual_tools/rviz_visual_tools.hpp>
#include <thread>

int main(int argc, char ** argv)
{
  using MoveGroupInterface = moveit::planning_interface::MoveGroupInterface;

  rclcpp::init(argc, argv);
  const auto node = rclcpp::Node::make_shared("mm_obstacle_avoidance_node");
  const auto logger = rclcpp::get_logger("mm_obstacle_avoidance");

  const auto visual_tools =
    std::make_shared<rviz_visual_tools::RvizVisualTools>("base_link", "/rviz_visual_markers", node);

  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  auto spin_thread = std::thread([&executor]() { executor.spin(); });

  visual_tools->loadRemoteControl();
  const std::string planning_group{"arm_base"};

  // Create the MoveGroupInterface
  MoveGroupInterface move_group_interface(node, planning_group);

  // Create the PlanningSceneInterface
  moveit::planning_interface::PlanningSceneInterface planning_scene_interface;

  // Create an obstacle
  moveit_msgs::msg::CollisionObject object;
  object.header.frame_id = move_group_interface.getPlanningFrame();
  object.id = "cube";
  object.primitives.resize(1);
  object.primitives[0].type = shape_msgs::msg::SolidPrimitive::BOX;
  object.primitives[0].dimensions = {0.3, 0.3, 1.0};
  object.primitive_poses.resize(1);
  object.pose.position.x = 1.5;
  object.pose.position.y = -0.0;
  object.pose.position.z = 1.0;

  planning_scene_interface.applyCollisionObject(object);

  // Create a goal pose
  geometry_msgs::msg::Pose goal_pose;
  goal_pose.position.x = 3.0;
  goal_pose.position.y = 0.0;
  goal_pose.position.z = 1.0;

  // Visualize the goal pose
  visual_tools->publishAxis(goal_pose);
  visual_tools->trigger();

  // Wait for user input to continue
  visual_tools->prompt("Press 'Next' to plan motion");

  // Set the goal to the goal pose and plan
  move_group_interface.setPoseTarget(goal_pose, "arm_tool0");
  move_group_interface.setPlanningTime(5);
  move_group_interface.setGoalPositionTolerance(0.05);

  MoveGroupInterface::Plan plan;
  bool success{false};
  for (std::uint16_t planning_attempts = 0; planning_attempts < 10 && !success; ++planning_attempts)
  {
    success = static_cast<bool>(move_group_interface.plan(plan));
  }

  // Execute the plan
  if (success)
  {
    move_group_interface.execute(plan);
  }

  else
  {
    RCLCPP_ERROR(logger, "Planning failed!");
  }

  rclcpp::shutdown();
  spin_thread.join();
  return 0;
}

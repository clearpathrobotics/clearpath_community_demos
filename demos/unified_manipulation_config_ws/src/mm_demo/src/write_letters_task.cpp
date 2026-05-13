// Copyright (c) 2026, Rockwell Automation Technologies, Inc., and community contributors.
// Licensed under the Apache License, Version 2.0.

#include "mm_demo/write_letters_task.hpp"

#include <moveit/task_constructor/container.h>
#include <moveit/task_constructor/solvers.h>
#include <moveit/task_constructor/stages.h>
#include <moveit/task_constructor/stages/move_relative.h>
#include <moveit/task_constructor/stages/move_to.h>
#include <moveit_msgs/msg/collision_object.hpp>
#include <rclcpp/logging.hpp>

#include "geometry_msgs/msg/vector3_stamped.hpp"
#include "mm_demo/write_letters_params.hpp"

#include <cmath>
#include <string>
#include <unordered_map>
#include <vector>

namespace mm_demo
{
namespace
{
const auto & logger = rclcpp::get_logger("write_letters_task");
}  // namespace

namespace mtc = moveit::task_constructor;
WriteLettersTask::WriteLettersTask(const rclcpp::Node::SharedPtr & node, const std::string & name)
: TaskBase(node, name)
{
}

bool WriteLettersTask::init()
{
  task_.stages()->setName(task_name_);
  task_.loadRobotModel(node_);

  const write_letters::ParamListener param_listener(node_);
  const auto params = param_listener.get_params();
  const auto fraction = params.fraction;
  const auto letters = params.letters;
  const auto motion_names = params.motion_names;
  const auto sampling_planning_attempts = static_cast<uint>(params.sampling_planning_attempts);
  const auto sampling_planning_timeout = params.sampling_planning_timeout;

  // Map to store the relative motion that make up each stage
  std::unordered_map<std::string, std::vector<double>> motions;

  // Map for starting points of each letter
  std::unordered_map<std::string, std::vector<double>> start_points;

  // Map for ordered list of stages for each letter
  std::unordered_map<std::string, std::vector<std::string>> letter_motions;

  for (const auto & letter : letters)
  {
    // Retrieve the stage names for this letter
    letter_motions[letter] = params.letter_motions.letters_map.at(letter).value;
    RCLCPP_INFO_STREAM(
      logger,
      "Generating stages, letter " << letter << " has stages: " << letter_motions[letter].size());
    const std::string param_name_base = "write_letters.points." + letter + ".";

    // Retrieve the start stage
    start_points[letter] = params.start_points.letters_map.at(letter).value;
  }
  for (const auto & motion_name : motion_names)
  {
    // Retrieve the motion for this stage
    motions[motion_name] = params.motions.motion_names_map.at(motion_name).value;
  }

  const auto sampling_planner = std::make_shared<mtc::solvers::PipelinePlanner>(node_);
  sampling_planner->setProperty("num_planning_attempts", sampling_planning_attempts);
  sampling_planner->setTimeout(sampling_planning_timeout);
  const auto cartesian_planner = std::make_shared<mtc::solvers::CartesianPath>();
  cartesian_planner->setMaxVelocityScalingFactor(1.0);
  cartesian_planner->setMaxAccelerationScalingFactor(1.0);
  cartesian_planner->setStepSize(.03);
  cartesian_planner->setMinFraction(fraction);

  task_.setProperty("group", group_);

  {
    auto current_state = std::make_unique<mtc::stages::CurrentState>("current state");
    task_.add(std::move(current_state));
  }

  for (const auto & letter : letters)
  {
    {
      auto stage = std::make_unique<mtc::stages::MoveTo>("start " + letter, sampling_planner);
      stage->setGroup(group_);
      geometry_msgs::msg::PoseStamped start_pose;
      start_pose.header.frame_id = "odom";
      start_pose.pose.position.x = start_points[letter][0];
      start_pose.pose.position.y = start_points[letter][1];
      start_pose.pose.position.z = start_points[letter][2];
      // Hardcoded orientation for now, but could be parameterized if needed
      start_pose.pose.orientation.x = 0.0;
      start_pose.pose.orientation.y = 0.0;
      start_pose.pose.orientation.z = M_PI_2;
      start_pose.pose.orientation.w = M_PI_2;
      stage->setGoal(start_pose);
      task_.add(std::move(stage));
    }
    {
      auto container = std::make_unique<mtc::SerialContainer>("draw " + letter);
      task_.properties().exposeTo(container->properties(), {"group"});
      container->properties().configureInitFrom(mtc::Stage::PARENT, {"group"});

      for (const auto & motion_name : letter_motions[letter])
      {
        auto stage = std::make_unique<mtc::stages::MoveRelative>(motion_name, cartesian_planner);
        stage->setGroup(group_);
        geometry_msgs::msg::Vector3Stamped direction;
        direction.header.frame_id = "odom";
        direction.vector.x = motions.at(motion_name)[0];
        direction.vector.y = motions.at(motion_name)[1];
        direction.vector.z = motions.at(motion_name)[2];
        stage->setDirection(direction);
        container->add(std::move(stage));
      }

      task_.add(std::move(container));

      {
        auto stage = std::make_unique<mtc::stages::MoveRelative>("return", sampling_planner);
        stage->setGroup("base");
        geometry_msgs::msg::Vector3Stamped vec;
        vec.header.frame_id = "odom";
        vec.vector.x = -0.5;
        stage->setIKFrame("base_link");
        stage->setDirection(vec);
        task_.add(std::move(stage));
      }
      {
        auto stage = std::make_unique<mtc::stages::MoveTo>("return", sampling_planner);
        stage->setGroup(group_);
        stage->setGoal("zero");
        task_.add(std::move(stage));
      }
    }
  }
  task_.init();

  return true;
}

}  // namespace mm_demo

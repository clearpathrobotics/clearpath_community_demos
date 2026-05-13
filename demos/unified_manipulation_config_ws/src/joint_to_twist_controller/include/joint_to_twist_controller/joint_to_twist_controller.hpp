// Copyright (c) 2026, Rockwell Automation Technologies, Inc., and community contributors.
// Licensed under the Apache License, Version 2.0.

#pragma once

#include <memory>
#include <string>
#include <vector>

#include <control_msgs/action/follow_joint_trajectory.hpp>
#include <control_msgs/msg/joint_trajectory_controller_state.hpp>
#include <controller_interface/chainable_controller_interface.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <realtime_tools/realtime_publisher.hpp>
#include <realtime_tools/realtime_thread_safe_box.hpp>

#include "control_msgs/msg/joint_trajectory_controller_state.hpp"

namespace joint_to_twist_controller
{
class JointToTwistController : public controller_interface::ChainableControllerInterface
{
public:
  JointToTwistController() = default;

  controller_interface::InterfaceConfiguration command_interface_configuration() const override;

  controller_interface::InterfaceConfiguration state_interface_configuration() const override;

  controller_interface::CallbackReturn on_init() override;

  controller_interface::CallbackReturn on_activate(
    const rclcpp_lifecycle::State & previous_state) override;

  controller_interface::CallbackReturn on_deactivate(
    const rclcpp_lifecycle::State & previous_state) override;

  // Should be unused, as this controller should always be in chained mode
  controller_interface::return_type update_reference_from_subscribers(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

  controller_interface::return_type update_and_write_commands(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

protected:
  std::vector<std::string> joints_;
  std::vector<std::string> command_joints_;

  // Integrated orientation of robot
  double theta_{0};

  using ControllerReferenceMsg = geometry_msgs::msg::TwistStamped;
  using ControllerStateMsg = control_msgs::msg::JointTrajectoryControllerState;
  using StatePublisher = realtime_tools::RealtimePublisher<ControllerStateMsg>;
  using StatePublisherPtr = std::unique_ptr<StatePublisher>;

  rclcpp::Subscription<ControllerReferenceMsg>::SharedPtr reference_subscriber_;
  realtime_tools::RealtimeThreadSafeBox<ControllerReferenceMsg> input_ref_;
  ControllerReferenceMsg reference_msg_;

  rclcpp::Publisher<ControllerStateMsg>::SharedPtr state_publisher_;
  StatePublisherPtr state_publisher_ptr_;
  ControllerStateMsg state_msg_;

  std::vector<hardware_interface::CommandInterface> on_export_reference_interfaces() override;

  bool on_set_chained_mode(bool chained_mode) override;
};
}  // namespace joint_to_twist_controller

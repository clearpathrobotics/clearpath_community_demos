// Copyright (c) 2026, Rockwell Automation Technologies, Inc., and community contributors.
// Licensed under the Apache License, Version 2.0.

// TODO: Investigate adding this option to mecanum_drive_controller

#include "joint_to_twist_controller/joint_to_twist_controller.hpp"
#include <cmath>
#include <controller_interface/helpers.hpp>
#include <hardware_interface/handle.hpp>
#include <hardware_interface/hardware_info.hpp>
#include <hardware_interface/types/hardware_interface_type_values.hpp>
#include <lifecycle_msgs/msg/state.hpp>
#include <rclcpp/logging.hpp>
#include <tf2/transform_datatypes.hpp>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <vector>

namespace joint_to_twist_controller
{

controller_interface::InterfaceConfiguration
JointToTwistController::command_interface_configuration() const
{
  controller_interface::InterfaceConfiguration conf;
  conf.names = command_joints_;
  conf.type = controller_interface::interface_configuration_type::INDIVIDUAL;
  return conf;
}

controller_interface::InterfaceConfiguration JointToTwistController::state_interface_configuration()
  const
{
  controller_interface::InterfaceConfiguration conf;
  conf.type = controller_interface::interface_configuration_type::NONE;
  return conf;
}

std::vector<hardware_interface::CommandInterface>
JointToTwistController::on_export_reference_interfaces()
{
  reference_interfaces_.resize(3, std::numeric_limits<double>::quiet_NaN());
  std::vector<hardware_interface::CommandInterface> reference_interfaces;

  std::vector<std::string> reference_interface_names = {"/linear/x", "/linear/y", "/angular/z"};

  for (size_t i = 0; i < reference_interface_names.size(); ++i)
  {
    reference_interfaces.push_back(hardware_interface::CommandInterface(
      get_node()->get_name() + reference_interface_names.at(i),
      hardware_interface::HW_IF_VELOCITY, &reference_interfaces_.at(i)));
  }
  return reference_interfaces;
}

controller_interface::return_type JointToTwistController::update_reference_from_subscribers(
  const rclcpp::Time & /* time */, const rclcpp::Duration & /* period */)
{
  auto current_ref_op = input_ref_.try_get();
  if (current_ref_op.has_value())
  {
    reference_msg_ = current_ref_op.value();
  }

  if (
    !std::isnan(reference_msg_.twist.linear.x) && !std::isnan(reference_msg_.twist.linear.y) &&
    !std::isnan(reference_msg_.twist.angular.z))
  {
    reference_interfaces_.at(0) = reference_msg_.twist.linear.x;
    reference_interfaces_.at(1) = reference_msg_.twist.linear.y;
    reference_interfaces_.at(2) = reference_msg_.twist.angular.z;
  }
  return controller_interface::return_type::OK;
}

controller_interface::return_type JointToTwistController::update_and_write_commands(
  const rclcpp::Time & time, const rclcpp::Duration & period)
{
  const auto & vx = reference_interfaces_.at(0);
  const auto & vy = reference_interfaces_.at(1);
  const auto & vtheta = reference_interfaces_.at(2);

  // Integrate theta
  theta_ += std::fmod(vtheta * period.seconds(), 2.0 * M_PI);

  // Convert twist from world frame to base frame
  tf2::Quaternion orientation_wb;
  orientation_wb.setRPY(0.0, 0.0, theta_);
  tf2::Vector3 velocity_base =
    tf2::Matrix3x3((orientation_wb.inverse())) * tf2::Vector3(vx, vy, 0.0);

  const bool success = command_interfaces_.at(0).set_value(velocity_base.x()) &&
                       command_interfaces_.at(1).set_value(velocity_base.y()) &&
                       command_interfaces_.at(2).set_value(vtheta);
  RCLCPP_ERROR_EXPRESSION(
    get_node()->get_logger(), !success, "Setting values to command interfaces has failed! ");

  state_msg_.header.stamp = time;
  state_msg_.reference.velocities.at(0) = vx;
  state_msg_.reference.velocities.at(1) = vy;
  state_msg_.reference.velocities.at(2) = vtheta;
  state_msg_.output.velocities.at(0) = velocity_base.x();
  state_msg_.output.velocities.at(1) = velocity_base.y();
  state_msg_.output.velocities.at(2) = vtheta;

  if (state_publisher_ptr_)
  {
    state_publisher_ptr_->try_publish(state_msg_);
  }

  return controller_interface::return_type::OK;
}

controller_interface::CallbackReturn JointToTwistController::on_init()
{
  auto reference_sub_qos = rclcpp::QoS(1).best_effort();

  reference_subscriber_ = get_node()->create_subscription<ControllerReferenceMsg>(
    "~/reference", reference_sub_qos,
    [this](ControllerReferenceMsg::SharedPtr msg) { input_ref_.set(*msg); });
  state_publisher_ = get_node()->create_publisher<ControllerStateMsg>(
    "~/controller_state", rclcpp::SystemDefaultsQoS());
  state_publisher_ptr_ = std::make_unique<StatePublisher>(state_publisher_);

  const std::vector<std::string> default_command_joints{};
  get_node()->declare_parameter<std::vector<std::string>>("command_joints", default_command_joints);
  get_node()->get_parameter("command_joints", command_joints_);

  // Not going to support drones here
  if (command_joints_.size() != 3)
  {
    RCLCPP_ERROR(
      get_node()->get_logger(),
      "joint_to_twist_controller requires exactly three command joints but got %zu.",
      command_joints_.size());
    return controller_interface::CallbackReturn::ERROR;
  }
  // TODO: what if the robot doesn't start at 0 orientation? Can we pass in position interfaces instead of integrating?
  theta_ = 0.0;

  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::CallbackReturn JointToTwistController::on_activate(
  const rclcpp_lifecycle::State & /* previous_state */)
{
  state_msg_.output.velocities.resize(3);
  state_msg_.reference.velocities.resize(3);
  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::CallbackReturn JointToTwistController::on_deactivate(
  const rclcpp_lifecycle::State & /* previous_state */)
{
  return controller_interface::CallbackReturn::SUCCESS;
}

bool JointToTwistController::on_set_chained_mode(bool /* chained_mode */) { return true; }

}  // namespace joint_to_twist_controller

#include "pluginlib/class_list_macros.hpp"

PLUGINLIB_EXPORT_CLASS(
  joint_to_twist_controller::JointToTwistController,
  controller_interface::ChainableControllerInterface)

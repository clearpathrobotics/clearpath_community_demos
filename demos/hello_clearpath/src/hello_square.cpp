// Copyright (c) 2026, Clearpath Robotics, by Rockwell Automation, and
// community contributors.
// Licensed under the Apache License, Version 2.0.

#include <cmath>
#include <memory>

#include <geometry_msgs/msg/twist_stamped.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <rclcpp/rclcpp.hpp>

namespace
{
constexpr double kSideLengthM = 1.0;
constexpr double kTurnAngleRad = M_PI / 2.0;
constexpr double kLinearSpeed = 0.2;   // m/s
constexpr double kAngularSpeed = 0.5;  // rad/s
constexpr double kPositionToleranceM = 0.02;
constexpr double kHeadingToleranceRad = 2.0 * M_PI / 180.0;
constexpr auto kTickPeriod = std::chrono::milliseconds(50);

double yaw_from_quaternion(const geometry_msgs::msg::Quaternion & q)
{
  const double siny_cosp = 2.0 * (q.w * q.z + q.x * q.y);
  const double cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z);
  return std::atan2(siny_cosp, cosy_cosp);
}

double angle_diff(double a, double b) { return std::atan2(std::sin(a - b), std::cos(a - b)); }
}  // namespace

class HelloSquare : public rclcpp::Node
{
public:
  HelloSquare() : rclcpp::Node("hello_square")
  {
    cmd_pub_ = create_publisher<geometry_msgs::msg::TwistStamped>("cmd_vel", 10);
    odom_sub_ = create_subscription<nav_msgs::msg::Odometry>(
      "platform/odom", 10, [this](nav_msgs::msg::Odometry::ConstSharedPtr msg) { on_odom(*msg); });
    timer_ = create_wall_timer(kTickPeriod, [this] { tick(); });
    RCLCPP_INFO(get_logger(), "Hello, Clearpath! Driving a 1m x 1m square.");
  }

private:
  enum class Phase
  {
    kForward,
    kTurn
  };

  void on_odom(const nav_msgs::msg::Odometry & msg)
  {
    x_ = msg.pose.pose.position.x;
    y_ = msg.pose.pose.position.y;
    yaw_ = yaw_from_quaternion(msg.pose.pose.orientation);
    if (!have_odom_)
    {
      start_x_ = x_;
      start_y_ = y_;
      start_yaw_ = yaw_;
      have_odom_ = true;
    }
  }

  void publish_cmd(double linear, double angular)
  {
    geometry_msgs::msg::TwistStamped msg;
    msg.header.stamp = now();
    msg.twist.linear.x = linear;
    msg.twist.angular.z = angular;
    cmd_pub_->publish(msg);
  }

  double distance_traveled() const { return std::hypot(x_ - start_x_, y_ - start_y_); }

  double heading_change() const { return std::abs(angle_diff(yaw_, start_yaw_)); }

  void tick()
  {
    if (!have_odom_)
    {
      return;
    }

    if (phase_ == Phase::kForward)
    {
      if (distance_traveled() + kPositionToleranceM < kSideLengthM)
      {
        publish_cmd(kLinearSpeed, 0.0);
      }
      else
      {
        publish_cmd(0.0, 0.0);
        RCLCPP_INFO(get_logger(), "Side %d complete.", side_ + 1);
        phase_ = Phase::kTurn;
        start_yaw_ = yaw_;
      }
    }
    else
    {
      if (heading_change() + kHeadingToleranceRad < kTurnAngleRad)
      {
        publish_cmd(0.0, kAngularSpeed);
      }
      else
      {
        publish_cmd(0.0, 0.0);
        ++side_;
        if (side_ >= 4)
        {
          RCLCPP_INFO(get_logger(), "Square complete.");
          rclcpp::shutdown();
          return;
        }
        phase_ = Phase::kForward;
        start_x_ = x_;
        start_y_ = y_;
      }
    }
  }

  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr cmd_pub_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
  rclcpp::TimerBase::SharedPtr timer_;
  Phase phase_{Phase::kForward};
  int side_{0};
  bool have_odom_{false};
  double x_{0.0};
  double y_{0.0};
  double yaw_{0.0};
  double start_x_{0.0};
  double start_y_{0.0};
  double start_yaw_{0.0};
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<HelloSquare>());
  rclcpp::shutdown();
  return 0;
}

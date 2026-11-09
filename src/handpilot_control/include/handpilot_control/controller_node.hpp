#pragma once

#include <chrono>
#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <std_srvs/srv/trigger.hpp>
#include <handpilot_interfaces/msg/teleop_command.hpp>
#include <handpilot_interfaces/msg/controller_status.hpp>
#include <handpilot_interfaces/srv/set_engaged.hpp>
#include "handpilot_core/controller.hpp"

namespace handpilot_control {
class ControllerNode : public rclcpp::Node {
public:
  explicit ControllerNode(const rclcpp::NodeOptions & options = rclcpp::NodeOptions());

private:
  using Clock = std::chrono::steady_clock;
  using Teleop = handpilot_interfaces::msg::TeleopCommand;
  using Status = handpilot_interfaces::msg::ControllerStatus;
  using Engage = handpilot_interfaces::srv::SetEngaged;
  double steady_seconds() const;
  void on_command(const Teleop::SharedPtr message);
  void tick();
  void publish(double now, const handpilot_core::Joints & velocities);
  Clock::time_point epoch_{Clock::now()};
  Clock::time_point previous_tick_{epoch_};
  std::unique_ptr<handpilot_core::Controller> controller_;
  rclcpp::Subscription<Teleop>::SharedPtr command_subscription_;
  rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr joint_publisher_;
  rclcpp::Publisher<Status>::SharedPtr status_publisher_;
  rclcpp::Service<Engage>::SharedPtr engage_service_;
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr reset_service_;
  rclcpp::TimerBase::SharedPtr timer_;
};
}

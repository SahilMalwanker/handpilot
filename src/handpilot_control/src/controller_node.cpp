#include "handpilot_control/controller_node.hpp"
#include <cmath>
#include <functional>
#include <stdexcept>
#include <rcl_interfaces/msg/parameter_descriptor.hpp>

namespace handpilot_control {
ControllerNode::ControllerNode(const rclcpp::NodeOptions & options)
: Node("handpilot_controller", options)
{
  rcl_interfaces::msg::ParameterDescriptor descriptor;
  descriptor.read_only = true;
  const auto parameter = [this, &descriptor](const std::string & name, double value) {
      return declare_parameter<double>(name, value, descriptor);
    };
  handpilot_core::Config config;
  config.link1 = parameter("link1_length", config.link1);
  config.link2 = parameter("link2_length", config.link2);
  config.lower = {parameter("shoulder_min", config.lower[0]), parameter("elbow_min", config.lower[1])};
  config.upper = {parameter("shoulder_max", config.upper[0]), parameter("elbow_max", config.upper[1])};
  config.max_speed = {parameter("shoulder_max_speed", config.max_speed[0]),
    parameter("elbow_max_speed", config.max_speed[1])};
  config.initial = {parameter("initial_shoulder", config.initial[0]),
    parameter("initial_elbow", config.initial[1])};
  config.max_cartesian_speed = parameter("max_cartesian_speed", config.max_cartesian_speed);
  config.command_timeout = parameter("command_timeout", config.command_timeout);
  config.max_dt = parameter("max_dt", config.max_dt);
  const double rate = parameter("control_rate_hz", 50.0);
  if (!std::isfinite(rate) || rate < 1.0 || rate > 500.0 || 1.0 / rate > config.max_dt) {
    throw std::invalid_argument("control_rate_hz must be 1..500 and its period <= max_dt");
  }
  controller_ = std::make_unique<handpilot_core::Controller>(config);
  command_subscription_ = create_subscription<Teleop>("teleop/command",
    rclcpp::QoS(rclcpp::KeepLast(1)).best_effort().durability_volatile(),
    std::bind(&ControllerNode::on_command, this, std::placeholders::_1));
  joint_publisher_ = create_publisher<sensor_msgs::msg::JointState>("joint_states", 10);
  status_publisher_ = create_publisher<Status>("controller/status", 10);
  engage_service_ = create_service<Engage>("controller/set_engaged",
    [this](const std::shared_ptr<Engage::Request> request,
    std::shared_ptr<Engage::Response> response) {
      const auto result = controller_->set_engaged(request->engaged, steady_seconds());
      response->success = result.success;
      response->message = result.message;
    });
  reset_service_ = create_service<std_srvs::srv::Trigger>("controller/reset",
    [this](const std::shared_ptr<std_srvs::srv::Trigger::Request>,
    std::shared_ptr<std_srvs::srv::Trigger::Response> response) {
      const auto result = controller_->reset();
      response->success = result.success;
      response->message = result.message;
    });
  previous_tick_ = Clock::now();
  timer_ = create_wall_timer(
    std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::duration<double>(1.0 / rate)),
    std::bind(&ControllerNode::tick, this));
  RCLCPP_INFO(get_logger(), "Kinematic simulation ready, DISENGAGED; no hardware feedback");
}

double ControllerNode::steady_seconds() const
{
  return std::chrono::duration<double>(Clock::now() - epoch_).count();
}

void ControllerNode::on_command(const Teleop::SharedPtr message)
{
  if (message->header.frame_id != "base_link") {
    controller_->fault("command frame must be base_link");
    return;
  }
  controller_->receive({message->source_id, message->sequence,
    {message->velocity_x, message->velocity_y}, message->active}, steady_seconds());
}

void ControllerNode::tick()
{
  const auto current = Clock::now();
  const double elapsed = std::chrono::duration<double>(current - previous_tick_).count();
  const double now = std::chrono::duration<double>(current - epoch_).count();
  previous_tick_ = current;
  const auto before = controller_->joints();
  controller_->step(now, elapsed);
  handpilot_core::Joints velocities{};
  if (elapsed > 0.0 && std::isfinite(elapsed)) {
    for (std::size_t joint = 0; joint < 2; ++joint) {
      velocities[joint] = (controller_->joints()[joint] - before[joint]) / elapsed;
    }
  }
  publish(now, velocities);
}

void ControllerNode::publish(double now, const handpilot_core::Joints & velocities)
{
  sensor_msgs::msg::JointState joints;
  joints.header.stamp = get_clock()->now();
  joints.header.frame_id = "base_link";
  joints.name = {"shoulder_joint", "elbow_joint"};
  const auto & positions = controller_->joints();
  joints.position.assign(positions.begin(), positions.end());
  joints.velocity.assign(velocities.begin(), velocities.end());
  joint_publisher_->publish(joints);
  Status status;
  status.header = joints.header;
  status.state = static_cast<std::uint8_t>(controller_->state());
  status.reason = controller_->reason();
  const auto requested = controller_->requested();
  const auto achieved = controller_->achieved();
  status.requested_position = {requested.x, requested.y};
  status.achieved_position = {achieved.x, achieved.y};
  status.joints = positions;
  status.limited = controller_->limited();
  status.rejected = controller_->rejected();
  const auto age = controller_->command_age(now);
  status.command_age_valid = age.has_value();
  status.command_age = age.value_or(0.0);
  status_publisher_->publish(status);
  controller_->clear_events();
}
}

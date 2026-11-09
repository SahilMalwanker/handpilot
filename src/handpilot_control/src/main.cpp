#include "handpilot_control/controller_node.hpp"
#include <exception>
#include <iostream>

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  int result = 0;
  try {
    auto node = std::make_shared<handpilot_control::ControllerNode>();
    rclcpp::executors::SingleThreadedExecutor executor;
    executor.add_node(node);
    executor.spin();
    executor.remove_node(node);
  } catch (const std::exception & error) {
    std::cerr << "HandPilot startup/runtime error: " << error.what() << '\n';
    result = 1;
  }
  if (rclcpp::ok()) {rclcpp::shutdown();}
  return result;
}

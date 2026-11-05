#pragma once

#include <array>
#include <cstdint>
#include <string>

namespace handpilot_core {
constexpr double kPi = 3.14159265358979323846;
using Joints = std::array<double, 2>;
using Jacobian = std::array<std::array<double, 2>, 2>;

struct Vec2 {
  double x{0.0};
  double y{0.0};
};

struct Config {
  double link1{0.30};
  double link2{0.25};
  Joints lower{-2.8, -2.8};
  Joints upper{2.8, 2.8};
  Joints max_speed{0.8, 0.8};
  Joints initial{0.4, 1.0};
  double max_cartesian_speed{0.12};
  double command_timeout{0.25};
  double max_dt{0.10};
};

enum class State : std::uint8_t { DISENGAGED = 0, ENGAGED = 1, HOLD = 2, FAULT = 3 };

struct Command {
  std::string source_id;
  std::uint64_t sequence{0};
  Vec2 velocity;
  bool active{false};
};

struct ActionResult {
  bool success{false};
  std::string message;
};
}  // namespace handpilot_core

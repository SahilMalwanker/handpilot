#pragma once

#include <vector>
#include "handpilot_core/types.hpp"

namespace handpilot_core {
struct IKResult {
  bool success{false};
  Joints joints{};
  std::vector<Joints> solutions;
  std::string reason;
};
IKResult inverse_kinematics(const Config & config, Vec2 target, const Joints & current);
}  // namespace handpilot_core

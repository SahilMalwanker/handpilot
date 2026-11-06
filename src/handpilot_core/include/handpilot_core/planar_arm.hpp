#pragma once

#include "handpilot_core/types.hpp"

namespace handpilot_core {
Vec2 forward_kinematics(const Config & config, const Joints & joints);
Jacobian jacobian(const Config & config, const Joints & joints);
}  // namespace handpilot_core

#pragma once

#include "handpilot_core/types.hpp"

namespace handpilot_core {
bool finite(Vec2 value);
bool finite(const Joints & value);
bool within_limits(const Config & config, const Joints & joints);
bool valid_config(const Config & config);
Vec2 bound_velocity(Vec2 velocity, double maximum, bool & limited);
Joints rate_limit(const Config & config, const Joints & current,
  const Joints & desired, double dt, bool & limited);
}  // namespace handpilot_core

#include "handpilot_core/constraints.hpp"
#include <algorithm>
#include <cmath>

namespace handpilot_core {
bool finite(Vec2 value) {return std::isfinite(value.x) && std::isfinite(value.y);}
bool finite(const Joints & value)
{
  return std::isfinite(value[0]) && std::isfinite(value[1]);
}

bool within_limits(const Config & config, const Joints & joints)
{
  return finite(joints) && joints[0] >= config.lower[0] && joints[0] <= config.upper[0] &&
         joints[1] >= config.lower[1] && joints[1] <= config.upper[1];
}

bool valid_config(const Config & config)
{
  if (!std::isfinite(config.link1) || !std::isfinite(config.link2) ||
    config.link1 < 1e-4 || config.link2 < 1e-4 || config.link1 > 10.0 || config.link2 > 10.0 ||
    !finite(config.lower) || !finite(config.upper) || !finite(config.max_speed) ||
    !within_limits(config, config.initial) ||
    !std::isfinite(config.max_cartesian_speed) || config.max_cartesian_speed <= 0.0 ||
    config.max_cartesian_speed > 10.0 || !std::isfinite(config.command_timeout) ||
    config.command_timeout <= 0.0 || !std::isfinite(config.max_dt) ||
    config.max_dt <= 0.0 || config.max_dt > 1.0)
  {
    return false;
  }
  for (std::size_t joint = 0; joint < 2; ++joint) {
    if (config.lower[joint] >= config.upper[joint] || config.lower[joint] < -2.0 * kPi ||
      config.upper[joint] > 2.0 * kPi || config.max_speed[joint] <= 0.0 ||
      config.max_speed[joint] > 100.0)
    {
      return false;
    }
  }
  return true;
}

Vec2 bound_velocity(Vec2 velocity, double maximum, bool & limited)
{
  if (!finite(velocity) || !std::isfinite(maximum) || maximum <= 0.0) {
    limited = true;
    return {};
  }
  const double scale = std::max(std::abs(velocity.x), std::abs(velocity.y));
  if (scale == 0.0) {return velocity;}
  const Vec2 unit{velocity.x / scale, velocity.y / scale};
  const double norm = std::hypot(unit.x, unit.y);
  if (scale > maximum / norm) {
    limited = true;
    return {unit.x * (maximum / norm), unit.y * (maximum / norm)};
  }
  return velocity;
}

Joints rate_limit(const Config & config, const Joints & current,
  const Joints & desired, double dt, bool & limited)
{
  if (!valid_config(config) || !within_limits(config, current) ||
    !within_limits(config, desired) || !std::isfinite(dt) || dt <= 0.0 || dt > config.max_dt)
  {
    limited = true;
    return finite(current) ? current : Joints{};
  }
  Joints next = current;
  for (std::size_t joint = 0; joint < 2; ++joint) {
    const double maximum = config.max_speed[joint] * dt;
    const double delta = desired[joint] - current[joint];
    const double bounded = std::clamp(delta, -maximum, maximum);
    limited = limited || bounded != delta;
    next[joint] = std::clamp(current[joint] + bounded, config.lower[joint], config.upper[joint]);
  }
  return next;
}
}  // namespace handpilot_core

#include "handpilot_core/planar_arm.hpp"
#include <cmath>

namespace handpilot_core {
Vec2 forward_kinematics(const Config & config, const Joints & joints)
{
  const double combined = joints[0] + joints[1];
  return {config.link1 * std::cos(joints[0]) + config.link2 * std::cos(combined),
    config.link1 * std::sin(joints[0]) + config.link2 * std::sin(combined)};
}

Jacobian jacobian(const Config & config, const Joints & joints)
{
  const double combined = joints[0] + joints[1];
  const double distal_x = -config.link2 * std::sin(combined);
  const double distal_y = config.link2 * std::cos(combined);
  return {{{-config.link1 * std::sin(joints[0]) + distal_x, distal_x},
    {config.link1 * std::cos(joints[0]) + distal_y, distal_y}}};
}
}  // namespace handpilot_core

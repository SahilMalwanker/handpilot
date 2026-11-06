#include "handpilot_core/inverse_kinematics.hpp"
#include "handpilot_core/constraints.hpp"
#include <algorithm>
#include <cmath>
#include <limits>

namespace handpilot_core {
IKResult inverse_kinematics(const Config & config, Vec2 target, const Joints & current)
{
  IKResult result;
  if (!valid_config(config) || !finite(target) || !within_limits(config, current)) {
    result.reason = "invalid IK input";
    return result;
  }
  const double radius = std::hypot(target.x, target.y);
  double cosine = (radius * radius - config.link1 * config.link1 - config.link2 * config.link2) /
    (2.0 * config.link1 * config.link2);
  if (!std::isfinite(cosine) || cosine < -1.0 - 1e-10 || cosine > 1.0 + 1e-10) {
    result.reason = "outside radial workspace";
    return result;
  }
  cosine = std::clamp(cosine, -1.0, 1.0);
  double closest = std::numeric_limits<double>::infinity();
  for (const double sign : {1.0, -1.0}) {
    const double elbow = sign * std::acos(cosine);
    const bool folded_origin = radius < 1e-12 && std::abs(config.link1 - config.link2) < 1e-12;
    const double shoulder = folded_origin ? current[0] :
      std::atan2(target.y, target.x) -
      std::atan2(config.link2 * std::sin(elbow), config.link1 + config.link2 * std::cos(elbow));
    for (int shoulder_turn = -2; shoulder_turn <= 2; ++shoulder_turn) {
      for (int elbow_turn = -2; elbow_turn <= 2; ++elbow_turn) {
        const Joints candidate{shoulder + shoulder_turn * 2.0 * kPi,
          elbow + elbow_turn * 2.0 * kPi};
        if (!within_limits(config, candidate)) {continue;}
        const bool duplicate = std::any_of(result.solutions.begin(), result.solutions.end(),
          [&candidate](const Joints & existing) {
            return std::hypot(existing[0] - candidate[0], existing[1] - candidate[1]) < 1e-12;
          });
        if (duplicate) {continue;}
        result.solutions.push_back(candidate);
        const double distance = std::hypot(candidate[0] - current[0], candidate[1] - current[1]);
        if (distance < closest) {
          closest = distance;
          result.joints = candidate;
          result.success = true;
        }
      }
    }
  }
  result.reason = result.success ? "solution" : "joint limits exclude all IK branches";
  return result;
}
}  // namespace handpilot_core

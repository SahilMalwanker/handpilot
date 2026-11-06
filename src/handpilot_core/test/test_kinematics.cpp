#include <gtest/gtest.h>
#include <cmath>
#include <limits>
#include "handpilot_core/constraints.hpp"
#include "handpilot_core/inverse_kinematics.hpp"
#include "handpilot_core/planar_arm.hpp"

using namespace handpilot_core;

TEST(Kinematics, KnownForwardValues)
{
  const Config config;
  auto position = forward_kinematics(config, {0.0, 0.0});
  EXPECT_NEAR(position.x, 0.55, 1e-12);
  EXPECT_NEAR(position.y, 0.0, 1e-12);
  position = forward_kinematics(config, {kPi / 2.0, -kPi / 2.0});
  EXPECT_NEAR(position.x, 0.25, 1e-12);
  EXPECT_NEAR(position.y, 0.30, 1e-12);
}

TEST(Kinematics, RoundTripsAndBothBranches)
{
  const Config config;
  for (const double shoulder : {-1.0, 0.0, 1.0}) {
    for (const double elbow : {-1.4, -0.6, 0.6, 1.4}) {
      const Joints original{shoulder, elbow};
      const Vec2 target = forward_kinematics(config, original);
      const auto result = inverse_kinematics(config, target, original);
      ASSERT_TRUE(result.success) << result.reason;
      EXPECT_NEAR(result.joints[0], shoulder, 1e-10);
      EXPECT_NEAR(result.joints[1], elbow, 1e-10);
      const auto achieved = forward_kinematics(config, result.joints);
      EXPECT_NEAR(achieved.x, target.x, 1e-12);
      EXPECT_NEAR(achieved.y, target.y, 1e-12);
    }
  }
  const auto result = inverse_kinematics(config,
    forward_kinematics(config, config.initial), config.initial);
  ASSERT_EQ(result.solutions.size(), 2u);
  EXPECT_GT(result.solutions[0][1] * -result.solutions[1][1], 0.0);
  const auto other = inverse_kinematics(config,
    forward_kinematics(config, config.initial), result.solutions[1]);
  EXPECT_NEAR(other.joints[1], result.solutions[1][1], 1e-12);
}

TEST(Kinematics, WorkspaceAndJointRestrictions)
{
  Config config;
  EXPECT_FALSE(inverse_kinematics(config, {0.049, 0.0}, config.initial).success);
  EXPECT_FALSE(inverse_kinematics(config, {0.56, 0.0}, config.initial).success);
  EXPECT_FALSE(inverse_kinematics(config, {0.05, 0.0}, config.initial).success);
  config.lower = {-kPi, -kPi};
  config.upper = {kPi, kPi};
  EXPECT_TRUE(inverse_kinematics(config, {0.05, 0.0}, config.initial).success);
  EXPECT_TRUE(inverse_kinematics(config, {0.55, 0.0}, config.initial).success);
  config.lower = {0.2, 0.2};
  config.upper = {0.8, 1.5};
  EXPECT_FALSE(inverse_kinematics(config, {-0.3, -0.2}, config.initial).success);
}

TEST(Kinematics, EquivalentAnglesRespectHardBounds)
{
  Config config;
  config.lower = {3.0, 0.1};
  config.upper = {4.0, 2.8};
  config.initial = {3.4, 1.0};
  const auto result = inverse_kinematics(config,
    forward_kinematics(config, {3.5, 1.1}), config.initial);
  ASSERT_TRUE(result.success);
  EXPECT_NEAR(result.joints[0], 3.5, 1e-10);
  EXPECT_TRUE(within_limits(config, result.joints));
  config.lower = {-2.0 * kPi, -2.0 * kPi};
  config.upper = {2.0 * kPi, 2.0 * kPi};
  config.initial = {6.0, 0.4};
  const auto multiple = inverse_kinematics(config,
    forward_kinematics(config, {0.1, 0.5}), config.initial);
  ASSERT_TRUE(multiple.success);
  const double selected = std::hypot(multiple.joints[0] - 6.0, multiple.joints[1] - 0.4);
  for (const auto & candidate : multiple.solutions) {
    EXPECT_LE(selected, std::hypot(candidate[0] - 6.0, candidate[1] - 0.4) + 1e-12);
  }
}

TEST(Kinematics, CosineToleranceAndNonFiniteRejection)
{
  const Config config;
  const auto radius = [&config](double cosine) {
      return std::sqrt(config.link1 * config.link1 + config.link2 * config.link2 +
        2.0 * config.link1 * config.link2 * cosine);
    };
  EXPECT_TRUE(inverse_kinematics(config, {radius(1.0 + 5e-11), 0.0}, config.initial).success);
  EXPECT_FALSE(inverse_kinematics(config, {radius(1.0 + 2e-10), 0.0}, config.initial).success);
  for (const double invalid : {std::numeric_limits<double>::quiet_NaN(),
      std::numeric_limits<double>::infinity()})
  {
    const auto result = inverse_kinematics(config, {invalid, 0.0}, config.initial);
    EXPECT_FALSE(result.success);
    EXPECT_TRUE(finite(result.joints));
  }
}

TEST(Kinematics, JacobianMatchesCentralDifferences)
{
  const Config config;
  const Joints pose{0.7, -1.2};
  const auto analytic = jacobian(config, pose);
  constexpr double epsilon = 1e-6;
  for (std::size_t joint = 0; joint < 2; ++joint) {
    auto plus = pose;
    auto minus = pose;
    plus[joint] += epsilon;
    minus[joint] -= epsilon;
    const auto high = forward_kinematics(config, plus);
    const auto low = forward_kinematics(config, minus);
    EXPECT_NEAR(analytic[0][joint], (high.x - low.x) / (2.0 * epsilon), 1e-9);
    EXPECT_NEAR(analytic[1][joint], (high.y - low.y) / (2.0 * epsilon), 1e-9);
  }
}

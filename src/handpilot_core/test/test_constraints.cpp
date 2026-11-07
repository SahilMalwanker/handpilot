#include <gtest/gtest.h>
#include <cmath>
#include <limits>
#include <stdexcept>
#include "handpilot_core/constraints.hpp"
#include "handpilot_core/controller.hpp"

using namespace handpilot_core;

TEST(Constraints, CartesianMagnitudeIncludingHugeFiniteInput)
{
  bool limited = false;
  auto bounded = bound_velocity({3.0, 4.0}, 0.12, limited);
  EXPECT_TRUE(limited);
  EXPECT_NEAR(std::hypot(bounded.x, bounded.y), 0.12, 1e-12);
  EXPECT_NEAR(bounded.x / bounded.y, 0.75, 1e-12);
  bounded = bound_velocity({std::numeric_limits<double>::max(),
      std::numeric_limits<double>::max()}, 0.12, limited);
  EXPECT_TRUE(finite(bounded));
  EXPECT_LE(std::hypot(bounded.x, bounded.y), 0.12 + 1e-12);
}

TEST(Constraints, JointRateAndPositionBounds)
{
  const Config config;
  bool limited = false;
  const auto next = rate_limit(config, config.initial, {2.8, -2.8}, 0.02, limited);
  EXPECT_TRUE(limited);
  EXPECT_TRUE(within_limits(config, next));
  for (std::size_t joint = 0; joint < 2; ++joint) {
    EXPECT_LE(std::abs(next[joint] - config.initial[joint]), config.max_speed[joint] * 0.02 + 1e-12);
  }
}

TEST(Constraints, InvalidIntervalsAndInputsDoNotMove)
{
  const Config config;
  for (const double interval : {0.0, -0.02, 100.0,
      std::numeric_limits<double>::quiet_NaN(), std::numeric_limits<double>::infinity()})
  {
    bool limited = false;
    EXPECT_EQ(rate_limit(config, config.initial, {1.0, 1.0}, interval, limited), config.initial);
    EXPECT_TRUE(limited);
  }
  bool limited = false;
  EXPECT_EQ(rate_limit(config, config.initial, {10.0, 0.0}, 0.02, limited), config.initial);
  const auto bounded = bound_velocity({std::numeric_limits<double>::infinity(), 0.0}, 0.12, limited);
  EXPECT_DOUBLE_EQ(bounded.x, 0.0);
  EXPECT_DOUBLE_EQ(bounded.y, 0.0);
}

TEST(Constraints, InvalidConfigurationIsRejected)
{
  Config config;
  ASSERT_TRUE(valid_config(config));
  config.link1 = 0.0;
  EXPECT_FALSE(valid_config(config));
  EXPECT_THROW(Controller{config}, std::invalid_argument);
  config = Config{};
  config.initial[0] = 3.0;
  EXPECT_FALSE(valid_config(config));
  config = Config{};
  config.max_speed[1] = std::numeric_limits<double>::quiet_NaN();
  EXPECT_FALSE(valid_config(config));
}
